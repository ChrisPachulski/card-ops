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
    (r"FRED[\s-]*MEYER(?!.*FUEL)", "Fred Meyer", "Groceries", "Supermarket"),
    (r"COSTCO\s*WHSE", "Costco", "Shopping", "Warehouse"),
    (r"QFC", "QFC", "Groceries", "Supermarket"),
    (r"ACME\s*(MARKETS?|STORE)?", "Acme", "Groceries", "Supermarket"),
    (r"GROCERY\s*OUTL", "Grocery Outlet", "Groceries", "Discount"),
    (r"SEA\s*MART", "Sea Mart", "Groceries", "Supermarket"),
    (r"WHOLE\s*FOODS", "Whole Foods", "Whole Foods", "Supermarket"),
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
    (r"KEY\s*FOOD", "Key Food", "Groceries", "Supermarket"),
    (r"IMPERFECT\s*FOODS", "Imperfect Foods", "Groceries", "Delivery"),
    (r"STEW\s*LEONARD", "Stew Leonard's", "Groceries", "Supermarket"),
    (r"FOODCELLAR\s*MARKET", "Foodcellar Market", "Groceries", "Supermarket"),
    (r"KING\s*KULLEN", "King Kullen", "Groceries", "Supermarket"),
    (r"CHERRY\s*VALLEY\s*MARKET", "Cherry Valley Market", "Groceries", "Supermarket"),
    (r"RAUB'?S\s*FARM\s*MARKET", "Raub's Farm Market", "Groceries", "Farm Market"),
    (r"RIO\s*SUPERMARKET", "Rio Supermarket", "Groceries", "Supermarket"),

    # -------------------------------------------------------------------------
    # Dining -- chains & fast food (specific before general)
    # -------------------------------------------------------------------------
    (r"STARBUCKS", "Starbucks", "Dining", "Coffee"),
    (r"DUNKIN", "Dunkin'", "Dining", "Coffee"),
    (r"CHICK-?FIL-?A", "Chick-fil-A", "Dining", "Fast Food"),
    (r"MCDONALD", "McDonald's", "Dining", "Fast Food"),
    (r"PAPA\s*JOHN", "Papa John's", "Dining", "Pizza"),
    (r"FIVE\s*GUYS|5GUYS|5\s*GUYS", "Five Guys", "Dining", "Fast Food"),
    (r"JERSEY\s*MIKE", "Jersey Mike's", "Dining", "Fast Food"),
    (r"BWW\s|BUFFALO\s*WILD\s*WINGS|BUFFALO\s*WILD\s*ECOM", "Buffalo Wild Wings", "Dining", "Casual Dining"),
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
    (r"CHILI'?S\s*BAR", "Chili's", "Dining", "Casual Dining"),
    (r"FIREHOUSE\s*SUBS", "Firehouse Subs", "Dining", "Fast Food"),
    (r"MOE'?S\s*SW\s*GRILL", "Moe's Southwest Grill", "Dining", "Fast Food"),
    (r"JOHNNY\s*ROCKETS", "Johnny Rockets", "Dining", "Fast Food"),
    (r"AUNTIE\s*ANNE", "Auntie Anne's", "Dining", "Fast Food"),
    (r"CINNABON", "Cinnabon", "Dining", "Dessert"),
    (r"MISSION\s*BBQ", "Mission BBQ", "Dining", "Casual Dining"),
    (r"JUST\s*SALAD", "Just Salad", "Dining", "Fast Casual"),
    (r"AU\s*BON\s*PAIN", "Au Bon Pain", "Dining", "Fast Casual"),

    # -------------------------------------------------------------------------
    # Dining -- local restaurants (PA, NY, WA)
    # -------------------------------------------------------------------------
    (r"TST\*\s*MCCALL\s*COLLECTI", "McCall Collective", "Dining", "Brewery"),
    (r"TAKUMI\s*SUSHI", "Takumi Sushi", "Dining", "Restaurant"),
    (r"3RD\s*(&|AND)?\s*FERRY\s*FISH\s*MARKET", "3rd & Ferry Fish Market", "Dining", "Restaurant"),
    (r"TST\*\s*BIRTHRIGHT\s*BREW|BIRTHRIGHT\s*BREW", "Birthright Brewing", "Dining", "Brewery"),
    (r"TST\*\s*BOSER\s*GEIST|BOSER\s*GEIST", "Boser Geist Brewing", "Dining", "Brewery"),
    (r"TST\*\s*TWO\s*RIVERS\s*BREW", "Two Rivers Brewing", "Dining", "Brewery"),
    (r"TST\*\s*BOLETE", "Bolete Restaurant", "Dining", "Fine Dining"),
    (r"SMILE\s*CAFE", "Smile Cafe", "Dining", "Cafe"),
    (r"DINER\s*248", "Diner 248", "Dining", "Casual Dining"),
    (r"EASTON\s*ASIAN\s*BISTRO", "Easton Asian Bistro", "Dining", "Restaurant"),
    (r"KOJA\s*CUISINE", "Koja Cuisine", "Dining", "Restaurant"),
    (r"TST\*\s*THE\s*MELTING\s*POT", "The Melting Pot", "Dining", "Fine Dining"),
    (r"TST\*\s*SORRENTI", "Sorrenti's Cherry Valley", "Dining", "Restaurant"),
    (r"TST\*\s*RANCH\s*CITY\s*BREW", "Ranch City Brewing", "Dining", "Brewery"),
    (r"TST\*\s*ALOHA\s*JAY|ALOHA\s*JAY", "Aloha Jay's", "Dining", "Restaurant"),
    (r"TST\*\s*THE\s*BAYOU", "The Bayou", "Dining", "Restaurant"),
    (r"TST\*\s*TUCKER\s*SILK\s*MILL", "Tucker Silk Mill", "Dining", "Restaurant"),
    (r"TST\*\s*FOLINO\s*ESTATE|FOLINO\s*ESTATE", "Folino Estate Winery", "Dining", "Winery"),
    (r"TST\*\s*TOLINO|TOLINO\s*VINEYARDS", "Tolino Vineyards", "Dining", "Winery"),
    (r"TST\*\s*THE\s*RAVEN", "The Raven", "Dining", "Restaurant"),
    (r"TST\*\s*MISTER\s*LEE", "Mister Lee's", "Dining", "Restaurant"),
    (r"TST\*\s*WANDERLUST\s*BEER", "Wanderlust Beer Garden", "Dining", "Brewery"),
    (r"TST\*\s*MS\.?\s*JACKSON", "Ms. Jackson's Kitchen", "Dining", "Restaurant"),
    (r"TST\*\s*SETTE\s*LUNA", "Sette Luna", "Dining", "Restaurant"),
    (r"TST\*\s*BRUCHELLES", "Bruchelle's Bagel Bistro", "Dining", "Cafe"),
    (r"TST\*\s*KHANISA", "Khanisa's Pudding", "Dining", "Dessert"),
    (r"TST\*\s*BRU\s*DADDY", "Bru Daddy's Brewing", "Dining", "Brewery"),
    (r"TST\*\s*RIOS\s*BRAZILIAN", "Rio's Brazilian Steakhouse", "Dining", "Restaurant"),
    (r"TST\*\s*ZEST", "Zest", "Dining", "Restaurant"),
    (r"TST\*\s*QUADRANT\s*BOOK\s*MART", "Quadrant Book Mart", "Dining", "Cafe"),
    (r"TST\*\s*SHARPS\s*ROAST", "Sharp's Roasthouse", "Dining", "Restaurant"),
    (r"TST\*\s*THYME", "Thyme", "Dining", "Restaurant"),
    (r"TST\*\s*LA\s*KANG\s*THAI", "La Kang Thai Eatery", "Dining", "Restaurant"),
    (r"TST\*\s*HELMSMAN", "Helmsman Ale House", "Dining", "Brewery"),
    (r"TST\*\s*GOAT\s*PUB|TST\*\s*The\s*GOAT", "The Goat Pub & Pie", "Dining", "Restaurant"),
    (r"TST\*\s*BUTCHER\s*BAR", "Butcher Bar", "Dining", "Restaurant"),
    (r"TST\*\s*CANNELLE|CANNELLE\s*(LIC|PATISSERIE)", "Cannelle Patisserie", "Dining", "Bakery"),
    (r"TST\*\s*SLICE", "Slice", "Dining", "Pizza"),
    (r"TST\*\s*AMPLE\s*HILLS", "Ample Hills Creamery", "Dining", "Dessert"),
    (r"TST\*\s*KIZUKI\s*RAMEN", "Kizuki Ramen", "Dining", "Restaurant"),
    (r"TST\*\s*NAYA\s*EXPRESS", "Naya Express", "Dining", "Fast Casual"),
    (r"TST\*\s*BEECHER", "Beecher's Handmade Cheese", "Dining", "Restaurant"),
    (r"TST\*\s*JOJU", "JoJu", "Dining", "Restaurant"),
    (r"TST\*\s*ADDENDUM", "Addendum", "Dining", "Fine Dining"),
    (r"TST\*\s*THREEBIRDS|TST\*\s*ThreeBirds", "Three Birds Coffee House", "Dining", "Coffee"),
    (r"PLAYA\s*BOWLS", "Playa Bowls", "Dining", "Fast Casual"),
    (r"THE\s*TRESTLE", "The Trestle", "Dining", "Restaurant"),
    (r"SACS\s*PLACE", "Sac's Place", "Dining", "Restaurant"),
    (r"THE\s*ALCOVE\s*RESTAURANT", "The Alcove", "Dining", "Restaurant"),
    (r"IN\s*\*\s*CAFE\s*TRISKELL", "Cafe Triskell", "Dining", "Restaurant"),
    (r"SUZUKI\s*SHOKUDO", "Suzuki Shokudo", "Dining", "Restaurant"),
    (r"DOMINIES\s*HOEK", "Dominies Hoek", "Dining", "Restaurant"),
    (r"THE\s*HIGHWATER", "The Highwater", "Dining", "Restaurant"),
    (r"ASTORIA\s*BIER\s*AND\s*CHEESE", "Astoria Bier & Cheese", "Dining", "Restaurant"),
    (r"MOKJA\s*KOR", "Mokja Korean Eatery", "Dining", "Restaurant"),
    (r"SWEET\s*AFTON", "Sweet Afton", "Dining", "Restaurant"),
    (r"MOMS\s*AND\s*HALSEYS", "Moms & Halseys", "Dining", "Restaurant"),
    (r"BEANS\s*&?\s*LAGER", "Beans & Lager", "Dining", "Restaurant"),
    (r"SALSA\s*IN\s*QUEENS", "Salsa in Queens", "Dining", "Restaurant"),
    (r"MAPLE\s*THAI\s*EATERY", "Maple Thai Eatery", "Dining", "Restaurant"),
    (r"JONGRO\s*BBQ", "Jongro BBQ", "Dining", "Restaurant"),
    (r"KOI\s*KOKORO", "Koi Kokoro", "Dining", "Restaurant"),
    (r"TULLULAHS", "Tullulah's", "Dining", "Restaurant"),
    (r"THE\s*HUNTRESS\s*BAR", "The Huntress Bar", "Dining", "Restaurant"),
    (r"RIVER\s*GRILL", "River Grill", "Dining", "Restaurant"),
    (r"BLACKSTAR\s*BAKERY", "Blackstar Bakery Cafe", "Dining", "Bakery"),
    (r"QUEENS\s*BAKEHOUSE|Queens\s*Bakehouse", "Queens Bakehouse", "Dining", "Bakery"),
    (r"NYC\s*BAGEL\s*&?\s*COFFEE", "NYC Bagel & Coffee", "Dining", "Cafe"),
    (r"BROOKLYN\s*B\*\s*BROADWAY|BROOKLYN\s*B.+BROADWAY", "Brooklyn Bagel Broadway", "Dining", "Cafe"),
    (r"OWOWCOW", "Owowcow Creamery", "Dining", "Dessert"),
    (r"PLANTS\+COFFEE|PLANTS\s*\+\s*COFFEE", "Plants + Coffee", "Dining", "Coffee"),
    (r"SQ\s*\*\s*SPECTRACOLOR\s*COFFEE", "Spectracolor Coffee", "Dining", "Coffee"),
    (r"SQ\s*\*\s*ZEKRAFT", "Zekraft", "Dining", "Cafe"),
    (r"SQ\s*\*\s*CLOUD\s*CITY\s*GAMES", "Cloud City Games", "Entertainment", "Games"),
    (r"SQ\s*\*\s*CASCADIA\s*PIZZA", "Cascadia Pizza Co.", "Dining", "Pizza"),
    (r"SQ\s*\*\s*JERSEY\s*PICKLES", "Jersey Pickles", "Dining", "Restaurant"),
    (r"SQ\s*\*\s*THE\s*SMOKIN", "The Smokin' Pasty Co.", "Dining", "Restaurant"),
    (r"SQ\s*\*\s*BITTY\s*&?\s*BEAU", "Bitty & Beau's Coffee", "Dining", "Coffee"),
    (r"SQ\s*\*\s*CERASELLA", "Cerasella", "Dining", "Restaurant"),
    (r"SQ\s*\*\s*HAWAII\s*POKE", "Hawaii Poke Bowl", "Dining", "Restaurant"),
    (r"SQ\s*\*\s*COFFEE\s*AVE", "Coffee Ave", "Dining", "Coffee"),
    (r"SQ\s*\*\s*GREAT\s*SOUTH\s*BAY\s*BREWE", "Great South Bay Brewery", "Dining", "Brewery"),
    (r"SQ\s*\*\s*BLOOM\s*BISTRO", "Bloom Bistro", "Dining", "Restaurant"),
    (r"SQ\s*\*\s*ICE\s*&?\s*VICE", "Ice & Vice", "Dining", "Dessert"),
    (r"SQ\s*\*\s*GAMESTORIA", "Gamestoria", "Entertainment", "Games"),
    (r"SQ\s*\*\s*APPLE\s*RIDGE\s*FARM", "Apple Ridge Farm", "Dining", "Farm Market"),
    (r"SQ\s*\*\s*YUMPLING", "Yumpling", "Dining", "Restaurant"),
    (r"SQ\s*\*\s*THE\s*HIVE", "The Hive", "Dining", "Cafe"),
    (r"SQ\s*\*\s*AMARE\s*HAIR", "Amare Hair Salon", "Shopping", "Personal Care"),
    (r"SQ\s*\*\s*SALON\s*AT\s*THE\s*SILK", "Salon at the Silk", "Shopping", "Personal Care"),
    (r"SQ\s*\*\s*PIE\+TART|SQ\s*\*\s*PIE\s*\+\s*TART", "Pie + Tart", "Dining", "Bakery"),
    (r"SQ\s*\*\s*MONA'?S\s*BAKERY", "Mona's Bakery", "Dining", "Bakery"),
    (r"SQ\s*\*\s*PARISI\s*BAKERY", "Parisi Bakery", "Dining", "Bakery"),
    (r"SQ\s*\*\s*PARTNERS\s*COFFEE", "Partners Coffee", "Dining", "Coffee"),
    (r"SQ\s*\*\s*TEA\s*AND\s*MILK", "Tea and Milk", "Dining", "Cafe"),
    (r"SQ\s*\*\s*L\s*&?\s*H\s*BAGEL", "L & H Bagel", "Dining", "Cafe"),
    (r"SQ\s*\*\s*LIC\s*LANDING", "LIC Landing Cafe", "Dining", "Cafe"),
    (r"SQ\s*\*\s*SCHOLL\s*ORCHARDS", "Scholl Orchards", "Dining", "Farm Market"),
    (r"SQ\s*\*\s*SONNYMOON", "Sonnymoon", "Dining", "Restaurant"),
    (r"SQ\s*\*\s*THE\s*LINWOOD", "The Linwood", "Dining", "Restaurant"),
    (r"SQ\s*\*\s*CLAURA", "Claura", "Dining", "Cafe"),
    (r"SQ\s*\*\s*HARBES\s*ORCHARD", "Harbes Orchard", "Entertainment", "Farm"),
    (r"SQ\s*\*\s*OSPREY", "Osprey's Dominion Vineyard", "Dining", "Winery"),
    (r"SQ\s*\*\s*CHIP\s*CITY", "Chip City", "Dining", "Dessert"),
    (r"SQ\s*\*\s*E\s*&?\s*P\s*PRETZELS", "E&P Pretzels", "Dining", "Fast Food"),
    (r"SQ\s*\*\s*DREAMSCAPE", "Dreamscape", "Entertainment", "Experience"),
    (r"SQ\s*\*\s*GOOD\s*GAMES", "Good Games NYC", "Entertainment", "Games"),
    (r"SQ\s*\*\s*KRAFT\s*&?\s*CO", "Kraft & Co", "Dining", "Restaurant"),
    (r"SQ\s*\*\s*ROASTWELL", "Roastwell Coffee", "Dining", "Coffee"),
    (r"SQ\s*\*\s*WEATHERED\s*VINEYARD", "Weathered Vineyards", "Dining", "Winery"),
    (r"SQ\s*\*\s*CELLAR\s*BEAST", "Cellar Beast Winehouse", "Dining", "Winery"),
    (r"SQ\s*\*\s*WOODS\s*COFFEE", "Woods Coffee", "Dining", "Coffee"),
    (r"SQ\s*\*\s*KLEIN", "Klein's Dairy Store", "Dining", "Cafe"),
    (r"UEP\*\s*NARUTO\s*RAMEN|NARUTO\s*RAMEN", "Naruto Ramen", "Dining", "Restaurant"),
    (r"TAKUMEN", "Takumen", "Dining", "Restaurant"),
    (r"RAMEN\s*KYOTO", "Ramen Kyoto", "Dining", "Restaurant"),
    (r"FAN\s*FOOD", "Fan Food", "Dining", "Restaurant"),
    (r"ASTORIA\s*SEAFOOD", "Astoria Seafood", "Dining", "Restaurant"),
    (r"BUND\s*ON\s*BROADWAY", "Bund on Broadway", "Dining", "Restaurant"),
    (r"IL\s*BAMBINO", "Il Bambino", "Dining", "Restaurant"),
    (r"CHIPNYC", "Chip NYC", "Dining", "Dessert"),
    (r"MORE\s*THAN\s*Q", "More Than Q", "Dining", "Restaurant"),
    (r"BAY\s*SHORE\s*BEAN", "Bay Shore Bean", "Dining", "Coffee"),
    (r"DRYLAND\s*CREAMERY", "Dryland Creamery", "Dining", "Dessert"),
    (r"INDAY\b", "Inday", "Dining", "Restaurant"),
    (r"TORIFUKU\s*RAMEN", "Torifuku Ramen", "Dining", "Restaurant"),
    (r"THE\s*MODERN\s*CRUMB", "The Modern Crumb", "Dining", "Bakery"),
    (r"ALOHA\s*POKE", "Aloha Poke", "Dining", "Restaurant"),
    (r"UEP\*\s*HOCAA\s*BUBBLE|HOCAA\s*BUBBLE", "Hocaa Bubble Tea", "Dining", "Cafe"),
    (r"MOGE\s*TEE", "Moge Tee", "Dining", "Cafe"),
    (r"HENLEY'?S\s*VILLAGE\s*TAVERN", "Henley's Village Tavern", "Dining", "Restaurant"),
    (r"DUCK\s*DONUTS", "Duck Donuts", "Dining", "Dessert"),
    (r"BURRITO\s*MARIACHI", "Burrito Mariachi", "Dining", "Restaurant"),
    (r"THE\s*BARONESS", "The Baroness Bar", "Dining", "Restaurant"),
    (r"ANGRY\s*DUMPLING", "Angry Dumpling", "Dining", "Restaurant"),
    (r"NEW\s*IDEAL\s*BARBERSHOP", "New Ideal Barbershop", "Shopping", "Personal Care"),
    (r"SANFORDSRESTAURANT|SANFORDS\s*RESTAURANT", "Sanford's Restaurant", "Dining", "Restaurant"),
    (r"WEYERBACHER\s*BREWERY", "Weyerbacher Brewery", "Dining", "Brewery"),

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
    (r"AMZ\*", "Amazon", "Amazon", "Marketplace"),
    (r"AWS", "AWS", "Amazon", "Cloud Services"),
    (r"Kindle\s*Svcs", "Kindle", "Amazon", "Subscription"),

    # -------------------------------------------------------------------------
    # Mortgage / Housing (must be before Gas to prevent Shellpoint -> Shell)
    # -------------------------------------------------------------------------
    (r"NEWREZ|SHELLPOIN", "Newrez Shellpoint", "Home", "Mortgage"),

    # -------------------------------------------------------------------------
    # Gas / Fuel
    # -------------------------------------------------------------------------
    (r"SHEETZ", "Sheetz", "Gas", "Gas Station"),
    (r"COSTCO\s*GAS|COSTCO\s*FUEL", "Costco Gas", "Gas", "Gas Station"),
    (r"FRED[\s-]*M(EYER)?\s*(FUEL|#\d+\s*00)", "Fred Meyer Fuel", "Gas", "Gas Station"),
    (r"UNION\s*76|76\s*-\s*", "Union 76", "Gas", "Gas Station"),
    (r"ARCO", "Arco", "Gas", "Gas Station"),
    (r"CHEVRON", "Chevron", "Gas", "Gas Station"),
    (r"SHELL\s*(OIL|SERVICE|GAS)\b|(?<![A-Z])SHELL\s*#|\bSHELL\b(?!POIN)", "Shell", "Gas", "Gas Station"),
    (r"EXXON|(?<!T-)MOBIL(?!E)", "ExxonMobil", "Gas", "Gas Station"),
    (r"BP\b|BRITISH\s*PETRO", "BP", "Gas", "Gas Station"),
    (r"WAWA", "Wawa", "Gas", "Gas Station"),
    (r"SPEEDWAY", "Speedway", "Gas", "Gas Station"),
    (r"SUNOCO", "Sunoco", "Gas", "Gas Station"),
    (r"MARATHON\s*(GAS|PETRO)?", "Marathon", "Gas", "Gas Station"),
    (r"7-ELEVEN|7\s*ELEVEN", "7-Eleven", "Gas", "Convenience"),
    (r"AMOCO", "Amoco", "Gas", "Gas Station"),
    (r"APPLEGREEN\s*GAS", "Applegreen", "Gas", "Gas Station"),

    # -------------------------------------------------------------------------
    # Streaming
    # -------------------------------------------------------------------------
    (r"NETFLIX", "Netflix", "Streaming", "Video"),
    (r"SPOTIFY", "Spotify", "Streaming", "Music"),
    (r"DISNEY\s*\+|DISNEYPLUS|DISNEY\s*PLUS", "Disney+", "Streaming", "Video"),
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
    (r"INTUIT\s*\*\s*QBOOKS|QBooks\s*Online", "QuickBooks", "Software", "Finance"),
    (r"INTUIT\s*\*\s*TURBOTAX|TURBOTAX", "TurboTax", "Software", "Finance"),
    (r"DISCORD", "Discord", "Software", "Communication"),
    (r"PATREON", "Patreon", "Software", "Subscription"),
    (r"GITHUB", "GitHub", "Software", "Developer Tools"),
    (r"NOTION", "Notion", "Software", "Productivity"),
    (r"SLACK", "Slack", "Software", "Communication"),
    (r"ZOOM\s*(VIDEO)?", "Zoom", "Software", "Communication"),
    (r"APPLE\.COM/BILL|ITUNES", "Apple Services", "Software", "Subscription"),
    (r"GOOGLE\s*\*", "Google Services", "Software", "Subscription"),
    (r"MICROSOFT\s*\*\s*(SUBSCRIPTION|MICROSOFT\s*365|STORE)", "Microsoft 365", "Software", "Subscription"),
    (r"PLAYSTATION\s*NETWORK|SIE\*\s*PLAYSTATION|PlaystationNetwork", "PlayStation Network", "Entertainment", "Gaming"),
    (r"STEAMGAMES|WL\s*\*\s*Steam", "Steam", "Entertainment", "Gaming"),
    (r"NINTENDO", "Nintendo", "Entertainment", "Gaming"),
    (r"Chess\.com", "Chess.com", "Software", "Subscription"),
    (r"A\s*MEDIUM\s*CORPORATION", "Medium", "Software", "Subscription"),
    (r"CHEGG\s*ORDER", "Chegg", "Software", "Education"),
    (r"SCRIBD", "Scribd", "Software", "Subscription"),
    (r"NOOM\b", "Noom", "Software", "Subscription"),
    (r"KOVOCREDIT|KOVO\s*CREDIT", "Kovo Credit", "Software", "Finance"),
    (r"RING\s*(YEARLY\s*PLAN|BASIC\s*PLAN)", "Ring", "Software", "Subscription"),
    (r"STASH\s*FINANCIAL", "Stash", "Software", "Finance"),
    (r"ROCKET\s*MONEY", "Rocket Money", "Software", "Finance"),
    (r"PLEXINC|PLEX\.TV", "Plex", "Software", "Subscription"),
    (r"NEBULA\b", "Nebula", "Streaming", "Video"),

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
    # Shopping -- specific brands before general
    # -------------------------------------------------------------------------
    (r"GAMESTOP", "GameStop", "Shopping", "Electronics"),
    (r"HOBBY\s*LOBBY", "Hobby Lobby", "Shopping", "Crafts"),
    (r"MICHAELS\s*STORES?", "Michaels", "Shopping", "Crafts"),
    (r"BARNES\s*&?\s*NOBLE", "Barnes & Noble", "Shopping", "Books"),
    (r"FIVE\s*BELOW", "Five Below", "Shopping", "Discount"),
    (r"DICK'?S\s*CLOTHING|DICK'?S\s*SPORT", "Dick's Sporting Goods", "Shopping", "Sporting Goods"),
    (r"NEIMAN\s*MARCUS", "Neiman Marcus", "Shopping", "Department Store"),
    (r"SAKS\s*(O5|OFF\s*5TH|FIFTH)", "Saks Off 5th", "Shopping", "Department Store"),
    (r"AE\s*OUTF|A\s*EAGLE\s*OUTF|AMERICAN\s*EAGLE\s*OUTFITTERS", "American Eagle", "Shopping", "Clothing"),
    (r"UNIQLO", "Uniqlo", "Shopping", "Clothing"),
    (r"ABERCROMBIE", "Abercrombie & Fitch", "Shopping", "Clothing"),
    (r"GAP\s*(OUTLET|US)\b", "Gap", "Shopping", "Clothing"),
    (r"J\s*CREW", "J.Crew", "Shopping", "Clothing"),
    (r"BANANA\s*REPUBLIC|BR\s*FACTORY", "Banana Republic", "Shopping", "Clothing"),
    (r"LUCKYBRAND", "Lucky Brand", "Shopping", "Clothing"),
    (r"TOMMY\s*HILFIGER", "Tommy Hilfiger", "Shopping", "Clothing"),
    (r"EDDIE\s*BAUER", "Eddie Bauer", "Shopping", "Clothing"),
    (r"MODCLOTH", "ModCloth", "Shopping", "Clothing"),
    (r"ALTAR'?D\s*STATE", "Altar'd State", "Shopping", "Clothing"),
    (r"VICTORIA'?S\s*SECRET|VICTORIASSECRET", "Victoria's Secret", "Shopping", "Clothing"),
    (r"KATE\s*SPADE", "Kate Spade", "Shopping", "Clothing"),
    (r"SOMA\s*INTIMATES", "Soma Intimates", "Shopping", "Clothing"),
    (r"COACH\s*OUTLET|&\s*COACH\s*OUTLET", "Coach Outlet", "Shopping", "Clothing"),
    (r"BOX\s*LUNCH", "BoxLunch", "Shopping", "Clothing"),
    (r"EXPRESS\s*#\d+", "Express", "Shopping", "Clothing"),
    (r"HOT\s*TOPIC", "Hot Topic", "Shopping", "Clothing"),
    (r"VANS\.COM", "Vans", "Shopping", "Clothing"),
    (r"HANNA\s*ANDERSSON", "Hanna Andersson", "Shopping", "Clothing"),
    (r"VERA\s*BRADLEY", "Vera Bradley", "Shopping", "Clothing"),
    (r"SEPHORA", "Sephora", "Shopping", "Personal Care"),
    (r"GLOSSIER", "Glossier", "Shopping", "Personal Care"),
    (r"LUSH\s*DIGITAL", "Lush", "Shopping", "Personal Care"),
    (r"DASHING\s*DIVA", "Dashing Diva", "Shopping", "Personal Care"),
    (r"MEUNDIES", "MeUndies", "Shopping", "Clothing"),
    (r"DSW\b", "DSW", "Shopping", "Shoes"),
    (r"CARTER'?S\s*#|CARTERS", "Carter's", "Shopping", "Clothing"),
    (r"THE\s*CHILDREN'?S\s*PLACE", "The Children's Place", "Shopping", "Clothing"),
    (r"BUY\s*BUY\s*BABY", "Buy Buy Baby", "Shopping", "Baby"),
    (r"FRG\*\s*FANATICS|FRG\*\s*SHOP\.NHL", "Fanatics / NHL Shop", "Shopping", "Sports"),
    (r"UNCOMMONGOODS", "UncommonGoods", "Shopping", "Gifts"),
    (r"1-?800-?FLOWERS|FTD\*\s*FTD", "1-800-Flowers / FTD", "Shopping", "Gifts"),
    (r"BOUQS\.COM", "Bouqs", "Shopping", "Gifts"),
    (r"SHUTTERFLY", "Shutterfly", "Shopping", "Photo"),
    (r"SP\s*PRIMARY\.COM|PRIMARY\.COM", "Primary", "Shopping", "Kids Clothing"),
    (r"SP\s*LITTLE\s*SLEEPIES", "Little Sleepies", "Shopping", "Kids Clothing"),
    (r"SP\s*KYTE\s*BABY", "Kyte Baby", "Shopping", "Kids Clothing"),
    (r"SP\s*BRAVE\s*LITTLE\s*ONES|BRAVE\s*LITTL", "Brave Little Ones", "Shopping", "Kids Clothing"),
    (r"SP\s*TEN\s*LITTLE", "Ten Little", "Shopping", "Kids Clothing"),
    (r"SP\s*WOOLINO", "Woolino", "Shopping", "Kids Clothing"),
    (r"SP\s*GOODBUY\s*GEAR", "Goodbuy Gear", "Shopping", "Kids"),
    (r"SP\s*PUPGUM", "Pupgum", "Shopping", "Pets"),
    (r"SP\s*RUGGABLE", "Ruggable", "Home", "Decor"),
    (r"SP\s*THURSDAY\s*BOOT", "Thursday Boot Co.", "Shopping", "Shoes"),
    (r"SP\s*SNAKE\s*RIVER\s*FARMS", "Snake River Farms", "Groceries", "Specialty"),
    (r"SP\s*GORAL\s*SON", "Goral Son Ltd", "Shopping", "Online"),
    (r"SP\s*ROSE\s*ANVIL|ROSE\s*ANVIL", "Rose Anvil", "Shopping", "Shoes"),
    (r"ETSY|Etsy", "Etsy", "Shopping", "Online"),
    (r"EBAY|eBay", "eBay", "Shopping", "Online"),
    (r"PAYPAL\s*\*\s*KALAWANGSAP", "PayPal - Kalawangsap", "Shopping", "Online"),
    (r"GROUPON", "Groupon", "Shopping", "Deals"),
    (r"TARGET", "Target", "Shopping", "Department Store"),
    (r"MARSHALLS", "Marshalls", "Shopping", "Discount"),
    (r"T[\.\s]*J[\.\s]*MAXX|TJMAXX", "TJ Maxx", "Shopping", "Discount"),
    (r"HOMEGOODS", "HomeGoods", "Shopping", "Home"),
    (r"OLD\s*NAVY", "Old Navy", "Shopping", "Clothing"),
    (r"NORDSTROM", "Nordstrom", "Shopping", "Department Store"),
    (r"WAL-?MART|WM\s*SUPERCENTER", "Walmart", "Shopping", "Department Store"),
    (r"APPLE\s*(STORE|ONLINE)", "Apple Store", "Shopping", "Electronics"),
    (r"BEST\s*BUY", "Best Buy", "Shopping", "Electronics"),
    (r"COSTCO(?!\s*(GAS|FUEL|WHSE))", "Costco", "Shopping", "Warehouse"),
    (r"AMAZON(?!\s*(PRIME|VIDEO))", "Amazon", "Shopping", "Online"),
    (r"KOHLS|KOHL'S", "Kohl's", "Shopping", "Department Store"),
    (r"\bMACY", "Macy's", "Shopping", "Department Store"),
    (r"ROSS\s*(DRESS|STORE)?", "Ross", "Shopping", "Discount"),
    (r"DOLLAR\s*(TREE|GENERAL)", "Dollar Store", "Shopping", "Discount"),
    (r"BED\s*BATH", "Bed Bath & Beyond", "Shopping", "Home"),
    (r"BATH\s*AND\s*BODY\s*WORKS|BATH\s*&?\s*BODY\s*WORKS", "Bath & Body Works", "Shopping", "Personal Care"),
    (r"JOANN\s*STORES?|JOANN\.COM", "Joann", "Shopping", "Crafts"),
    (r"STAPLES", "Staples", "Shopping", "Office"),
    (r"DUANE\s*READE", "Duane Reade", "Shopping", "Pharmacy"),
    (r"JAF\s*COMICS|THE\s*PORTAL\s*COMICS|BROTHER'?S\s*GRIM\s*GAMES", "Comics / Game Store", "Entertainment", "Games"),
    (r"PETSMART", "PetSmart", "Shopping", "Pets"),
    (r"PETCO", "Petco", "Shopping", "Pets"),
    (r"PET\s*SUPPLIES\s*PLUS", "Pet Supplies Plus", "Shopping", "Pets"),
    (r"MONTBLANC", "Montblanc", "Shopping", "Luxury"),
    (r"DAVIDS\s*BRIDAL", "David's Bridal", "Shopping", "Clothing"),
    (r"THE\s*KNOT\s*REGISTRY", "The Knot Registry", "Shopping", "Gifts"),
    (r"WORLD\s*MARKET", "World Market", "Shopping", "Home"),
    (r"BROOKSTONE", "Brookstone", "Shopping", "Electronics"),
    (r"SPORT\s*CLIPS", "Sport Clips", "Shopping", "Personal Care"),
    (r"MAGNOLIA\s*NAILS", "Magnolia Nails & Spa", "Shopping", "Personal Care"),
    (r"COLORI\s*BELLA", "Colori Bella Hair Studio", "Shopping", "Personal Care"),
    (r"GENTLEMENS\s*BARBERSHOP|NOBLE\s*SAVAGE\s*BARBER", "Barbershop", "Shopping", "Personal Care"),
    (r"LIDS\.COM", "Lids", "Shopping", "Clothing"),
    (r"ASICS\b", "Asics", "Shopping", "Shoes"),
    (r"TORY\s*BURCH", "Tory Burch", "Shopping", "Clothing"),
    (r"MICHAEL\s*KORS", "Michael Kors", "Shopping", "Clothing"),
    (r"ANN\s*TAYLOR", "Ann Taylor", "Shopping", "Clothing"),
    (r"NASTYGAL", "Nasty Gal", "Shopping", "Clothing"),
    (r"ASOS\.COM", "ASOS", "Shopping", "Clothing"),
    (r"LULUS\.COM", "Lulu's", "Shopping", "Clothing"),

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
    (r"BLINDS\.COM", "Blinds.com", "Home", "Window Treatments"),
    (r"JUST\s*FURNITURE", "Just Furniture", "Home", "Furniture"),
    (r"SHERWIN\s*WILLIAMS", "Sherwin-Williams", "Home", "Paint"),
    (r"SUR\s*LA\s*TABLE", "Sur La Table", "Home", "Kitchen"),
    (r"ROTO-?ROOTER", "Roto-Rooter", "Home", "Plumbing"),
    (r"PODS\b", "PODS", "Home", "Moving"),
    (r"1-?800-?GOT-?JUNK|1800GOTJUNK", "1-800-GOT-JUNK", "Home", "Junk Removal"),
    (r"HIRE\s*A\s*HELPER", "Hire A Helper", "Home", "Moving"),
    (r"PACK\s*&?\s*LOAD\s*SERVICE", "Pack & Load Services", "Home", "Moving"),
    (r"NATURAL\s*LIGHT\s*WINDOW", "Natural Light Window Co.", "Home", "Window Treatments"),
    (r"THE\s*PATCH\s*BOYS", "The Patch Boys", "Home", "Repair"),
    (r"JOHNSON\s*SEAL\s*COAT", "Johnson Sealcoating", "Home", "Repair"),
    (r"RIZZ\s*CONTAINERS", "Rizz Containers", "Home", "Waste"),
    (r"PILLAR\s*TO\s*POST", "Pillar to Post", "Home", "Inspection"),
    (r"SP\s*NUGGETCOMFORT|NUGGETCO", "Nugget Comfort", "Home", "Furniture"),
    (r"SP\s*\*?\s*GREAT\s*JONES", "Great Jones", "Home", "Kitchen"),
    (r"GROVE\s*HTTPS", "Grove Co.", "Home", "Cleaning"),

    # -------------------------------------------------------------------------
    # Healthcare
    # -------------------------------------------------------------------------
    (r"WILLIAM\s*PENN\s*VET", "William Penn Vet", "Healthcare", "Veterinary"),
    (r"A\s*PET\s*CLINIC", "A Pet Clinic", "Healthcare", "Veterinary"),
    (r"COURT\s*SQUARE\s*ANIMAL", "Court Square Animal Hospital", "Healthcare", "Veterinary"),
    (r"WEST\s*HILLS\s*(E\s*)?VET|WEST\s*HILLS\s*ANIMAL", "West Hills Veterinary", "Healthcare", "Veterinary"),
    (r"SHAKE\s*A\s*PAW", "Shake A Paw", "Shopping", "Pets"),
    (r"ST\.?\s*LUKE", "St. Luke's", "Healthcare", "Hospital"),
    (r"SWEDISH\s*MEDICAL", "Swedish Medical", "Healthcare", "Hospital"),
    (r"CVS", "CVS", "Healthcare", "Pharmacy"),
    (r"WALGREENS", "Walgreens", "Healthcare", "Pharmacy"),
    (r"RITE\s*AID", "Rite Aid", "Healthcare", "Pharmacy"),
    (r"KAISER", "Kaiser Permanente", "Healthcare", "Hospital"),
    (r"BH\*\s*BETTERHELP|BETTERHELP", "BetterHelp", "Healthcare", "Mental Health"),
    (r"LIC\s*DENTAL|FAMILY\s*DENTAL|MAPLE\s*TREE\s*DENTAL", "Dental Office", "Healthcare", "Dental"),
    (r"OPTIMEYES\s*VISION|DAVID\s*S\s*ALTENDERFER\s*OD", "Eye Doctor", "Healthcare", "Vision"),
    (r"LABCORP", "LabCorp", "Healthcare", "Lab"),
    (r"HAND\s*AND\s*STONE\s*MASSAGE", "Hand & Stone Massage", "Healthcare", "Wellness"),
    (r"CLR\*\s*PUREBARRE|PUREBARRE", "Pure Barre", "Healthcare", "Fitness"),
    (r"INNER\s*STRENGTH\s*FITNESS", "Inner Strength Fitness", "Healthcare", "Fitness"),
    (r"GRAVITY\s*VAULT", "Gravity Vault", "Healthcare", "Fitness"),
    (r"EWC\s*EASTON|EASTON-?\s*0485", "European Wax Center", "Shopping", "Personal Care"),
    (r"IN\s*\*\s*SMOOTHE\s*WAX", "Smoothe Wax Studio", "Shopping", "Personal Care"),
    (r"SUFFOLK\s*ORAL\s*SURGERY", "Suffolk Oral Surgery", "Healthcare", "Dental"),
    (r"PHR\*\s*URGENTCARE|NORTH\s*SHORE.*URGENT", "Urgent Care", "Healthcare", "Urgent Care"),

    # -------------------------------------------------------------------------
    # Travel -- rides/car rental (specific before general)
    # -------------------------------------------------------------------------
    (r"AMERICAN\s*AIR|AMERICAN\s*AI\b", "American Airlines", "Travel", "Flights"),
    (r"UNITED\s*(AIR|\d{10,})", "United Airlines", "Travel", "Flights"),
    (r"UA\s*INFLT", "United Airlines In-Flight", "Travel", "Flights"),
    (r"AA\s*WIFI", "American Airlines Wi-Fi", "Travel", "Flights"),
    (r"SPIRIT\s*AIR", "Spirit Airlines", "Travel", "Flights"),
    (r"DELTA\s*AIR", "Delta Air Lines", "Travel", "Flights"),
    (r"SOUTHWEST\s*AIR", "Southwest Airlines", "Travel", "Flights"),
    (r"JETBLUE", "JetBlue", "Travel", "Flights"),
    (r"ALASKA\s*AIR", "Alaska Airlines", "Travel", "Flights"),
    (r"FRONTIER\s*AIR", "Frontier Airlines", "Travel", "Flights"),
    (r"TRIP\.COM", "Trip.com", "Travel", "Booking"),
    (r"AIRBNB", "Airbnb", "Travel", "Lodging"),
    (r"HILTON", "Hilton", "Travel", "Lodging"),
    (r"MARRIOTT", "Marriott", "Travel", "Lodging"),
    (r"HYATT", "Hyatt", "Travel", "Lodging"),
    (r"HOLIDAY\s*INN", "Holiday Inn", "Travel", "Lodging"),
    (r"HAMPTON\s*INN", "Hampton Inn", "Travel", "Lodging"),
    (r"COMFORT\s*SUITES", "Comfort Suites", "Travel", "Lodging"),
    (r"W\s*HOTELS", "W Hotels", "Travel", "Lodging"),
    (r"FAIRMONT", "Fairmont", "Travel", "Lodging"),
    (r"FITZPATRICK\s*GRAND", "Fitzpatrick Grand Central", "Travel", "Lodging"),
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
    (r"E-?Z\*?\s*PASS", "E-ZPass", "Travel", "Tolls"),
    (r"WSDOT.*GOODTOGO|GOOD\s*TO\s*GO", "Good To Go", "Travel", "Tolls"),
    (r"MTA\*\s*METROCARD|MTA\*\s*METROCARD/PATH", "MTA MetroCard", "Travel", "Transit"),
    (r"QUEENS\s*WEST\s*PARKING", "Queens West Parking", "Travel", "Parking"),
    (r"LINCOLN\s*HARBOR\s*GARAGE", "Lincoln Harbor Garage", "Travel", "Parking"),
    (r"EASTON\s*PA\s*PARKING", "Easton Parking", "Travel", "Parking"),
    (r"ALLIANZ\s*(TRAVEL|EVENT)\s*INS", "Allianz Travel Insurance", "Travel", "Insurance"),
    (r"TRAVEL\s*GUARD", "Travel Guard", "Travel", "Insurance"),

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
    (r"LIBERTY\s*MUTUAL", "Liberty Mutual", "Insurance", "Auto"),
    (r"MSI\s*INSURANCE", "MSI Insurance", "Insurance", "General"),

    # -------------------------------------------------------------------------
    # Utilities
    # -------------------------------------------------------------------------
    (r"FIRSTENERGY|FIRST\s*ENERGY", "FirstEnergy", "Utilities", "Electric"),
    (r"PUGET\s*SOUND\s*ENERGY|PSE\b", "Puget Sound Energy", "Utilities", "Electric"),
    (r"UGI\b", "UGI", "Utilities", "Gas"),
    (r"SOOS\s*CREEK", "Soos Creek", "Utilities", "Water"),
    (r"REPUBLIC\s*SERVICES", "Republic Services", "Utilities", "Waste"),
    (r"EASTON\s*SUBURBAN\s*WATER", "Easton Suburban Water", "Utilities", "Water"),
    (r"CITY\s*OF\s*COVINGTON\s*PANDR", "City of Covington", "Utilities", "Water"),
    (r"GOODLEAP", "GoodLeap", "Utilities", "Solar"),

    # -------------------------------------------------------------------------
    # Alcohol
    # -------------------------------------------------------------------------
    (r"PA\s*WINE\s*&?\s*SPIRITS|FINE\s*WINE\s*&?\s*GOOD\s*SPIRITS", "PA Wine & Spirits", "Alcohol", "Liquor Store"),
    (r"WINE\s*AND\s*SPIRITS|WINE/SPIRITS\s*SHOPPE", "PA Wine & Spirits", "Alcohol", "Liquor Store"),
    (r"EASTON\s*WINE\s*PROJECT", "Easton Wine Project", "Alcohol", "Wine Bar"),
    (r"TOTAL\s*WINE", "Total Wine", "Alcohol", "Liquor Store"),
    (r"36TH\s*AVE\s*WINE", "36th Ave Wine & Spirits", "Alcohol", "Liquor Store"),
    (r"BOURBON\s*ST(REET)?\s*(WINE|MEMORIAL)", "Bourbon Street Wine", "Alcohol", "Liquor Store"),
    (r"BLUE\s*STREAK\s*WINES", "Blue Streak Wines", "Alcohol", "Liquor Store"),
    (r"TERRACE\s*LIQUOR", "Terrace Liquor Depot", "Alcohol", "Liquor Store"),
    (r"ANGELA'?S\s*WINE", "Angela's Wine & Spirit", "Alcohol", "Liquor Store"),
    (r"HOLBROOK\s*LIQUORS", "Holbrook Liquors", "Alcohol", "Liquor Store"),
    (r"VERNON\s*WINE", "Vernon Wine & Liquor", "Alcohol", "Liquor Store"),
    (r"L\s*&?\s*C\s*LIQUOR", "L & C Liquor", "Alcohol", "Liquor Store"),
    (r"LAKE\s*BUY\s*-?\s*RITE\s*LIQUOR", "Lake Buy-Rite Liquor", "Alcohol", "Liquor Store"),
    (r"GARDEN\s*CITY\s*WINE\s*CELLAR", "Garden City Wine Cellar", "Alcohol", "Liquor Store"),
    (r"S\s*&?\s*A\s*WINES", "S & A Wines", "Alcohol", "Liquor Store"),
    (r"KH\s*&?\s*H\s*LIQUORS", "KH & H Liquors", "Alcohol", "Liquor Store"),
    (r"BEEKMAN\s*WINE", "Beekman Wine Liquor", "Alcohol", "Liquor Store"),
    (r"MANHATTAN\s*WINE", "Manhattan Wine Company", "Alcohol", "Liquor Store"),
    (r"SPIRITS\s*UNLIMITED", "Spirits Unlimited", "Alcohol", "Liquor Store"),
    (r"CHICONES\s*LIQUOR", "Chicone's Liquor", "Alcohol", "Liquor Store"),
    (r"NEW\s*ENGLAND\s*COFFEE.*WEB", "New England Coffee", "Groceries", "Coffee"),
    (r"SP\s*STATESIDE\s*VODKA", "Stateside Vodka", "Alcohol", "Liquor Store"),
    (r"BLUE\s*RIDGE\s*ESTATE\s*VINEYARD", "Blue Ridge Estate Vineyard", "Alcohol", "Wine Bar"),

    # -------------------------------------------------------------------------
    # Entertainment
    # -------------------------------------------------------------------------
    (r"MAGICCON", "MagicCon", "Entertainment", "Convention"),
    (r"AMC\s*(THEATRE|MOVIE|4401|\d{4}\s)", "AMC Theatres", "Entertainment", "Movies"),
    (r"REGAL\s*(CINEMA|THEATRE|KAUFMAN|DEER\s*PARK)", "Regal Cinemas", "Entertainment", "Movies"),
    (r"MOVIETAVERN", "Movie Tavern", "Entertainment", "Movies"),
    (r"KAUFMAN\s*ASTORIA", "Kaufman Astoria", "Entertainment", "Movies"),
    (r"NORTHAMPTON\s*CINEMA", "Northampton Cinema", "Entertainment", "Movies"),
    (r"FANDANGO", "Fandango", "Entertainment", "Movies"),
    (r"TICKETMASTER", "Ticketmaster", "Entertainment", "Events"),
    (r"STUBHUB", "StubHub", "Entertainment", "Events"),
    (r"TCGPLAYER", "TCGplayer", "Entertainment", "Games"),
    (r"CARDKINGDOM", "Card Kingdom", "Entertainment", "Games"),
    (r"BRILLIANTM\*\s*WIZARDS", "Wizards of the Coast", "Entertainment", "Games"),
    (r"TOLARIAN\s*COMMUNITY", "Tolarian Community College", "Entertainment", "Games"),
    (r"ARTSQUEST", "ArtsQuest", "Entertainment", "Events"),
    (r"LEHIGH\s*VALLEY\s*IRON\s*PIGS", "Lehigh Valley IronPigs", "Entertainment", "Events"),
    (r"MSG\s*CONCESSIONS", "MSG Concessions", "Entertainment", "Events"),
    (r"FEVER\s*USA", "Fever", "Entertainment", "Events"),
    (r"SEATTLE\s*AQUARIUM|AT\s*\*\s*SEATTLEAQUARIUM", "Seattle Aquarium", "Entertainment", "Attraction"),
    (r"POINT\s*DEFIANCE\s*ZOO", "Point Defiance Zoo", "Entertainment", "Attraction"),
    (r"MUSEUM\s*OF\s*FLIGHT|MUSEUM\s*MOVINGIMAGE", "Museum", "Entertainment", "Attraction"),
    (r"LEHIGH\s*VALLEY\s*ZOO|FH\*\s*LEHIGH\s*VALLEY\s*ZOO", "Lehigh Valley Zoo", "Entertainment", "Attraction"),
    (r"LOST\s*RIVER\s*CAVERNS", "Lost River Caverns", "Entertainment", "Attraction"),
    (r"HISTORIC\s*BETHLEHEM\s*MUSEU", "Historic Bethlehem Museum", "Entertainment", "Attraction"),
    (r"KEMERER\s*MUSEUM", "Kemerer Museum", "Entertainment", "Attraction"),
    (r"SCHIMANSKI", "Schimanski", "Entertainment", "Nightlife"),
    (r"NY\s*COMEDY", "NY Comedy", "Entertainment", "Events"),
    (r"GOVERNORS\s*COMEDY", "Governor's Comedy", "Entertainment", "Events"),
    (r"VISION\s*ENTERTAINMENT", "Vision Entertainment", "Entertainment", "Events"),
    (r"PP\*\s*VRCAFE", "VR Cafe", "Entertainment", "Games"),
    (r"FSP\*\s*SCRATCH\s*EASTON|SCRATCH\s*610", "Scratch", "Entertainment", "Games"),

    # -------------------------------------------------------------------------
    # Shipping
    # -------------------------------------------------------------------------
    (r"PIRATE\s*SHIP", "Pirate Ship", "Shipping", "Postage"),
    (r"USPS", "USPS", "Shipping", "Postage"),
    (r"UPS\b", "UPS", "Shipping", "Postage"),
    (r"FEDEX", "FedEx", "Shipping", "Postage"),

    # -------------------------------------------------------------------------
    # Government / Auto / Misc Services
    # -------------------------------------------------------------------------
    (r"PA\s*DRIVER\s*&?\s*VEHICLE|CP\s*PENNDOT", "PennDOT", "Shopping", "Government"),
    (r"NEW\s*YORK\s*STATE\s*DMV", "NY DMV", "Shopping", "Government"),
    (r"WA\s*DOL\s*LIC", "WA DOL", "Shopping", "Government"),
    (r"ONLINE\s*PASSPORT\s*FEES", "Passport Fees", "Shopping", "Government"),
    (r"CITY\s*CLERK", "City Clerk", "Shopping", "Government"),
    (r"PRINTSCAN", "PrintScan", "Shopping", "Government"),
    (r"MAVIS\s*\d+", "Mavis Tires", "Shopping", "Auto"),
    (r"SHAMMY\s*SHINE|Shammy\s*Shine", "Shammy Shine", "Shopping", "Auto"),
    (r"GREAT\s*CLIPS", "Great Clips", "Shopping", "Personal Care"),
    (r"PP\*\s*HAUS\s*OF\s*WAX", "Haus of Wax", "Shopping", "Personal Care"),
    (r"PRECISION\s*LASER", "Precision Laser", "Shopping", "Personal Care"),
    (r"TORILOPEZPHOTOGRAPHY", "Tori Lopez Photography", "Shopping", "Photography"),
    (r"PMUSA\s*\d+", "PMUSA", "Shopping", "Tobacco"),
    (r"UNIDINE\s*CAFE", "Unidine Cafe", "Dining", "Cafeteria"),

    # -------------------------------------------------------------------------
    # Car payments / finance (appearing in checking)
    # -------------------------------------------------------------------------
    (r"MAZDA\s*FINANCIAL", "Mazda Financial", "Shopping", "Auto"),
    (r"KMF\s*KMFUSA", "Kia Motors Finance", "Shopping", "Auto"),
    (r"CALIBER\s*HOME\s*LOA", "Caliber Home Loans", "Home", "Mortgage"),
    (r"LORI\s*GILL\s*&?\s*ASSO", "Lori Gill & Associates", "Home", "Property Mgmt"),
    (r"PA\s*TAP\s*529", "PA 529 Plan", "Shopping", "Savings"),
    (r"ELLEN\s*M\s*STOCKER", "Ellen M Stocker", "Home", "Misc"),
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
