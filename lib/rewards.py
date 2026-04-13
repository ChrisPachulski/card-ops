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
    "Whole Foods": "whole_foods",
    "Dining": "dining",
    "Delivery": "dining",
    "Amazon": "amazon",
    "Gas": "gas",
    "Streaming": "streaming",
    "Transit": "transit",
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


def _load_rate_overrides() -> dict[str, dict[str, float]]:
    """Load merchant-level rate overrides from known-cards.yml.

    Returns a dict keyed by card slug whose values are
    {merchant_name_lower: override_rate} dicts.

    These handle cases where a card's category rate doesn't apply to
    specific merchants (e.g., BCP gets 6% groceries but 1% at Costco
    because warehouse clubs use MCC 5300, not 5411).
    """
    from lib.card_lookup import _load_known_cards

    overrides: dict[str, dict[str, float]] = {}
    try:
        known = _load_known_cards()
        for slug, card in known.items():
            raw = card.get("rate_overrides") or {}
            if raw:
                overrides[slug] = {k.lower(): float(v) for k, v in raw.items()}
    except Exception:
        pass
    return overrides


# Module-level cache for overrides (loaded once per session)
_RATE_OVERRIDES: dict[str, dict[str, float]] | None = None


def _get_rate_overrides() -> dict[str, dict[str, float]]:
    """Return cached rate overrides, loading on first call."""
    global _RATE_OVERRIDES
    if _RATE_OVERRIDES is None:
        _RATE_OVERRIDES = _load_rate_overrides()
    return _RATE_OVERRIDES


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


def _rate_for_card_merchant(
    card_slug: str,
    card_rates: dict[str, float],
    category: str,
    merchant: str,
) -> float:
    """Look up the earn rate for a specific card + merchant combination.

    Checks merchant-level overrides first (e.g., BCP -> Costco = 1%),
    then falls back to the category rate.
    """
    overrides = _get_rate_overrides()
    card_overrides = overrides.get(card_slug, {})
    if card_overrides and merchant:
        merchant_lower = merchant.lower()
        for override_merchant, override_rate in card_overrides.items():
            if override_merchant in merchant_lower:
                return override_rate
    return _rate_for_card_category(card_rates, category)


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
# Grocery Cap Helpers
###############################################################################

def _find_grocery_cap(
    all_card_rates: dict[str, dict[str, float]],
) -> tuple[str | None, float, float | None, float]:
    """Find the card with a grocery cap and return its parameters.

    Returns (capped_slug, capped_rate, cap_amount, after_cap_rate).
    If no card has a cap, returns (None, 0.0, None, 0.0).
    """
    for slug, rates in all_card_rates.items():
        if "groceries_cap" in rates:
            return (
                slug,
                rates.get("groceries", 0.0),
                rates["groceries_cap"],
                rates.get("groceries_after_cap", 0.01),
            )
    return (None, 0.0, None, 0.0)


def _best_non_capped_grocery_rate(
    all_card_rates: dict[str, dict[str, float]],
    exclude_slug: str | None,
) -> tuple[str, float]:
    """Find the best grocery rate among cards that are NOT the capped card."""
    best_slug = ""
    best_rate = 0.0
    for slug, rates in all_card_rates.items():
        if slug == exclude_slug:
            continue
        rate = _rate_for_card_category(rates, "Groceries")
        if rate > best_rate:
            best_rate = rate
            best_slug = slug
    return best_slug, best_rate


def _optimal_grocery_rewards(
    total_grocery: float,
    all_card_rates: dict[str, dict[str, float]],
) -> float:
    """Compute the maximum possible grocery rewards given cap constraints."""
    capped_slug, capped_rate, cap_amount, after_cap_rate = _find_grocery_cap(
        all_card_rates
    )
    if capped_slug is None:
        _, best_rate = _best_rate_for_category("Groceries", all_card_rates)
        return total_grocery * best_rate

    alt_slug, alt_rate = _best_non_capped_grocery_rate(all_card_rates, capped_slug)
    overflow_rate = max(after_cap_rate, alt_rate)

    if total_grocery <= cap_amount:
        return total_grocery * capped_rate

    return cap_amount * capped_rate + (total_grocery - cap_amount) * overflow_rate


def _handle_grocery_rewards(
    df_grocery: pd.DataFrame,
    all_card_rates: dict[str, dict[str, float]],
    annualize: float,
    by_category: list[dict],
    leaks: list[dict],
) -> None:
    """Process grocery transactions with cap-aware rewards and leak detection.

    Mutates by_category and leaks in place.
    """
    if df_grocery.empty:
        return

    capped_slug, capped_rate, cap_amount, after_cap_rate = _find_grocery_cap(
        all_card_rates
    )
    alt_slug, alt_rate = _best_non_capped_grocery_rate(all_card_rates, capped_slug)

    # Compute annualized grocery spend per card
    grocery_by_card: dict[str, float] = {}
    for card, group in df_grocery.groupby("card"):
        period_spend = float(group["amount"].sum())
        grocery_by_card[card] = round(period_spend * annualize, 0)

    total_grocery = sum(grocery_by_card.values())

    # Record by_category entries with cap-aware actual rates
    for card, annual_spend in grocery_by_card.items():
        card_rates = all_card_rates.get(card, {})
        if card == capped_slug and cap_amount is not None:
            under_cap = min(annual_spend, cap_amount)
            over_cap = max(0.0, annual_spend - cap_amount)
            actual_reward = under_cap * capped_rate + over_cap * after_cap_rate
            effective_rate = actual_reward / annual_spend if annual_spend > 0 else 0.0
        else:
            effective_rate = _rate_for_card_category(card_rates, "Groceries")
            actual_reward = annual_spend * effective_rate

        by_category.append({
            "category": "Groceries",
            "card": card,
            "annual_spend": annual_spend,
            "earn_rate": round(effective_rate, 4),
            "annual_reward": round(actual_reward, 2),
        })

    # No cap card in portfolio -- skip cap-aware leak detection
    if capped_slug is None or cap_amount is None:
        for card, annual_spend in grocery_by_card.items():
            if annual_spend <= 100:
                continue
            card_rates = all_card_rates.get(card, {})
            current_rate = _rate_for_card_category(card_rates, "Groceries")
            best_card, best_rate = _best_rate_for_category(
                "Groceries", all_card_rates
            )
            if best_rate > current_rate:
                leaks.append({
                    "category": "Groceries",
                    "current_card": card,
                    "current_rate": current_rate,
                    "best_card": best_card,
                    "best_rate": best_rate,
                    "annual_spend": annual_spend,
                    "annual_leak": round(
                        annual_spend * (best_rate - current_rate), 2
                    ),
                })
        return

    # Cap-aware leak detection
    bcp_grocery = grocery_by_card.get(capped_slug, 0.0)
    cap_remaining = max(0.0, cap_amount - bcp_grocery)

    for card, annual_spend in grocery_by_card.items():
        if annual_spend <= 100:
            continue

        if card == capped_slug:
            # BCP overflow above the cap earns after_cap_rate -- leak if alt is better
            over_cap = max(0.0, annual_spend - cap_amount)
            if over_cap > 100 and alt_rate > after_cap_rate:
                leaks.append({
                    "category": "Groceries",
                    "current_card": card,
                    "current_rate": after_cap_rate,
                    "best_card": alt_slug,
                    "best_rate": alt_rate,
                    "annual_spend": round(over_cap, 0),
                    "annual_leak": round(
                        over_cap * (alt_rate - after_cap_rate), 2
                    ),
                    "note": (
                        f"BCP grocery cap (${cap_amount:,.0f}/yr) exceeded; "
                        f"overflow earns {after_cap_rate:.1%} vs "
                        f"{alt_rate:.1%} on {alt_slug}"
                    ),
                })
        else:
            # Non-BCP card: only a leak if cap has room
            card_rates = all_card_rates.get(card, {})
            current_rate = _rate_for_card_category(card_rates, "Groceries")
            leakable = min(annual_spend, cap_remaining)
            if leakable > 100 and capped_rate > current_rate:
                leaks.append({
                    "category": "Groceries",
                    "current_card": card,
                    "current_rate": current_rate,
                    "best_card": capped_slug,
                    "best_rate": capped_rate,
                    "annual_spend": round(leakable, 0),
                    "annual_leak": round(
                        leakable * (capped_rate - current_rate), 2
                    ),
                    "note": (
                        f"BCP cap has ${cap_remaining:,.0f} room; "
                        f"could earn {capped_rate:.1%} vs {current_rate:.1%}"
                    ),
                })
                cap_remaining -= leakable


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

    # Exclude checking accounts -- they don't earn credit card rewards
    cc_cards = set(all_card_rates.keys())
    if cc_cards:
        df = df[df["card"].isin(cc_cards)].copy()
    if df.empty:
        return {"error": "No credit card transactions found."}

    # Filter to trailing N months
    cutoff = df["date"].max() - pd.DateOffset(months=months)
    df = df[df["date"] >= cutoff].copy()

    n_months = df["date"].dt.to_period("M").nunique()
    if n_months == 0:
        return {"error": "No transactions in the requested window."}

    annualize = 12 / n_months

    by_category: list[dict] = []
    leaks: list[dict] = []

    # Split grocery and non-grocery transactions
    df_grocery = df[df["category"] == "Groceries"]
    df_other = df[df["category"] != "Groceries"]

    # --- Non-grocery categories (no cap complexity) ---
    for (cat, card), group in df_other.groupby(["category", "card"]):
        period_spend = float(group["amount"].sum())
        annual_spend = round(period_spend * annualize, 0)

        card_rates = all_card_rates.get(card, {})
        current_rate = _rate_for_card_category(card_rates, cat)
        current_reward = annual_spend * current_rate

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

    # --- Grocery category (cap-aware) ---
    _handle_grocery_rewards(df_grocery, all_card_rates, annualize, by_category, leaks)

    total_spend = sum(r["annual_spend"] for r in by_category) or 1.0
    total_current = sum(r["annual_reward"] for r in by_category)

    # Optimal total: cap-aware for groceries, simple best-rate for others
    category_spend: dict[str, float] = {}
    for row in by_category:
        category_spend[row["category"]] = (
            category_spend.get(row["category"], 0.0) + row["annual_spend"]
        )

    total_optimal = 0.0
    for cat, spend in category_spend.items():
        if cat == "Groceries":
            total_optimal += _optimal_grocery_rewards(spend, all_card_rates)
        else:
            total_optimal += spend * _best_rate_for_category(cat, all_card_rates)[1]

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
