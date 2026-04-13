"""
Merchant normalization for credit card statement entries.

Maps raw merchant strings to clean (name, category, subcategory) tuples
using compiled regex patterns.
"""

import re


###############################################################################
# Merchant Pattern Registry
###############################################################################

# Each entry: (regex_pattern, clean_name, category, subcategory)
# Order matters -- more specific patterns must come before general ones.

_MERCHANT_PATTERNS: list[tuple[str, str, str, str]] = [
    # -------------------------------------------------------------------------
    # Groceries
    # -------------------------------------------------------------------------
    (r"WEGMANS", "Wegmans", "Groceries", "Supermarket"),
    (r"TRADER\s*JOE", "Trader Joe's", "Groceries", "Supermarket"),
    (r"FRED\s*MEYER(?!.*FUEL)", "Fred Meyer", "Groceries", "Supermarket"),
    (r"COSTCO\s*WHSE", "Costco", "Groceries", "Warehouse"),
    (r"QFC", "QFC", "Groceries", "Supermarket"),
    (r"ACME\s*(MARKETS?|STORE)?", "Acme", "Groceries", "Supermarket"),
    (r"GROCERY\s*OUTLET", "Grocery Outlet", "Groceries", "Discount"),
    (r"SEA\s*MART", "Sea Mart", "Groceries", "Supermarket"),
    (r"WHOLE\s*FOODS", "Whole Foods", "Groceries", "Supermarket"),
    (r"ALDI", "Aldi", "Groceries", "Discount"),
    (r"KROGER", "Kroger", "Groceries", "Supermarket"),
    (r"SAFEWAY", "Safeway", "Groceries", "Supermarket"),
    (r"PUBLIX", "Publix", "Groceries", "Supermarket"),
    (r"H[- ]?E[- ]?B\b", "H-E-B", "Groceries", "Supermarket"),
    (r"WEIS\s*MARKETS?", "Weis Markets", "Groceries", "Supermarket"),
    (r"GIANT\s*(FOOD)?", "Giant", "Groceries", "Supermarket"),
    (r"STOP\s*&?\s*SHOP", "Stop & Shop", "Groceries", "Supermarket"),
    (r"FOOD\s*LION", "Food Lion", "Groceries", "Supermarket"),
    (r"HARRIS\s*TEETER", "Harris Teeter", "Groceries", "Supermarket"),
    (r"SPROUTS", "Sprouts", "Groceries", "Supermarket"),

    # -------------------------------------------------------------------------
    # Dining
    # -------------------------------------------------------------------------
    (r"STARBUCKS", "Starbucks", "Dining", "Coffee"),
    (r"DUNKIN", "Dunkin'", "Dining", "Coffee"),
    (r"CHICK-?FIL-?A", "Chick-fil-A", "Dining", "Fast Food"),
    (r"MCDONALD", "McDonald's", "Dining", "Fast Food"),
    (r"PAPA\s*JOHN", "Papa John's", "Dining", "Pizza"),
    (r"FIVE\s*GUYS", "Five Guys", "Dining", "Fast Food"),
    (r"JERSEY\s*MIKE", "Jersey Mike's", "Dining", "Fast Food"),
    (r"BUFFALO\s*WILD\s*WINGS", "Buffalo Wild Wings", "Dining", "Casual Dining"),
    (r"LONGHORN", "LongHorn Steakhouse", "Dining", "Casual Dining"),
    (r"COLD\s*STONE", "Cold Stone Creamery", "Dining", "Dessert"),
    (r"TST\*\s*DRIP|DRIP\s*-?\s*THE\s*FLAVOR", "Drip - The Flavor Lab", "Dining", "Coffee"),
    (r"CHIPOTLE", "Chipotle", "Dining", "Fast Casual"),
    (r"TACO\s*BELL", "Taco Bell", "Dining", "Fast Food"),
    (r"WENDY", "Wendy's", "Dining", "Fast Food"),
    (r"BURGER\s*KING", "Burger King", "Dining", "Fast Food"),
    (r"PANERA", "Panera Bread", "Dining", "Fast Casual"),
    (r"OLIVE\s*GARDEN", "Olive Garden", "Dining", "Casual Dining"),
    (r"RED\s*ROBIN", "Red Robin", "Dining", "Casual Dining"),
    (r"APPLEBEE", "Applebee's", "Dining", "Casual Dining"),
    (r"OUTBACK\s*STEAK", "Outback Steakhouse", "Dining", "Casual Dining"),
    (r"DENNY", "Denny's", "Dining", "Casual Dining"),
    (r"POPEYE", "Popeyes", "Dining", "Fast Food"),
    (r"SONIC\s*DRIVE", "Sonic Drive-In", "Dining", "Fast Food"),
    (r"CRACKER\s*BARREL", "Cracker Barrel", "Dining", "Casual Dining"),
    (r"WAFFLE\s*HOUSE", "Waffle House", "Dining", "Casual Dining"),
    (r"PANDA\s*EXPRESS", "Panda Express", "Dining", "Fast Food"),
    (r"WH?ATABURGER", "Whataburger", "Dining", "Fast Food"),
    (r"RAISING\s*CANE", "Raising Cane's", "Dining", "Fast Food"),
    (r"CULVER", "Culver's", "Dining", "Fast Food"),

    # -------------------------------------------------------------------------
    # Delivery
    # -------------------------------------------------------------------------
    (r"DD\s*\*\s*DOORDASH|DOORDASH", "DoorDash", "Delivery", "Food Delivery"),
    (r"UBER\s*EAT", "Uber Eats", "Delivery", "Food Delivery"),
    (r"GRUBHUB", "Grubhub", "Delivery", "Food Delivery"),
    (r"INSTACART", "Instacart", "Delivery", "Grocery Delivery"),
    (r"POSTMATES", "Postmates", "Delivery", "Food Delivery"),

    # -------------------------------------------------------------------------
    # Amazon
    # -------------------------------------------------------------------------
    (r"AMAZON\s*PRIME", "Amazon Prime", "Amazon", "Subscription"),
    (r"AUDIBLE", "Audible", "Amazon", "Subscription"),
    (r"AMZN\s*MKTP|AMAZON\.COM|AMAZON\s*MKTPL|AMZN\.COM", "Amazon", "Amazon", "Marketplace"),
    (r"AWS", "AWS", "Amazon", "Cloud Services"),

    # -------------------------------------------------------------------------
    # Gas / Fuel
    # -------------------------------------------------------------------------
    (r"SHEETZ", "Sheetz", "Gas", "Gas Station"),
    (r"COSTCO\s*GAS|COSTCO\s*FUEL", "Costco Gas", "Gas", "Gas Station"),
    (r"FRED\s*MEYER.*FUEL", "Fred Meyer Fuel", "Gas", "Gas Station"),
    (r"UNION\s*76|76\s*-\s*", "Union 76", "Gas", "Gas Station"),
    (r"ARCO", "Arco", "Gas", "Gas Station"),
    (r"CHEVRON", "Chevron", "Gas", "Gas Station"),
    (r"SHELL\s*(OIL|SERVICE|GAS)?", "Shell", "Gas", "Gas Station"),
    (r"EXXON|MOBIL", "ExxonMobil", "Gas", "Gas Station"),
    (r"BP\b|BRITISH\s*PETRO", "BP", "Gas", "Gas Station"),
    (r"WAWA", "Wawa", "Gas", "Gas Station"),
    (r"SPEEDWAY", "Speedway", "Gas", "Gas Station"),
    (r"SUNOCO", "Sunoco", "Gas", "Gas Station"),
    (r"MARATHON\s*(GAS|PETRO)?", "Marathon", "Gas", "Gas Station"),

    # -------------------------------------------------------------------------
    # Streaming
    # -------------------------------------------------------------------------
    (r"NETFLIX", "Netflix", "Streaming", "Video"),
    (r"SPOTIFY", "Spotify", "Streaming", "Music"),
    (r"DISNEY\s*\+|DISNEYPLUS", "Disney+", "Streaming", "Video"),
    (r"HULU", "Hulu", "Streaming", "Video"),
    (r"YOUTUBE\s*PREM", "YouTube Premium", "Streaming", "Video"),
    (r"HBO\s*MAX|MAX\.COM", "Max", "Streaming", "Video"),
    (r"APPLE\s*TV", "Apple TV+", "Streaming", "Video"),
    (r"PEACOCK", "Peacock", "Streaming", "Video"),
    (r"PARAMOUNT\s*\+|PARAMOUNTPLUS", "Paramount+", "Streaming", "Video"),
    (r"AMAZON\s*VIDEO|PRIME\s*VIDEO", "Prime Video", "Streaming", "Video"),

    # -------------------------------------------------------------------------
    # Software / Subscriptions
    # -------------------------------------------------------------------------
    (r"DIGITALOCEAN", "DigitalOcean", "Software", "Cloud Services"),
    (r"OPENAI|CHATGPT", "OpenAI", "Software", "AI"),
    (r"ANTHROPIC", "Anthropic", "Software", "AI"),
    (r"CURSOR", "Cursor", "Software", "Developer Tools"),
    (r"DOCKER", "Docker", "Software", "Developer Tools"),
    (r"ADOBE", "Adobe", "Software", "Creative"),
    (r"COURSERA", "Coursera", "Software", "Education"),
    (r"GOOGLE\s*CLOUD|GCP", "Google Cloud", "Software", "Cloud Services"),
    (r"QUICKBOOKS|INTUIT\s*QUICKBOOKS", "QuickBooks", "Software", "Finance"),
    (r"DISCORD", "Discord", "Software", "Communication"),
    (r"PATREON", "Patreon", "Software", "Subscription"),
    (r"GITHUB", "GitHub", "Software", "Developer Tools"),
    (r"NOTION", "Notion", "Software", "Productivity"),
    (r"SLACK", "Slack", "Software", "Communication"),
    (r"ZOOM\s*(VIDEO)?", "Zoom", "Software", "Communication"),
    (r"APPLE\.COM/BILL|ITUNES", "Apple Services", "Software", "Subscription"),
    (r"GOOGLE\s*\*", "Google Services", "Software", "Subscription"),

    # -------------------------------------------------------------------------
    # Telecom
    # -------------------------------------------------------------------------
    (r"DIRECTV|DIRECT\s*TV", "DirecTV Stream", "Telecom", "TV"),
    (r"COMCAST|XFINITY", "Xfinity", "Telecom", "Internet"),
    (r"ASTOUND|RCN", "Astound/RCN", "Telecom", "Internet"),
    (r"T-?\s*MOBILE", "T-Mobile", "Telecom", "Wireless"),
    (r"VERIZON", "Verizon", "Telecom", "Wireless"),
    (r"AT&T|ATT\b", "AT&T", "Telecom", "Wireless"),

    # -------------------------------------------------------------------------
    # Shopping
    # -------------------------------------------------------------------------
    (r"TARGET", "Target", "Shopping", "Department Store"),
    (r"MARSHALLS", "Marshalls", "Shopping", "Discount"),
    (r"TJ\s*MAXX|TJMAXX", "TJ Maxx", "Shopping", "Discount"),
    (r"HOMEGOODS", "HomeGoods", "Shopping", "Home"),
    (r"OLD\s*NAVY", "Old Navy", "Shopping", "Clothing"),
    (r"NORDSTROM", "Nordstrom", "Shopping", "Department Store"),
    (r"WALMART", "Walmart", "Shopping", "Department Store"),
    (r"APPLE\s*(STORE|ONLINE)", "Apple Store", "Shopping", "Electronics"),
    (r"BEST\s*BUY", "Best Buy", "Shopping", "Electronics"),
    (r"COSTCO(?!\s*(GAS|FUEL|WHSE))", "Costco", "Shopping", "Warehouse"),
    (r"AMAZON(?!\s*(PRIME|VIDEO))", "Amazon", "Shopping", "Online"),
    (r"KOHLS|KOHL'S", "Kohl's", "Shopping", "Department Store"),
    (r"\bMACY", "Macy's", "Shopping", "Department Store"),
    (r"ROSS\s*(DRESS|STORE)?", "Ross", "Shopping", "Discount"),
    (r"DOLLAR\s*(TREE|GENERAL)", "Dollar Store", "Shopping", "Discount"),
    (r"BED\s*BATH", "Bed Bath & Beyond", "Shopping", "Home"),
    (r"BATH\s*&?\s*BODY\s*WORKS", "Bath & Body Works", "Shopping", "Personal Care"),

    # -------------------------------------------------------------------------
    # Home
    # -------------------------------------------------------------------------
    (r"HOME\s*DEPOT", "Home Depot", "Home", "Hardware"),
    (r"IKEA", "IKEA", "Home", "Furniture"),
    (r"LA-?Z-?BOY|LAZBOY", "La-Z-Boy", "Home", "Furniture"),
    (r"POTTERY\s*BARN", "Pottery Barn", "Home", "Furniture"),
    (r"LOWE'?S\b", "Lowe's", "Home", "Hardware"),
    (r"MENARDS", "Menards", "Home", "Hardware"),
    (r"ACE\s*HARDWARE", "Ace Hardware", "Home", "Hardware"),
    (r"WAYFAIR", "Wayfair", "Home", "Furniture"),
    (r"CRATE\s*&?\s*BARREL", "Crate & Barrel", "Home", "Furniture"),
    (r"WILLIAMS\s*SONOMA", "Williams Sonoma", "Home", "Kitchen"),

    # -------------------------------------------------------------------------
    # Healthcare
    # -------------------------------------------------------------------------
    (r"WILLIAM\s*PENN\s*VET", "William Penn Vet", "Healthcare", "Veterinary"),
    (r"A\s*PET\s*CLINIC", "A Pet Clinic", "Healthcare", "Veterinary"),
    (r"ST\.?\s*LUKE", "St. Luke's", "Healthcare", "Hospital"),
    (r"SWEDISH\s*MEDICAL", "Swedish Medical", "Healthcare", "Hospital"),
    (r"CVS", "CVS", "Healthcare", "Pharmacy"),
    (r"WALGREENS", "Walgreens", "Healthcare", "Pharmacy"),
    (r"RITE\s*AID", "Rite Aid", "Healthcare", "Pharmacy"),
    (r"KAISER", "Kaiser Permanente", "Healthcare", "Hospital"),

    # -------------------------------------------------------------------------
    # Travel -- rides/car rental (specific before general)
    # -------------------------------------------------------------------------
    (r"AMERICAN\s*AIR", "American Airlines", "Travel", "Flights"),
    (r"UNITED\s*AIR", "United Airlines", "Travel", "Flights"),
    (r"SPIRIT\s*AIR", "Spirit Airlines", "Travel", "Flights"),
    (r"DELTA\s*AIR", "Delta Air Lines", "Travel", "Flights"),
    (r"SOUTHWEST\s*AIR", "Southwest Airlines", "Travel", "Flights"),
    (r"JETBLUE", "JetBlue", "Travel", "Flights"),
    (r"ALASKA\s*AIR", "Alaska Airlines", "Travel", "Flights"),
    (r"FRONTIER\s*AIR", "Frontier Airlines", "Travel", "Flights"),
    (r"AIRBNB", "Airbnb", "Travel", "Lodging"),
    (r"HILTON", "Hilton", "Travel", "Lodging"),
    (r"MARRIOTT", "Marriott", "Travel", "Lodging"),
    (r"HYATT", "Hyatt", "Travel", "Lodging"),
    (r"HOLIDAY\s*INN", "Holiday Inn", "Travel", "Lodging"),
    (r"AVIS\b", "Avis", "Travel", "Car Rental"),
    (r"BUDGET\s*(RENT|CAR)?", "Budget", "Travel", "Car Rental"),
    (r"SIXT", "Sixt", "Travel", "Car Rental"),
    (r"ENTERPRISE\s*(RENT)?", "Enterprise", "Travel", "Car Rental"),
    (r"EXPEDIA", "Expedia", "Travel", "Booking"),
    (r"CHASE\s*TRAVEL", "Chase Travel", "Travel", "Booking"),
    (r"UBER(?!\s*EAT)", "Uber", "Travel", "Rideshare"),
    (r"LYFT", "Lyft", "Travel", "Rideshare"),
    (r"HERTZ", "Hertz", "Travel", "Car Rental"),
    (r"NATIONAL\s*CAR", "National Car Rental", "Travel", "Car Rental"),

    # -------------------------------------------------------------------------
    # Childcare
    # -------------------------------------------------------------------------
    (r"KINDERCARE", "KinderCare", "Childcare", "Daycare"),
    (r"BRIGHT\s*HORIZONS", "Bright Horizons", "Childcare", "Daycare"),

    # -------------------------------------------------------------------------
    # Insurance
    # -------------------------------------------------------------------------
    (r"PROGRESSIVE", "Progressive", "Insurance", "Auto"),
    (r"GEICO", "GEICO", "Insurance", "Auto"),
    (r"STATE\s*FARM", "State Farm", "Insurance", "Auto"),
    (r"ALLSTATE", "Allstate", "Insurance", "Auto"),

    # -------------------------------------------------------------------------
    # Utilities
    # -------------------------------------------------------------------------
    (r"FIRSTENERGY|FIRST\s*ENERGY", "FirstEnergy", "Utilities", "Electric"),
    (r"PUGET\s*SOUND\s*ENERGY|PSE\b", "Puget Sound Energy", "Utilities", "Electric"),
    (r"UGI\b", "UGI", "Utilities", "Gas"),
    (r"SOOS\s*CREEK", "Soos Creek", "Utilities", "Water"),
    (r"REPUBLIC\s*SERVICES", "Republic Services", "Utilities", "Waste"),

    # -------------------------------------------------------------------------
    # Alcohol
    # -------------------------------------------------------------------------
    (r"PA\s*WINE\s*&?\s*SPIRITS|FINE\s*WINE\s*&?\s*GOOD\s*SPIRITS", "PA Wine & Spirits", "Alcohol", "Liquor Store"),
    (r"EASTON\s*WINE\s*PROJECT", "Easton Wine Project", "Alcohol", "Wine Bar"),
    (r"TOTAL\s*WINE", "Total Wine", "Alcohol", "Liquor Store"),

    # -------------------------------------------------------------------------
    # Entertainment
    # -------------------------------------------------------------------------
    (r"MAGICCON", "MagicCon", "Entertainment", "Convention"),
    (r"AMC\s*THEATRE|AMC\s*MOVIE", "AMC Theatres", "Entertainment", "Movies"),
    (r"REGAL\s*(CINEMA|THEATRE)", "Regal Cinemas", "Entertainment", "Movies"),
    (r"TICKETMASTER", "Ticketmaster", "Entertainment", "Events"),
    (r"STUBHUB", "StubHub", "Entertainment", "Events"),

    # -------------------------------------------------------------------------
    # Shipping
    # -------------------------------------------------------------------------
    (r"PIRATE\s*SHIP", "Pirate Ship", "Shipping", "Postage"),
    (r"USPS", "USPS", "Shipping", "Postage"),
    (r"UPS\b", "UPS", "Shipping", "Postage"),
    (r"FEDEX", "FedEx", "Shipping", "Postage"),
]


###############################################################################
# Compiled Pattern Cache
###############################################################################

_COMPILED_PATTERNS: list[tuple[re.Pattern[str], str, str, str]] = [
    (re.compile(pattern, re.IGNORECASE), name, category, subcategory)
    for pattern, name, category, subcategory in _MERCHANT_PATTERNS
]


###############################################################################
# Public API
###############################################################################

def normalize_merchant(raw: str) -> tuple[str, str, str]:
    """
    Normalize a raw merchant string from a credit card statement.

    Parameters
    ----------
    raw : str
        Raw merchant string, e.g. "WEGMANS NAZARETH #94EASTON PA"

    Returns
    -------
    tuple[str, str, str]
        (clean_name, category, subcategory). Falls back to
        (raw, "Other", "Uncategorized") when no pattern matches.
    """
    stripped = raw.strip()
    for compiled_re, name, category, subcategory in _COMPILED_PATTERNS:
        if compiled_re.search(stripped):
            return (name, category, subcategory)
    return (stripped, "Other", "Uncategorized")


def get_uncategorized(merchants: list[str]) -> list[str]:
    """
    Return merchants that do not match any known pattern.

    Parameters
    ----------
    merchants : list[str]
        List of raw merchant strings.

    Returns
    -------
    list[str]
        Subset of merchants whose category resolves to "Other".
    """
    return [m for m in merchants if normalize_merchant(m)[1] == "Other"]
