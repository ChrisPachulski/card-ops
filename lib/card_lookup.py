"""
Card product lookup from known-cards.yml.

The user says "I have a BCP" -- this module returns the correct earn rates,
annual fee, and notes without asking the user to type in numbers they don't know.
"""
from __future__ import annotations

from pathlib import Path

import yaml


###############################################################################
# Paths
###############################################################################

CARD_OPS_ROOT = Path(__file__).parent.parent
KNOWN_CARDS_PATH = CARD_OPS_ROOT / "data" / "known-cards.yml"


###############################################################################
# Types
###############################################################################

from typing import TypedDict


class KnownCard(TypedDict):
    slug: str
    issuer: str
    card: str
    aliases: list[str]
    annual_fee: int | float
    earn_rates: dict[str, float]
    rate_overrides: dict[str, float]  # merchant -> rate (issuer-specific exclusions)
    notes: list[str]
    requires: str


###############################################################################
# Load + Index
###############################################################################

_CACHE: dict[str, KnownCard] | None = None
_ALIAS_INDEX: dict[str, str] | None = None


def _load_known_cards() -> dict[str, KnownCard]:
    """Load known-cards.yml and return dict keyed by slug."""
    global _CACHE
    if _CACHE is not None:
        return _CACHE

    with open(KNOWN_CARDS_PATH, encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    cards: dict[str, KnownCard] = {}
    for slug, data in raw.items():
        cards[slug] = KnownCard(
            slug=slug,
            issuer=data.get("issuer", ""),
            card=data.get("card", ""),
            aliases=data.get("aliases", []),
            annual_fee=data.get("annual_fee", 0),
            earn_rates=data.get("earn_rates", {}),
            rate_overrides=data.get("rate_overrides", {}),
            notes=data.get("notes", []),
            requires=data.get("requires", ""),
        )

    _CACHE = cards
    return cards


def _build_alias_index() -> dict[str, str]:
    """Build a case-insensitive alias -> slug index."""
    global _ALIAS_INDEX
    if _ALIAS_INDEX is not None:
        return _ALIAS_INDEX

    cards = _load_known_cards()
    index: dict[str, str] = {}

    for slug, card in cards.items():
        # Index by slug
        index[slug.lower()] = slug
        # Index by each alias
        for alias in card["aliases"]:
            index[alias.lower()] = slug
        # Index by "issuer card" combination
        full_name = f"{card['issuer']} {card['card']}".lower()
        index[full_name] = slug
        # Index by just the card name
        index[card["card"].lower()] = slug

    _ALIAS_INDEX = index
    return index


###############################################################################
# Public API
###############################################################################

def lookup_card(name: str) -> KnownCard | None:
    """Look up a card product by name, alias, or slug.

    Case-insensitive. Returns None if not found -- caller should then use
    ``resolve_unknown_card()`` to web-search and add it.

    >>> lookup_card("BCP")
    KnownCard(slug='amex-blue-cash-preferred', issuer='American Express', ...)

    >>> lookup_card("Wells Fargo Active Cash")
    KnownCard(slug='wf-active-cash', ...)
    """
    index = _build_alias_index()
    return _load_known_cards().get(index.get(name.lower().strip()))


def list_known_cards() -> list[str]:
    """Return all known card slugs."""
    return list(_load_known_cards().keys())


def search_cards(query: str) -> list[KnownCard]:
    """Fuzzy search: return cards where query appears in any alias, name, or issuer."""
    query_lower = query.lower().strip()
    cards = _load_known_cards()
    results: list[KnownCard] = []

    for slug, card in cards.items():
        searchable = [
            slug,
            card["issuer"].lower(),
            card["card"].lower(),
        ] + [a.lower() for a in card["aliases"]]

        if any(query_lower in s for s in searchable):
            results.append(card)

    return results


def earn_rates_for_card(name: str) -> dict[str, float] | None:
    """Shortcut: look up a card and return just the earn_rates dict.

    Returns None if card not found.
    """
    card = lookup_card(name)
    if card is None:
        return None
    return dict(card["earn_rates"])


###############################################################################
# Cache-miss handler: add a new card to known-cards.yml
###############################################################################

def add_card(
    slug: str,
    issuer: str,
    card_name: str,
    aliases: list[str],
    annual_fee: int | float,
    earn_rates: dict[str, float],
    notes: list[str] | None = None,
    requires: str = "",
) -> KnownCard:
    """Add a newly-discovered card to known-cards.yml and return it.

    Call this after web-searching the issuer's product page for a card
    that wasn't in the file. The card is appended to the YAML and the
    in-memory cache is invalidated so subsequent lookups find it.

    The caller (Claude during onboarding) is responsible for:
    1. Web-searching the issuer page to get earn_rates
    2. Verifying the rates are current
    3. Calling this function with the verified data

    This function handles persistence and cache invalidation.
    """
    global _CACHE, _ALIAS_INDEX

    entry = {
        "issuer": issuer,
        "card": card_name,
        "aliases": aliases,
        "annual_fee": annual_fee,
        "earn_rates": earn_rates,
    }
    if notes:
        entry["notes"] = notes
    if requires:
        entry["requires"] = requires

    # Append to YAML file
    with open(KNOWN_CARDS_PATH, "a", encoding="utf-8") as f:
        f.write(f"\n{slug}:\n")
        f.write(f'  issuer: "{issuer}"\n')
        f.write(f'  card: "{card_name}"\n')
        f.write(f"  aliases: {aliases}\n")
        f.write(f"  annual_fee: {annual_fee}\n")
        f.write("  earn_rates:\n")
        for k, v in earn_rates.items():
            f.write(f"    {k}: {v}\n")
        if notes:
            f.write("  notes:\n")
            for note in notes:
                f.write(f'    - "{note}"\n')
        if requires:
            f.write(f'  requires: "{requires}"\n')

    # Invalidate caches so next lookup finds the new card
    _CACHE = None
    _ALIAS_INDEX = None

    return KnownCard(
        slug=slug,
        issuer=issuer,
        card=card_name,
        aliases=aliases,
        annual_fee=annual_fee,
        earn_rates=earn_rates,
        notes=notes or [],
        requires=requires,
    )
