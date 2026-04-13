"""
Market intelligence cache manager for card-ops.

Manages a YAML cache of card offers, signup bonuses, and issuer rule
updates. The actual web searching is done by Claude at the mode level --
this module handles cache read/write/staleness logic only.

Cache location: data/market/current-offers.yml
"""

from datetime import date
from pathlib import Path

import yaml


###############################################################################
# Constants
###############################################################################

_CACHE_PATH = Path(__file__).resolve().parent.parent / "data" / "market" / "current-offers.yml"

STALENESS_THRESHOLDS: dict[str, int] = {
    "signup_bonus": 30,
    "earn_rates": 90,
    "annual_fee": 90,
    "issuer_rules": 180,
}


###############################################################################
# Internal Helpers
###############################################################################

def _load_cache() -> dict:
    """Read the YAML cache file. Returns {"cards": {}} if missing or empty."""
    if not _CACHE_PATH.exists():
        return {"cards": {}}
    text = _CACHE_PATH.read_text(encoding="utf-8")
    if not text.strip():
        return {"cards": {}}
    parsed = yaml.safe_load(text)
    if not isinstance(parsed, dict) or "cards" not in parsed:
        return {"cards": {}}
    return parsed


def _save_cache(cache: dict) -> None:
    """Write the cache dict to YAML, creating the directory if needed."""
    _CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    _CACHE_PATH.write_text(
        yaml.dump(cache, default_flow_style=False, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )


###############################################################################
# Public API
###############################################################################

def is_stale(card_slug: str, field: str = "signup_bonus") -> bool:
    """
    Check if cached data for a card is older than the staleness threshold.

    Returns True if the card is missing, has no "fetched" timestamp, or
    if the fetched date exceeds the threshold for the given field.
    """
    cache = _load_cache()
    card = cache["cards"].get(card_slug)
    if card is None:
        return True
    fetched_raw = card.get("fetched")
    if fetched_raw is None:
        return True
    # Parse the fetched date -- YAML may load it as a date or string
    if isinstance(fetched_raw, date):
        fetched_date = fetched_raw
    else:
        fetched_date = date.fromisoformat(str(fetched_raw))
    threshold_days = STALENESS_THRESHOLDS.get(field, 30)
    age_days = (date.today() - fetched_date).days
    return age_days > threshold_days


def get_cached(card_slug: str) -> dict | None:
    """Return cached card data, or None if not in cache."""
    cache = _load_cache()
    return cache["cards"].get(card_slug)


def update_cache(card_slug: str, data: dict) -> None:
    """Write or update a cache entry with today's date as the fetched timestamp."""
    cache = _load_cache()
    entry = {**data, "fetched": date.today().isoformat()}
    cache["cards"][card_slug] = entry
    _save_cache(cache)


def seed_from_burn_it_all(cards: dict[str, dict]) -> None:
    """
    Bulk-write multiple card entries to the cache.

    Used for initial seeding from a burn-it-all research sweep.
    Each entry gets today's date as its fetched timestamp.
    """
    cache = _load_cache()
    today = date.today().isoformat()
    for slug, data in cards.items():
        cache["cards"][slug] = {**data, "fetched": today}
    _save_cache(cache)
