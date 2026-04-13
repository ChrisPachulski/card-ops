###############################################################################
# lib/rewards.py -- Rewards calculator + routing leak detector
#
# Calculates actual rewards earned per card per category, identifies routing
# leaks (spend earning below the best available rate in the portfolio).
###############################################################################
from pathlib import Path

import pandas as pd
import yaml

from lib.parse import load_all_transactions


###############################################################################
# Paths
###############################################################################

CARD_OPS_ROOT = Path(__file__).parent.parent
CONFIG_DIR = CARD_OPS_ROOT / "config"


###############################################################################
# Card Slug Mapping
#
# Profile YAML uses verbose names ("Wells Fargo" / "Active Cash") but the
# transaction parquets use compact slugs ("wf-active-cash").  This explicit
# map keeps the two worlds in sync without fragile string munging.
###############################################################################

_SLUG_OVERRIDES: dict[tuple[str, str], str] = {
    ("wells fargo", "active cash"): "wf-active-cash",
    ("american express", "blue cash preferred"): "amex-bcp",
    ("chase", "amazon prime visa signature"): "chase-amazon",
    ("chase", "freedom unlimited"): "chase-freedom",
}


###############################################################################
# Category -> Earn-Rate Key Mapping
#
# Categories come from normalize.py; rate keys come from profile YAML
# earn_rates dicts.  "everything" is the WF Active Cash catch-all key.
###############################################################################

_CATEGORY_RATE_KEY: dict[str, str] = {
    "Groceries": "groceries",
    "Dining": "dining",
    "Delivery": "dining",
    "Amazon": "amazon",
    "Gas": "gas",
    "Streaming": "streaming",
    "Software": "other",
    "Telecom": "other",
    "Shopping": "other",
    "Home": "other",
    "Healthcare": "other",
    "Travel": "other",
    "Entertainment": "other",
    "Alcohol": "other",
    "Childcare": "other",
    "Insurance": "other",
    "Utilities": "other",
    "Shipping": "other",
    "Other": "other",
}


###############################################################################
# Private Helpers
###############################################################################

def _card_slug(issuer: str, card_name: str) -> str:
    """Derive a compact slug for a card from its issuer + product name.

    Checks _SLUG_OVERRIDES first, then falls back to
    ``{issuer_lower}-{first_word_of_card_lower}``.
    """
    key = (issuer.lower(), card_name.lower())
    if key in _SLUG_OVERRIDES:
        return _SLUG_OVERRIDES[key]
    return f"{issuer.lower().replace(' ', '-')}-{card_name.lower().split()[0]}"


def _load_card_rates() -> dict[str, dict[str, float]]:
    """Load earn-rate dicts from all profile-*.yml files.

    Returns a dict keyed by card slug (e.g. ``"amex-bcp"``) whose values
    are the ``earn_rates`` dicts straight from the YAML.
    """
    rates: dict[str, dict[str, float]] = {}
    for profile_file in sorted(CONFIG_DIR.glob("profile-*.yml")):
        with open(profile_file) as f:
            profile = yaml.safe_load(f)
        for card in profile.get("cards", []):
            slug = _card_slug(card["issuer"], card["card"])
            rates[slug] = card.get("earn_rates", {})
    return rates


def _load_wallet_routing() -> dict[str, str]:
    """Load the wallet_routing section from household.yml."""
    household_path = CONFIG_DIR / "household.yml"
    with open(household_path) as f:
        household = yaml.safe_load(f)
    return household.get("wallet_routing", {})


def _rate_for_card_category(card_rates: dict[str, float], category: str) -> float:
    """Look up the earn rate a card gives for a spending category.

    Falls back through: category key -> ``"everything"`` -> ``"other"`` -> 0.01.
    """
    rate_key = _CATEGORY_RATE_KEY.get(category, "other")
    return float(
        card_rates.get(rate_key, card_rates.get("everything", card_rates.get("other", 0.01)))
    )


def _best_rate_for_category(
    category: str,
    all_card_rates: dict[str, dict[str, float]],
) -> tuple[str, float]:
    """Find the card with the highest earn rate for *category* across the
    entire portfolio (not just the routed card).

    Returns (best_card_slug, best_rate).
    """
    best_card = ""
    best_rate = 0.0
    for slug, rates in all_card_rates.items():
        rate = _rate_for_card_category(rates, category)
        if rate > best_rate:
            best_rate = rate
            best_card = slug
    return best_card, best_rate


###############################################################################
# Public API
###############################################################################

def calculate_rewards(months: int = 12) -> dict:
    """Calculate actual rewards earned and identify routing leaks.

    Parameters
    ----------
    months : int
        Number of trailing months to analyze.

    Returns
    -------
    dict
        Keys:
        - ``period_months``: actual distinct months in the window
        - ``total_current_rewards``: rewards at current routing
        - ``total_optimal_rewards``: rewards at best-possible routing
        - ``total_routing_leak``: optimal minus current
        - ``effective_rate``: current rewards / total spend (pct)
        - ``optimal_rate``: optimal rewards / total spend (pct)
        - ``leaks``: list of dicts, sorted by annual_leak descending
        - ``by_category``: list of per-(category, card) detail dicts
    """
    df = load_all_transactions()
    if df.empty:
        return {"error": "No transaction data. Run scan mode first."}

    all_card_rates = _load_card_rates()

    # Filter to trailing N months
    cutoff = df["date"].max() - pd.DateOffset(months=months)
    df = df[df["date"] >= cutoff].copy()

    n_months = df["date"].dt.to_period("M").nunique()
    if n_months == 0:
        return {"error": "No transactions in the requested window."}

    annualize = 12 / n_months

    # Accumulate per-(category, card) rows
    by_category: list[dict] = []
    leaks: list[dict] = []

    for (cat, card), group in df.groupby(["category", "card"]):
        period_spend = float(group["amount"].sum())
        annual_spend = round(period_spend * annualize, 0)

        # Current earn rate for this card on this category
        card_rates = all_card_rates.get(card, {})
        current_rate = _rate_for_card_category(card_rates, cat)
        current_reward = annual_spend * current_rate

        # Best available card in the full portfolio
        best_card, best_rate = _best_rate_for_category(cat, all_card_rates)
        optimal_reward = annual_spend * best_rate

        by_category.append({
            "category": cat,
            "card": card,
            "annual_spend": annual_spend,
            "earn_rate": current_rate,
            "annual_reward": round(current_reward, 2),
        })

        if best_rate > current_rate and annual_spend > 100:
            leaks.append({
                "category": cat,
                "current_card": card,
                "current_rate": current_rate,
                "best_card": best_card,
                "best_rate": best_rate,
                "annual_spend": annual_spend,
                "annual_leak": round(optimal_reward - current_reward, 2),
            })

    total_spend = sum(r["annual_spend"] for r in by_category) or 1.0
    total_current = sum(r["annual_reward"] for r in by_category)

    # Optimal total: sum best_rate * annual_spend across unique categories
    # (collapse across cards that share a category)
    category_spend: dict[str, float] = {}
    for row in by_category:
        category_spend[row["category"]] = (
            category_spend.get(row["category"], 0.0) + row["annual_spend"]
        )
    total_optimal = sum(
        spend * _best_rate_for_category(cat, all_card_rates)[1]
        for cat, spend in category_spend.items()
    )

    total_leak = round(total_optimal - total_current, 2)

    return {
        "period_months": n_months,
        "total_current_rewards": round(total_current, 2),
        "total_optimal_rewards": round(total_optimal, 2),
        "total_routing_leak": total_leak,
        "effective_rate": round(total_current / total_spend * 100, 2),
        "optimal_rate": round(total_optimal / total_spend * 100, 2),
        "leaks": sorted(leaks, key=lambda x: x["annual_leak"], reverse=True),
        "by_category": by_category,
    }
