"""Tests for merchant normalization module."""

import pytest

from lib.normalize import normalize_merchant, get_uncategorized


###############################################################################
# Parametrized tests for normalize_merchant
###############################################################################

@pytest.mark.parametrize(
    "raw, expected",
    [
        # Groceries
        (
            "WEGMANS NAZARETH #94EASTON PA",
            ("Wegmans", "Groceries", "Supermarket"),
        ),
        (
            "TRADER JOE'S #567 BETHLEHEM PA",
            ("Trader Joe's", "Groceries", "Supermarket"),
        ),
        (
            "FRED MEYER #123 SEATTLE WA",
            ("Fred Meyer", "Groceries", "Supermarket"),
        ),
        # Fred Meyer Fuel must go to Gas, not Groceries
        (
            "FRED MEYER FUEL #456 KENT WA",
            ("Fred Meyer Fuel", "Gas", "Gas Station"),
        ),
        # Dining
        (
            "STARBUCKS STORE 12345",
            ("Starbucks", "Dining", "Coffee"),
        ),
        (
            "CHICK-FIL-A #01234",
            ("Chick-fil-A", "Dining", "Fast Food"),
        ),
        (
            "TST* DRIP - THE FLAVOR LABOR EASTON PA",
            ("Drip - The Flavor Lab", "Dining", "Coffee"),
        ),
        # Delivery
        (
            "DD *DOORDASH THAI PLACE",
            ("DoorDash", "Delivery", "Food Delivery"),
        ),
        (
            "UBER EATS PENDING",
            ("Uber Eats", "Delivery", "Food Delivery"),
        ),
        # Amazon
        (
            "AMZN MKTP US*AB1CD2EF3",
            ("Amazon", "Amazon", "Marketplace"),
        ),
        (
            "AMAZON PRIME*AB12CD34",
            ("Amazon Prime", "Amazon", "Subscription"),
        ),
        (
            "AUDIBLE US*AB1234567",
            ("Audible", "Amazon", "Subscription"),
        ),
        # Gas
        (
            "SHEETZ 0392 EASTON PA",
            ("Sheetz", "Gas", "Gas Station"),
        ),
        (
            "COSTCO GAS #1234",
            ("Costco Gas", "Gas", "Gas Station"),
        ),
        # Streaming
        (
            "NETFLIX.COM 800-585-8003 CA",
            ("Netflix", "Streaming", "Video"),
        ),
        (
            "SPOTIFY USA",
            ("Spotify", "Streaming", "Music"),
        ),
        # Software
        (
            "OPENAI *CHATGPT SUBSCRIPTION",
            ("OpenAI", "Software", "AI"),
        ),
        (
            "ANTHROPIC US",
            ("Anthropic", "Software", "AI"),
        ),
        (
            "DIGITALOCEAN.COM CLOUD",
            ("DigitalOcean", "Software", "Cloud Services"),
        ),
        (
            "APPLE.COM/BILL ONE APPLE PARK",
            ("Apple Services", "Software", "Subscription"),
        ),
        # Shopping -- Apple Store should be Shopping, not Software
        (
            "APPLE STORE #R123",
            ("Apple Store", "Shopping", "Electronics"),
        ),
        # Telecom
        (
            "COMCAST CABLE COMM 800-266-2278",
            ("Xfinity", "Telecom", "Internet"),
        ),
        # Home
        (
            "HOME DEPOT 1234",
            ("Home Depot", "Home", "Hardware"),
        ),
        # Healthcare
        (
            "WILLIAM PENN VET CLINIC",
            ("William Penn Vet", "Healthcare", "Veterinary"),
        ),
        (
            "CVS/PHARMACY #04567",
            ("CVS", "Healthcare", "Pharmacy"),
        ),
        # Travel -- Uber rides should be Travel, not Delivery
        (
            "UBER *TRIP ABCDE",
            ("Uber", "Travel", "Rideshare"),
        ),
        (
            "AMERICAN AIRLINES 1234567890",
            ("American Airlines", "Travel", "Flights"),
        ),
        (
            "AIRBNB * ABCD1234",
            ("Airbnb", "Travel", "Lodging"),
        ),
        # Childcare
        (
            "KINDERCARE LEARNING #456",
            ("KinderCare", "Childcare", "Daycare"),
        ),
        # Insurance
        (
            "PROGRESSIVE *AUTOPAY",
            ("Progressive", "Insurance", "Auto"),
        ),
        # Utilities
        (
            "FIRSTENERGY ONLINE PMT",
            ("FirstEnergy", "Utilities", "Electric"),
        ),
        (
            "REPUBLIC SERVICES #789",
            ("Republic Services", "Utilities", "Waste"),
        ),
        # Alcohol
        (
            "PA WINE & SPIRITS #4321",
            ("PA Wine & Spirits", "Alcohol", "Liquor Store"),
        ),
        # Entertainment
        (
            "MAGICCON LAS VEGAS NV",
            ("MagicCon", "Entertainment", "Convention"),
        ),
        # Shipping
        (
            "PIRATE SHIP LABEL",
            ("Pirate Ship", "Shipping", "Postage"),
        ),
        (
            "USPS PO BOXES ONLINE",
            ("USPS", "Shipping", "Postage"),
        ),
        # Unknown -- should fall through to Other
        (
            "RANDOM UNKNOWN MERCHANT 12345",
            ("RANDOM UNKNOWN MERCHANT 12345", "Other", "Uncategorized"),
        ),
    ],
    ids=[
        "wegmans",
        "trader_joes",
        "fred_meyer_grocery",
        "fred_meyer_fuel",
        "starbucks",
        "chick_fil_a",
        "drip_flavor_lab",
        "doordash",
        "uber_eats",
        "amazon_marketplace",
        "amazon_prime",
        "audible",
        "sheetz",
        "costco_gas",
        "netflix",
        "spotify",
        "openai",
        "anthropic",
        "digitalocean",
        "apple_com_bill",
        "apple_store",
        "comcast",
        "home_depot",
        "william_penn_vet",
        "cvs",
        "uber_rides",
        "american_airlines",
        "airbnb",
        "kindercare",
        "progressive",
        "firstenergy",
        "republic_services",
        "pa_wine_spirits",
        "magiccon",
        "pirate_ship",
        "usps",
        "unknown_merchant",
    ],
)
def test_normalize_merchant(raw: str, expected: tuple[str, str, str]) -> None:
    assert normalize_merchant(raw) == expected


###############################################################################
# Tests for get_uncategorized
###############################################################################

def test_get_uncategorized_returns_only_unmatched() -> None:
    merchants = [
        "WEGMANS NAZARETH #94",
        "STARBUCKS STORE 999",
        "SOME RANDOM PLACE",
        "ANOTHER UNKNOWN SHOP",
    ]
    result = get_uncategorized(merchants)
    assert result == ["SOME RANDOM PLACE", "ANOTHER UNKNOWN SHOP"]


def test_get_uncategorized_empty_list() -> None:
    assert get_uncategorized([]) == []


def test_get_uncategorized_all_matched() -> None:
    merchants = ["WEGMANS #1", "NETFLIX.COM"]
    assert get_uncategorized(merchants) == []


###############################################################################
# Edge case tests
###############################################################################

def test_case_insensitive_matching() -> None:
    assert normalize_merchant("wegmans nazareth")[0] == "Wegmans"
    assert normalize_merchant("Netflix.com")[0] == "Netflix"


def test_whitespace_stripped() -> None:
    assert normalize_merchant("  WEGMANS #1  ")[0] == "Wegmans"
