"""
Portfolio scenario modeler for credit card optimization.

Takes annual spending by category + a list of card specs, computes optimal
routing and net rewards for each scenario.
"""

from pathlib import Path
from typing import TypedDict

import yaml


###############################################################################
# Types
###############################################################################

class CardSpec(TypedDict):
    name: str
    annual_fee: float
    earn_rates: dict[str, float]  # rate_key -> rate (e.g. "groceries": 0.06)


class ScenarioResult(TypedDict):
    name: str
    cards: list[str]
    gross_rewards: float
    total_af: float
    net_rewards: float
    effective_rate: float
    routing: dict[str, tuple[str, float]]  # category -> (card_name, rate)


###############################################################################
# Category Mapping
###############################################################################

# Maps spending categories to the rate key used in CardSpec.earn_rates
_CATEGORY_TO_RATE_KEY: dict[str, str] = {
    "Groceries": "groceries",
    "Dining": "dining",
    "Delivery": "dining",
    "Amazon": "amazon",
    "Gas": "gas",
    "Streaming": "streaming",
}


def _rate_key_for_category(category: str) -> str:
    """Return the earn_rates key for a spending category."""
    return _CATEGORY_TO_RATE_KEY.get(category, "other")


###############################################################################
# Rate Lookup
###############################################################################

def _get_card_rate(card: CardSpec, rate_key: str) -> float:
    """
    Get the earn rate a card offers for a given rate key.

    Falls back to the card's "everything" flat rate if the specific key
    is not present, then to 0.0.
    """
    rates = card["earn_rates"]
    if rate_key in rates:
        return rates[rate_key]
    if "everything" in rates:
        return rates["everything"]
    return 0.0


def _best_card_for_key(cards: list[CardSpec], rate_key: str) -> tuple[CardSpec, float]:
    """
    Find the card with the highest earn rate for a given rate key.

    Returns (card, rate).
    """
    best_card = cards[0]
    best_rate = _get_card_rate(cards[0], rate_key)

    for card in cards[1:]:
        rate = _get_card_rate(card, rate_key)
        if rate > best_rate:
            best_card = card
            best_rate = rate

    return best_card, best_rate


###############################################################################
# Grocery Cap Handling
###############################################################################

def _route_groceries(
    spend: float,
    cards: list[CardSpec],
) -> tuple[float, dict[str, tuple[str, float]]]:
    """
    Route grocery spend across cards, respecting groceries_cap limits.

    If a card has groceries_cap in its earn_rates, the high grocery rate
    applies only up to that cap. Spend above the cap uses either the card's
    groceries_after_cap rate or falls back to the next-best card.

    Returns (total_rewards, routing_dict).
    routing_dict maps descriptive keys to (card_name, rate) tuples:
      - "Groceries" when no cap split
      - "Groceries (capped)" and "Groceries (overflow)" when split
    """
    # Find the card with the best grocery rate
    best_card, best_rate = _best_card_for_key(cards, "groceries")
    cap = best_card["earn_rates"].get("groceries_cap")

    # No cap -- simple routing
    if cap is None or spend <= cap:
        rewards = spend * best_rate
        routing: dict[str, tuple[str, float]] = {
            "Groceries": (best_card["name"], best_rate),
        }
        return rewards, routing

    # Cap applies -- split spend
    capped_rewards = cap * best_rate
    overflow = spend - cap

    # For overflow: check if the capped card has an after-cap rate
    after_cap_rate = best_card["earn_rates"].get("groceries_after_cap", 0.0)

    # Find the best alternative card for overflow (excluding the capped card's
    # after-cap rate -- we compare it separately)
    other_cards = [c for c in cards if c["name"] != best_card["name"]]

    if other_cards:
        overflow_card, overflow_rate = _best_card_for_key(other_cards, "groceries")
        # If the capped card's after-cap rate beats alternatives, keep it there
        if after_cap_rate >= overflow_rate:
            overflow_card = best_card
            overflow_rate = after_cap_rate
    else:
        overflow_card = best_card
        overflow_rate = after_cap_rate

    overflow_rewards = overflow * overflow_rate

    routing = {
        "Groceries (capped)": (best_card["name"], best_rate),
        "Groceries (overflow)": (overflow_card["name"], overflow_rate),
    }
    return capped_rewards + overflow_rewards, routing


###############################################################################
# Scenario Modeling
###############################################################################

def model_scenario(
    spending: dict[str, float],
    cards: list[CardSpec],
    name: str = "scenario",
) -> ScenarioResult:
    """
    Model a portfolio scenario: compute optimal card routing and net rewards.

    For each spending category, assigns the card with the highest earn rate.
    Groceries receive special handling when a card has a groceries_cap.

    Parameters
    ----------
    spending : dict[str, float]
        Annual spend by category (e.g. {"Groceries": 9600, "Dining": 3600}).
    cards : list[CardSpec]
        Cards available in this scenario.
    name : str
        Label for the scenario.

    Returns
    -------
    ScenarioResult
        Routing decisions, gross/net rewards, and effective earn rate.
    """
    total_spend = sum(spending.values())
    gross_rewards = 0.0
    routing: dict[str, tuple[str, float]] = {}

    for category, spend in spending.items():
        if category == "Groceries":
            grocery_rewards, grocery_routing = _route_groceries(spend, cards)
            gross_rewards += grocery_rewards
            routing.update(grocery_routing)
            continue

        rate_key = _rate_key_for_category(category)
        best_card, best_rate = _best_card_for_key(cards, rate_key)
        gross_rewards += spend * best_rate
        routing[category] = (best_card["name"], best_rate)

    total_af = sum(c["annual_fee"] for c in cards)
    net_rewards = gross_rewards - total_af
    effective_rate = net_rewards / total_spend if total_spend > 0 else 0.0

    return ScenarioResult(
        name=name,
        cards=[c["name"] for c in cards],
        gross_rewards=round(gross_rewards, 2),
        total_af=round(total_af, 2),
        net_rewards=round(net_rewards, 2),
        effective_rate=round(effective_rate, 4),
        routing=routing,
    )


###############################################################################
# Scenario Comparison
###############################################################################

def compare_scenarios(
    spending: dict[str, float],
    scenarios: dict[str, list[CardSpec]],
) -> list[ScenarioResult]:
    """
    Run model_scenario for each named scenario, return sorted by net_rewards.

    Parameters
    ----------
    spending : dict[str, float]
        Annual spend by category.
    scenarios : dict[str, list[CardSpec]]
        Mapping of scenario name to list of cards.

    Returns
    -------
    list[ScenarioResult]
        Results sorted descending by net_rewards.
    """
    results = [
        model_scenario(spending, cards, name=scenario_name)
        for scenario_name, cards in scenarios.items()
    ]
    results.sort(key=lambda r: r["net_rewards"], reverse=True)
    return results


###############################################################################
# Config Loader
###############################################################################

_CONFIG_DIR = Path(__file__).resolve().parent.parent / "config"


def _parse_card_from_profile(card_entry: dict) -> CardSpec:
    """
    Convert a card entry from a profile YAML into a CardSpec.

    The profile format stores earn_rates as a flat dict that may include
    non-rate keys like groceries_cap and groceries_after_cap. These are
    preserved in earn_rates for downstream grocery-cap logic.
    """
    issuer = card_entry.get("issuer", "")
    card_name = card_entry.get("card", "")
    full_name = f"{issuer} {card_name}".strip()

    return CardSpec(
        name=full_name,
        annual_fee=float(card_entry.get("annual_fee", 0) or 0),
        earn_rates=dict(card_entry.get("earn_rates", {})),
    )


def _load_current_cards() -> list[CardSpec]:
    """
    Read config/profile-chris.yml and config/profile-dana.yml, returning
    a combined list of CardSpec for all held cards.
    """
    cards: list[CardSpec] = []

    for profile_file in ("profile-chris.yml", "profile-dana.yml"):
        profile_path = _CONFIG_DIR / profile_file
        if not profile_path.exists():
            continue

        with open(profile_path, "r", encoding="utf-8") as f:
            profile = yaml.safe_load(f)

        for card_entry in profile.get("cards", []):
            cards.append(_parse_card_from_profile(card_entry))

    return cards
