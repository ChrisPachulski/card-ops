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
        # ---- New patterns (high-volume merchants added in normalization expansion) ----
        # Wine & Spirits stores
        (
            "WINE AND SPIRITS 4814 EASTON PA",
            ("PA Wine & Spirits", "Alcohol", "Liquor Store"),
        ),
        (
            "36TH AVE WINE & SPIRITS LONG ISLAND C NY",
            ("36th Ave Wine & Spirits", "Alcohol", "Liquor Store"),
        ),
        (
            "BOURBON STREET MEMORIAL PHILLIPSBURG NJ",
            ("Bourbon Street Wine", "Alcohol", "Liquor Store"),
        ),
        # Groceries
        (
            "KEY FOOD 1620 LNG ISLND CTY NY",
            ("Key Food", "Groceries", "Supermarket"),
        ),
        (
            "IMPERFECT FOODS HTTPSWWW.IMPE CA",
            ("Imperfect Foods", "Groceries", "Delivery"),
        ),
        # Dining -- local restaurants
        (
            "TST* MCCALL COLLECTIVE BR ALLENTOWN PA",
            ("McCall Collective", "Dining", "Brewery"),
        ),
        (
            "BWW EASTON 297 678-514-4100 PA",
            ("Buffalo Wild Wings", "Dining", "Casual Dining"),
        ),
        (
            "TAKUMI SUSHI EASTON PA",
            ("Takumi Sushi", "Dining", "Restaurant"),
        ),
        (
            "3RD & FERRY FISH MARKET EASTON PA",
            ("3rd & Ferry Fish Market", "Dining", "Restaurant"),
        ),
        (
            "DINER 248 EASTON PA",
            ("Diner 248", "Dining", "Casual Dining"),
        ),
        (
            "OWOWCOW EASTON GLENDON PA",
            ("Owowcow Creamery", "Dining", "Dessert"),
        ),
        # Healthcare
        (
            "BH* BETTERHELP HTTPSWWW.BETT CA",
            ("BetterHelp", "Healthcare", "Mental Health"),
        ),
        (
            "COURT SQUARE ANIMAL HOSPI LONG ISLAND C NY",
            ("Court Square Animal Hospital", "Healthcare", "Veterinary"),
        ),
        # Shopping
        (
            "WAL-MART #2252 EASTON PA",
            ("Walmart", "Shopping", "Department Store"),
        ),
        (
            "WM SUPERCENTER #2252 EASTON PA",
            ("Walmart", "Shopping", "Department Store"),
        ),
        (
            "HOBBY LOBBY #432 EASTON PA",
            ("Hobby Lobby", "Shopping", "Crafts"),
        ),
        (
            "BARNES & NOBLE #2210 EASTON PA",
            ("Barnes & Noble", "Shopping", "Books"),
        ),
        (
            "AE OUTF ONLINE00029538 785-2297900 KS",
            ("American Eagle", "Shopping", "Clothing"),
        ),
        (
            "T J MAXX #1317 FARMINGDALE NY",
            ("TJ Maxx", "Shopping", "Discount"),
        ),
        (
            "EBAY INC. 866-779-3229 CA",
            ("eBay", "Shopping", "Online"),
        ),
        (
            "Etsy.com 718-8557955 NY",
            ("Etsy", "Shopping", "Online"),
        ),
        # Entertainment / Gaming
        (
            "PLAYSTATION NETWORK 800-345-7669 CA",
            ("PlayStation Network", "Entertainment", "Gaming"),
        ),
        (
            "TCGPLAYER.COM 315-501-0478 NY",
            ("TCGplayer", "Entertainment", "Games"),
        ),
        (
            "STEAMGAMES.COM 4259522985425-8899642 WA",
            ("Steam", "Entertainment", "Gaming"),
        ),
        # Software
        (
            "INTUIT *QBooks Online CL.INTUIT.COM CA",
            ("QuickBooks", "Software", "Finance"),
        ),
        # Gas -- 7-Eleven
        (
            "7-ELEVEN 33989 FARMINGDALE NY",
            ("7-Eleven", "Gas", "Convenience"),
        ),
        # Travel
        (
            "E-Z*PASSNY REBILL 800-333-8655 NY",
            ("E-ZPass", "Travel", "Tolls"),
        ),
        (
            "MTA*METROCARD MACHINE NEW YORK NY",
            ("MTA MetroCard", "Travel", "Transit"),
        ),
        # Home -- Shellpoint mortgage must NOT match Shell gas
        (
            "Newrez-Shellpoin Web Pmts",
            ("Newrez Shellpoint", "Home", "Mortgage"),
        ),
        # Government
        (
            "PA DRIVER & VEHICLE SERV WWW.PA.GOV PA",
            ("PennDOT", "Shopping", "Government"),
        ),
        (
            "NEW YORK STATE DMV 518-4740904 NY",
            ("NY DMV", "Shopping", "Government"),
        ),
        # Personal Care
        (
            "EWC EASTON 0485 Easton PA",
            ("European Wax Center", "Shopping", "Personal Care"),
        ),
        (
            "CLR*PureBarre6104199334 610-4199334 PA",
            ("Pure Barre", "Healthcare", "Fitness"),
        ),
        # Utilities
        (
            "EASTON SUBURBAN WATER 610-258-7181 PA",
            ("Easton Suburban Water", "Utilities", "Water"),
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
        # New pattern test IDs
        "wine_and_spirits_store",
        "36th_ave_wine",
        "bourbon_street_wine",
        "key_food",
        "imperfect_foods",
        "mccall_collective",
        "bww_easton",
        "takumi_sushi",
        "3rd_ferry_fish_market",
        "diner_248",
        "owowcow",
        "betterhelp",
        "court_square_animal",
        "walmart_hyphenated",
        "walmart_supercenter",
        "hobby_lobby",
        "barnes_noble",
        "american_eagle",
        "tj_maxx_spaced",
        "ebay",
        "etsy",
        "playstation_network",
        "tcgplayer",
        "steam",
        "quickbooks_intuit",
        "7_eleven",
        "ezpass",
        "mta_metrocard",
        "newrez_shellpoint_not_shell",
        "penndot",
        "ny_dmv",
        "european_wax_center",
        "pure_barre",
        "easton_suburban_water",
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
