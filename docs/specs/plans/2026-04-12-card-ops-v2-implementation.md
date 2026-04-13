# Card-Ops v2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Restructure card-ops into a three-layer architecture (ingest, analysis, strategy) so that normal mode invocations produce deep, data-driven analysis without requiring agent carpet-bombing.

**Architecture:** Python analysis modules in `lib/` read from a parquet transaction database and produce structured outputs. Mode files (`modes/*.md`) become orchestration instructions that tell Claude which modules to call and in what order. Config splits into per-applicant profiles + household file.

**Tech Stack:** Python (pandas, pdfplumber, pyyaml, pyarrow), parquet for persistence, YAML for config/cache.

**Spec:** `external/card-ops/docs/specs/2026-04-12-card-ops-v2-design.md`

**Project root:** `external/card-ops/` (all paths relative to this)

---

## Task 1: Directory Scaffolding + Config Migration

**Files:**
- Create: `lib/__init__.py`
- Create: `data/transactions/.gitkeep`
- Create: `data/market/.gitkeep`
- Create: `data/analysis/.gitkeep`
- Create: `config/profile-chris.yml`
- Create: `config/profile-dana.yml`
- Create: `config/household.yml`
- Read: `config/profile.yml` (source data for migration)

- [ ] **Step 1: Create directory structure**

```bash
mkdir -p lib data/transactions data/market data/analysis
touch lib/__init__.py data/transactions/.gitkeep data/market/.gitkeep data/analysis/.gitkeep
```

- [ ] **Step 2: Write profile-chris.yml**

Migrate Chris's data from `config/profile.yml`. Cards held by Chris: Amazon Prime Visa, WF Active Cash, Amex BCP.

```yaml
identity:
  name: "Chris Pachulski"
  role: "primary"

credit:
  score: 778
  score_bureau: "Experian"
  score_date: "2026-04-12"
  annual_income: 137500
  bonus_pct: 20

cards:
  - issuer: "Chase"
    card: "Amazon Prime Visa Signature"
    opened: "2017-01"
    credit_limit: 12800
    annual_fee: 0
    earn_rates:
      amazon: 0.05
      dining: 0.02
      gas: 0.02
      other: 0.01
  - issuer: "Wells Fargo"
    card: "Active Cash"
    opened: "2024-10"
    credit_limit: 16000
    annual_fee: 0
    earn_rates:
      everything: 0.02
  - issuer: "American Express"
    card: "Blue Cash Preferred"
    opened: "2022-12"
    credit_limit: null
    annual_fee: 95
    earn_rates:
      groceries: 0.06
      groceries_cap: 6000
      groceries_after_cap: 0.01
      gas: 0.03
      streaming: 0.03
      other: 0.01

applications:
  history: []
  five_24_count: 0
  inquiries_6mo:
    experian: 0
    transunion: 0
    equifax: 0

issuer_status:
  chase:
    sapphire_ever: false
    ink_ever: false
  amex:
    lifetime_bonuses: ["Blue Cash Preferred"]
    credit_card_count: 1
  citi:
    cards_ever: []
  capital_one:
    cards_held: 0
  wells_fargo:
    cards_held: 1
  us_bank:
    relationship: false
```

- [ ] **Step 3: Write profile-dana.yml**

Dana holds the Chase Freedom Unlimited.

```yaml
identity:
  name: "Dana Pachulski"
  role: "secondary"

credit:
  score: null
  score_bureau: null
  score_date: null
  annual_income: 120000
  bonus_pct: 2

cards:
  - issuer: "Chase"
    card: "Freedom Unlimited"
    opened: "2019-01"
    credit_limit: 9500
    annual_fee: 0
    earn_rates:
      dining: 0.03
      drugstore: 0.03
      chase_travel: 0.05
      other: 0.015

applications:
  history: []
  five_24_count: 0
  inquiries_6mo:
    experian: 0
    transunion: 0
    equifax: 0

issuer_status:
  chase:
    sapphire_ever: false
    ink_ever: false
  amex:
    lifetime_bonuses: []
    credit_card_count: 0
  citi:
    cards_ever: []
  capital_one:
    cards_held: 0
```

- [ ] **Step 4: Write household.yml**

```yaml
location:
  current: "Covington, WA"
  state: "WA"
  moved_from: "Palmer Township, PA"
  move_date: "2026-01-01"

income:
  household_gross: 257500

memberships:
  - "Costco (warehouse, no Citi card)"
  - "Amazon Prime"
  - "Audible"
  - "DashPass"

side_business:
  exists: true
  type: "sole_proprietorship"
  description: "MTG card sales via TCGPlayer"
  qualifies_for_business_cards: true

strategy:
  primary_goal: "cash_back"
  anti_goals: ["travel_points"]

wallet_routing:
  groceries_primary: "amex-bcp"
  groceries_overflow: "wf-active-cash"
  dining: "chase-freedom"
  doordash: "chase-freedom"
  amazon: "chase-amazon"
  gas: "amex-bcp"
  streaming: "amex-bcp"
  costco: "wf-active-cash"
  everything_else: "wf-active-cash"

life_events:
  - date: "2026-01-01"
    type: "relocation"
    detail: "PA to WA"
    impact: "grocery stores changed, no state income tax, new utility providers"
  - date: "2026-01-01"
    type: "new_expense"
    detail: "KinderCare daycare $1,450/mo"
  - date: "2026-01-01"
    type: "asset_event"
    detail: "PA home sold, $127,890 net proceeds"

analysis:
  last_full_analysis: null
  last_parse: null
  pending_flags: []
```

- [ ] **Step 5: Commit**

```bash
git add lib/ data/transactions/ data/market/ data/analysis/ config/profile-chris.yml config/profile-dana.yml config/household.yml
git commit -m "feat(card-ops): scaffold v2 directory structure + migrate config to dual-profile + household"
```

---

## Task 2: Merchant Normalization Module

**Files:**
- Create: `lib/normalize.py`
- Create: `lib/tests/test_normalize.py`

- [ ] **Step 1: Write test for normalize**

```python
###############################################################################
# lib/tests/test_normalize.py
###############################################################################
import pytest
from lib.normalize import normalize_merchant


@pytest.mark.parametrize("raw,expected_name,expected_cat,expected_sub", [
    ("WEGMANS NAZARETH #94EASTON PA", "Wegmans", "Groceries", "Supermarket"),
    ("DD *DOORDASH CASCADIAP 855-431-0459 CA", "DoorDash", "Delivery", "Food Delivery"),
    ("APPLE.COM/BILL 866-712-7753 CA", "Apple.com/Bill", "Software", "Subscription"),
    ("SHEETZ 03680800 EASTON PA", "Sheetz", "Gas", "Gas Station"),
    ("NETFLIX.COM 866-579-7172 CA", "Netflix", "Streaming", "Video"),
    ("DIGITALOCEAN.COM DIGITALOCEAN. NY", "DigitalOcean", "Software", "Cloud Hosting"),
    ("TST* DRIP -THE FLAVOR LAB484-851-3700 PA", "Drip - The Flavor Lab", "Dining", "Coffee"),
    ("COSTCO WHSE #1024 COVINGTON WA", "Costco", "Groceries", "Warehouse"),
    ("TRADER JOE'S #571 KENT WA", "Trader Joes", "Groceries", "Supermarket"),
    ("AMERICAN AIRLINE 0012140025186 800-4337300 TX", "American Airlines", "Travel", "Airline"),
    ("KINDERCARE LC #301954 COVINGTON WA", "KinderCare", "Childcare", "Daycare"),
    ("TOTALLY UNKNOWN MERCHANT XYZ", "TOTALLY UNKNOWN MERCHANT XYZ", "Other", "Uncategorized"),
])
def test_normalize_merchant(raw, expected_name, expected_cat, expected_sub):
    name, cat, sub = normalize_merchant(raw)
    assert name == expected_name
    assert cat == expected_cat
    assert sub == expected_sub


def test_normalize_returns_tuple_of_three_strings():
    result = normalize_merchant("ANYTHING")
    assert isinstance(result, tuple)
    assert len(result) == 3
    assert all(isinstance(s, str) for s in result)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd external/card-ops && python -m pytest lib/tests/test_normalize.py -v`
Expected: FAIL (module does not exist)

- [ ] **Step 3: Write normalize.py**

```python
###############################################################################
# lib/normalize.py -- Merchant normalization + categorization
###############################################################################
import re
from typing import TypedDict


class MerchantInfo(TypedDict):
    name: str
    category: str
    subcategory: str


# (pattern, clean_name, category, subcategory)
# Order matters -- first match wins. More specific patterns before general ones.
MERCHANT_MAP: list[tuple[str, str, str, str]] = [
    # Delivery
    (r"DD \*DOORDASH", "DoorDash", "Delivery", "Food Delivery"),
    (r"UBER\s*EATS", "Uber Eats", "Delivery", "Food Delivery"),
    (r"GRUBHUB", "Grubhub", "Delivery", "Food Delivery"),

    # Amazon ecosystem
    (r"AMAZON MKTPL|Amazon\.com|AMZN MKTP|AMAZON\.COM", "Amazon", "Amazon", "Marketplace"),
    (r"AMAZON PRIME", "Amazon Prime", "Amazon", "Subscription"),
    (r"AUDIBLE", "Audible", "Amazon", "Subscription"),
    (r"Amazon Web Services|AWS", "AWS", "Software", "Cloud Hosting"),
    (r"WHOLE FOODS", "Whole Foods", "Groceries", "Supermarket"),

    # Groceries
    (r"WEGMANS", "Wegmans", "Groceries", "Supermarket"),
    (r"TRADER JOE", "Trader Joes", "Groceries", "Supermarket"),
    (r"FRED-?MEYER(?!.*FUEL)", "Fred Meyer", "Groceries", "Supermarket"),
    (r"FRED M(?:EYER)? FUEL|FRED-MEYER.*FUEL", "Fred Meyer Fuel", "Gas", "Gas Station"),
    (r"COSTCO WHSE|COSTCO\.COM|WWW COSTCO COM", "Costco", "Groceries", "Warehouse"),
    (r"QFC\b", "QFC", "Groceries", "Supermarket"),
    (r"ACME\b", "Acme", "Groceries", "Supermarket"),
    (r"GROCERY OUTLET", "Grocery Outlet", "Groceries", "Supermarket"),
    (r"S\.E\.A\.\s*MART", "SEA Mart", "Groceries", "Supermarket"),

    # Gas
    (r"SHEETZ", "Sheetz", "Gas", "Gas Station"),
    (r"COSTCO GAS|COSTCO FUEL", "Costco Gas", "Gas", "Gas Station"),
    (r"UNION 76|76\s+#", "Union 76", "Gas", "Gas Station"),
    (r"ARCO\b", "Arco", "Gas", "Gas Station"),
    (r"CHEVRON\b", "Chevron", "Gas", "Gas Station"),
    (r"SHELL\b", "Shell", "Gas", "Gas Station"),

    # Streaming
    (r"NETFLIX", "Netflix", "Streaming", "Video"),
    (r"SPOTIFY", "Spotify", "Streaming", "Music"),
    (r"DISNEY PLUS|DISNEY\+", "Disney+", "Streaming", "Video"),
    (r"HLU\*HULU|HULU", "Hulu", "Streaming", "Video"),
    (r"GOOGLE \*YOUTUBE\s*PREMI", "YouTube Premium", "Streaming", "Video"),
    (r"APPLE\.COM/BILL", "Apple.com/Bill", "Software", "Subscription"),
    (r"APPLE ONLINE STORE|APPLE STORE", "Apple Store", "Shopping", "Electronics"),

    # Software / SaaS
    (r"DIGITALOCEAN", "DigitalOcean", "Software", "Cloud Hosting"),
    (r"OPENAI|CHATGPT", "OpenAI", "Software", "AI"),
    (r"ANTHROPIC", "Anthropic", "Software", "AI"),
    (r"CURSOR\b", "Cursor", "Software", "AI"),
    (r"DOCKER", "Docker", "Software", "DevTools"),
    (r"ADOBE", "Adobe", "Software", "Creative"),
    (r"COURSERA", "Coursera", "Software", "Education"),
    (r"GOOGLE \*CLOUD", "Google Cloud", "Software", "Cloud Hosting"),
    (r"INTUIT.*QBOOKS|QUICKBOOKS", "QuickBooks", "Software", "Business"),
    (r"DISCORD", "Discord", "Software", "Subscription"),
    (r"PATREON", "Patreon", "Software", "Subscription"),

    # Telecom
    (r"DIRECTV|SPI DIRECTV", "DirecTV Stream", "Telecom", "TV"),
    (r"COMCAST|XFINITY", "Comcast/Xfinity", "Telecom", "Internet"),
    (r"ASTOUND|RCN\b", "Astound/RCN", "Telecom", "Internet"),
    (r"T-MOBILE|TMOBILE", "T-Mobile", "Telecom", "Phone"),

    # Travel
    (r"AMERICAN AIRLINE|AA\b.*AIRLINE", "American Airlines", "Travel", "Airline"),
    (r"UNITED AIRLINE", "United Airlines", "Travel", "Airline"),
    (r"SPIRIT AIRL", "Spirit Airlines", "Travel", "Airline"),
    (r"AIRBNB", "Airbnb", "Travel", "Lodging"),
    (r"HILTON|HAMPTON INN|GARDEN INN", "Hilton", "Travel", "Lodging"),
    (r"MARRIOTT|COURTYARD|SHERATON|WESTIN", "Marriott", "Travel", "Lodging"),
    (r"HYATT", "Hyatt", "Travel", "Lodging"),
    (r"HOLIDAY INN|IHG\b", "Holiday Inn", "Travel", "Lodging"),
    (r"AVIS RENT", "Avis", "Travel", "Car Rental"),
    (r"BUDGET RENT|BUDGET CAR", "Budget", "Travel", "Car Rental"),
    (r"SIXT\b", "Sixt", "Travel", "Car Rental"),
    (r"ENTERPRISE RENT", "Enterprise", "Travel", "Car Rental"),
    (r"EXPEDIA\b", "Expedia", "Travel", "Booking"),
    (r"CL \*CHASE TRAVEL|TRIPCHRG\.COM", "Chase Travel", "Travel", "Booking"),
    (r"UBER\s+TRIP|UBER\b(?!.*EATS)", "Uber", "Travel", "Rideshare"),
    (r"LYFT\b", "Lyft", "Travel", "Rideshare"),

    # Shopping / Retail
    (r"TARGET\b", "Target", "Shopping", "Department"),
    (r"MARSHALLS", "Marshalls", "Shopping", "Clothing"),
    (r"TJMAXX|TJ\s*MAXX", "TJ Maxx", "Shopping", "Clothing"),
    (r"HOMEGOODS", "HomeGoods", "Shopping", "Home"),
    (r"OLDNAVY|OLD NAVY", "Old Navy", "Shopping", "Clothing"),
    (r"NORDSTROM", "Nordstrom", "Shopping", "Clothing"),
    (r"WALMART\b", "Walmart", "Shopping", "Department"),

    # Home
    (r"HOME\s*DEPOT|HOMEDEPOT", "Home Depot", "Home", "Hardware"),
    (r"IKEA\b", "IKEA", "Home", "Furniture"),
    (r"LA-Z-BOY|LAZBOY", "La-Z-Boy", "Home", "Furniture"),
    (r"POTTERY BARN", "Pottery Barn", "Home", "Furniture"),
    (r"LOWES\b|LOWE'S", "Lowes", "Home", "Hardware"),

    # Healthcare
    (r"WILLIAM PENN VET|WM PENN VET", "William Penn Vet", "Healthcare", "Veterinary"),
    (r"A PET CLINIC", "A Pet Clinic of Kent", "Healthcare", "Veterinary"),
    (r"ST\.?\s*LUKE", "St. Lukes", "Healthcare", "Medical"),
    (r"SWEDISH MEDICAL", "Swedish Medical", "Healthcare", "Medical"),
    (r"CVS\b", "CVS", "Healthcare", "Pharmacy"),
    (r"WALGREENS", "Walgreens", "Healthcare", "Pharmacy"),

    # Childcare
    (r"KINDERCARE", "KinderCare", "Childcare", "Daycare"),

    # Insurance
    (r"PROGRESSIVE\b", "Progressive", "Insurance", "Auto"),

    # Utilities
    (r"FIRSTENERGY|PPL ELECTRIC", "FirstEnergy", "Utilities", "Electric"),
    (r"PUGET SOUND ENERGY|PSE\b", "Puget Sound Energy", "Utilities", "Electric/Gas"),
    (r"UGI\b", "UGI", "Utilities", "Gas"),
    (r"SOOS CREEK", "Soos Creek Water", "Utilities", "Water/Sewer"),
    (r"REPUBLIC SERVICES", "Republic Services", "Utilities", "Trash"),

    # Alcohol (standalone stores, NOT grocery-bundled)
    (r"WINE AND SPIRITS|WINE & SPIRITS|WINE/SPIRITS", "PA Wine & Spirits", "Alcohol", "Liquor Store"),
    (r"EASTON WINE PROJECT|EWC EASTON", "Easton Wine Project", "Alcohol", "Wine Bar"),

    # Entertainment
    (r"MAGICCON", "MagicCon", "Entertainment", "Convention"),

    # Shipping
    (r"PIRATE SHIP", "Pirate Ship", "Shipping", "Labels"),
    (r"USPS\b", "USPS", "Shipping", "Postal"),
    (r"UPS STORE|UPS\b", "UPS", "Shipping", "Courier"),

    # Dining (broad patterns last -- these catch restaurants not matched above)
    (r"TST\*\s*DRIP.*FLAVOR\s*LAB", "Drip - The Flavor Lab", "Dining", "Coffee"),
    (r"STARBUCKS", "Starbucks", "Dining", "Coffee"),
    (r"DUNKIN", "Dunkin", "Dining", "Coffee"),
    (r"COLD\s*STONE", "Cold Stone", "Dining", "Dessert"),
    (r"CHICK-FIL-A", "Chick-fil-A", "Dining", "Fast Food"),
    (r"MCDONALD", "McDonalds", "Dining", "Fast Food"),
    (r"PAPA JOHN", "Papa Johns", "Dining", "Fast Food"),
    (r"FIVE GUYS", "Five Guys", "Dining", "Fast Food"),
    (r"JERSEY MIKE", "Jersey Mikes", "Dining", "Fast Food"),
    (r"BUFFALO WILD", "Buffalo Wild Wings", "Dining", "Restaurant"),
    (r"LONGHORN\b", "Longhorn Steakhouse", "Dining", "Restaurant"),
]

# Compile patterns once at import time
_COMPILED_MAP: list[tuple[re.Pattern, str, str, str]] = [
    (re.compile(pattern, re.IGNORECASE), name, cat, sub)
    for pattern, name, cat, sub in MERCHANT_MAP
]


def normalize_merchant(raw: str) -> tuple[str, str, str]:
    """Normalize a raw merchant string to (clean_name, category, subcategory).

    Returns the first matching pattern. If no pattern matches, returns
    (raw_string, "Other", "Uncategorized").
    """
    raw_stripped = raw.strip()
    for compiled, name, cat, sub in _COMPILED_MAP:
        if compiled.search(raw_stripped):
            return (name, cat, sub)
    return (raw_stripped, "Other", "Uncategorized")


def get_uncategorized(merchants: list[str]) -> list[str]:
    """Return merchant strings that don't match any pattern."""
    return [m for m in merchants if normalize_merchant(m)[1] == "Other"]
```

- [ ] **Step 4: Run tests**

Run: `cd external/card-ops && python -m pytest lib/tests/test_normalize.py -v`
Expected: All PASS

- [ ] **Step 5: Commit**

```bash
git add lib/normalize.py lib/tests/test_normalize.py
git commit -m "feat(card-ops): add merchant normalization module with 100+ patterns"
```

---

## Task 3: Statement Parsers (parse.py)

**Files:**
- Create: `lib/parse.py`
- Create: `lib/tests/test_parse.py`

This is the largest single module. It contains issuer-specific parsers for Amex Excel, Chase PDF, and Wells Fargo PDF formats, plus the orchestration function that detects new statements and appends to parquets.

- [ ] **Step 1: Write parse.py**

```python
###############################################################################
# lib/parse.py -- Statement parsing (PDF + Excel) -> parquet
###############################################################################
import re
from pathlib import Path

import pandas as pd
import pdfplumber

from lib.normalize import normalize_merchant


CARD_OPS_ROOT = Path(__file__).parent.parent
STATEMENTS_DIR = CARD_OPS_ROOT / "statements"
TRANSACTIONS_DIR = CARD_OPS_ROOT / "data" / "transactions"

TRANSACTION_SCHEMA = {
    "date": "datetime64[ns]",
    "merchant_raw": "string",
    "merchant": "string",
    "amount": "float64",
    "category": "string",
    "subcategory": "string",
    "cardholder": "string",
    "card": "string",
    "earn_rate": "float64",
    "reward_amount": "float64",
    "is_recurring": "bool",
    "merchant_state": "string",
    "statement_file": "string",
}


def _empty_df() -> pd.DataFrame:
    """Return an empty DataFrame with the transaction schema."""
    return pd.DataFrame({col: pd.Series(dtype=dtype) for col, dtype in TRANSACTION_SCHEMA.items()})


def _load_existing(card_id: str) -> pd.DataFrame:
    """Load existing parquet for a card, or return empty DataFrame."""
    path = TRANSACTIONS_DIR / f"{card_id}.parquet"
    if path.exists():
        return pd.read_parquet(path)
    return _empty_df()


def _save(df: pd.DataFrame, card_id: str) -> None:
    """Save DataFrame to parquet."""
    TRANSACTIONS_DIR.mkdir(parents=True, exist_ok=True)
    df.to_parquet(TRANSACTIONS_DIR / f"{card_id}.parquet", index=False)


def _already_parsed(df: pd.DataFrame, filename: str) -> bool:
    """Check if a statement file is already in the parquet."""
    if df.empty:
        return False
    return filename in df["statement_file"].values


def _normalize_row(merchant_raw: str) -> tuple[str, str, str]:
    """Normalize a single merchant string."""
    return normalize_merchant(merchant_raw)


###############################################################################
# Amex Excel Parser
###############################################################################

def parse_amex_excel(filepath: Path) -> pd.DataFrame:
    """Parse an Amex BCP activity Excel export.

    Column mapping (header=None, 0-indexed):
    0=date (MM/DD/YYYY), 1=merchant_raw, 2=cardholder, 3=card_suffix,
    4=amount (numeric), 5=detail, 6=merchant_dup, 7=address,
    8=city_state, 9=zip, 10=country, 11=txn_id, 12=amex_category
    """
    raw = pd.read_excel(filepath, header=None)
    date_mask = raw[0].astype(str).str.match(r"^\d{2}/\d{2}/\d{4}$", na=False)
    raw = raw[date_mask].copy()

    if raw.empty:
        return _empty_df()

    rows = []
    for _, r in raw.iterrows():
        amount = pd.to_numeric(r[4], errors="coerce")
        if pd.isna(amount) or amount <= 0:
            continue

        merchant_raw = str(r[1]).strip()
        name, cat, sub = _normalize_row(merchant_raw)
        cardholder_raw = str(r[2]).strip().lower()
        cardholder = "dana" if "dana" in cardholder_raw else "chris"

        # Extract state from merchant_raw (last 2-char word before end)
        state_match = re.search(r"\b([A-Z]{2})\s*$", str(r[1]))
        merchant_state = state_match.group(1) if state_match else ""

        rows.append({
            "date": pd.to_datetime(r[0], format="%m/%d/%Y"),
            "merchant_raw": merchant_raw,
            "merchant": name,
            "amount": float(amount),
            "category": cat,
            "subcategory": sub,
            "cardholder": cardholder,
            "card": "amex-bcp",
            "earn_rate": 0.0,
            "reward_amount": 0.0,
            "is_recurring": False,
            "merchant_state": merchant_state,
            "statement_file": filepath.name,
        })

    if not rows:
        return _empty_df()
    return pd.DataFrame(rows)


###############################################################################
# Chase PDF Parser
###############################################################################

def parse_chase_pdf(filepath: Path, card_id: str) -> pd.DataFrame:
    """Parse a Chase statement PDF (works for Amazon, Freedom, DoorDash cards).

    Looks for the PURCHASE section. Transaction lines:
    date (MM/DD) merchant_description amount
    Skips PAYMENTS AND OTHER CREDITS section and Order Number lines.
    """
    text_pages = []
    with pdfplumber.open(filepath) as pdf:
        for page in pdf.pages:
            t = page.extract_text()
            if t:
                text_pages.append(t)

    full_text = "\n".join(text_pages)

    # Determine statement year from the text (look for Opening/Closing Date)
    year_match = re.search(r"Opening/Closing Date\s+(\d{2}/\d{2}/(\d{2}))", full_text)
    if year_match:
        year_short = year_match.group(2)
        year = int("20" + year_short)
    else:
        # Fallback: extract from filename (YYYYMMDD format)
        fname_match = re.match(r"(\d{4})", filepath.stem)
        year = int(fname_match.group(1)) if fname_match else 2025

    # Find the PURCHASE section
    in_purchases = False
    rows = []

    for line in full_text.split("\n"):
        line = line.strip()

        if re.match(r"^PURCHASE\b", line, re.IGNORECASE):
            in_purchases = True
            continue
        if re.match(r"^(PAYMENTS|FEES CHARGED|INTEREST CHARGE|TOTAL\b|Year-to-date|2\d{3} Totals)", line, re.IGNORECASE):
            in_purchases = False
            continue
        if not in_purchases:
            continue

        # Skip non-transaction lines
        if re.match(r"^Order Number", line):
            continue
        if re.match(r"^Date of", line) or re.match(r"^Transaction\b", line):
            continue

        # Match transaction: MM/DD description amount
        txn_match = re.match(r"^(\d{2}/\d{2})\s+(.+?)\s+([\-]?\d[\d,]*\.\d{2})\s*$", line)
        if not txn_match:
            continue

        date_str = txn_match.group(1)
        merchant_raw = txn_match.group(2).strip()
        amount_str = txn_match.group(3).replace(",", "")
        amount = float(amount_str)

        if amount <= 0:
            continue

        month = int(date_str.split("/")[0])
        # Handle year rollover (Dec statement closing in Jan)
        txn_year = year if month <= 12 else year
        # If statement closes in Jan but txn is in Dec, use prior year
        if year_match:
            close_month = int(year_match.group(1).split("/")[0])
            if month > close_month and month >= 10:
                txn_year = year - 1

        name, cat, sub = _normalize_row(merchant_raw)

        # Extract state
        state_match = re.search(r"\b([A-Z]{2})\s*$", merchant_raw)
        merchant_state = state_match.group(1) if state_match else ""

        rows.append({
            "date": pd.Timestamp(year=txn_year, month=month, day=int(date_str.split("/")[1])),
            "merchant_raw": merchant_raw,
            "merchant": name,
            "amount": amount,
            "category": cat,
            "subcategory": sub,
            "cardholder": "",
            "card": card_id,
            "earn_rate": 0.0,
            "reward_amount": 0.0,
            "is_recurring": False,
            "merchant_state": merchant_state,
            "statement_file": filepath.name,
        })

    if not rows:
        return _empty_df()
    return pd.DataFrame(rows)


###############################################################################
# Wells Fargo PDF Parser
###############################################################################

def parse_wf_pdf(filepath: Path, card_id: str) -> pd.DataFrame:
    """Parse a Wells Fargo statement PDF.

    Transaction lines in Purchases section:
    card_ending trans_date post_date reference_number description amount
    Format: 1911 MM/DD MM/DD ref_number description amount
    """
    text_pages = []
    with pdfplumber.open(filepath) as pdf:
        for page in pdf.pages:
            t = page.extract_text()
            if t:
                text_pages.append(t)

    full_text = "\n".join(text_pages)

    # Get year from Statement Period
    period_match = re.search(r"Statement Period\s+(\d{2}/\d{2}/(\d{4}))\s+to\s+(\d{2}/\d{2}/(\d{4}))", full_text)
    if period_match:
        year = int(period_match.group(4))
    else:
        # Fallback from filename (MMDDYY format)
        fname_match = re.match(r"(\d{2})(\d{2})(\d{2})", filepath.stem.split()[0])
        if fname_match:
            year = 2000 + int(fname_match.group(3))
        else:
            year = 2025

    in_purchases = False
    rows = []

    for line in full_text.split("\n"):
        line = line.strip()

        if "Purchases, Balance Transfers" in line:
            in_purchases = True
            continue
        if re.match(r"^(TOTAL PURCHASES|TOTAL FEES|Fees Charged|Interest Charged|Payments\b|Other Credits)", line, re.IGNORECASE):
            in_purchases = False
            continue
        if not in_purchases:
            continue

        # Match WF transaction: card_end MM/DD MM/DD ref description amount
        txn_match = re.match(
            r"^\d{4}\s+(\d{2}/\d{2})\s+\d{2}/\d{2}\s+\S+\s+(.+?)\s+([\d,]+\.\d{2})\s*$",
            line
        )
        if not txn_match:
            continue

        date_str = txn_match.group(1)
        merchant_raw = txn_match.group(2).strip()
        amount_str = txn_match.group(3).replace(",", "")
        amount = float(amount_str)

        if amount <= 0:
            continue

        month = int(date_str.split("/")[0])
        day = int(date_str.split("/")[1])
        name, cat, sub = _normalize_row(merchant_raw)

        state_match = re.search(r"\b([A-Z]{2})\s*$", merchant_raw)
        merchant_state = state_match.group(1) if state_match else ""

        rows.append({
            "date": pd.Timestamp(year=year, month=month, day=day),
            "merchant_raw": merchant_raw,
            "merchant": name,
            "amount": amount,
            "category": cat,
            "subcategory": sub,
            "cardholder": "chris",
            "card": card_id,
            "earn_rate": 0.0,
            "reward_amount": 0.0,
            "is_recurring": False,
            "merchant_state": merchant_state,
            "statement_file": filepath.name,
        })

    if not rows:
        return _empty_df()
    return pd.DataFrame(rows)


###############################################################################
# Orchestration
###############################################################################

# Maps statement subdirectory to (parser_function, card_id, file_pattern)
CARD_PARSERS = {
    "amex": {
        "card_id": "amex-bcp",
        "parser": "amex_excel",
        "pattern": "*.xlsx",
    },
    "amazon": {
        "card_id": "chase-amazon",
        "parser": "chase_pdf",
        "pattern": "*.pdf",
    },
    "freedom": {
        "card_id": "chase-freedom",
        "parser": "chase_pdf",
        "pattern": "*.pdf",
    },
    "wells_fargo": {
        "card_id": "wf-active-cash",
        "parser": "wf_pdf",
        "pattern": "*.pdf",
    },
    "checkings": {
        "card_id": "wf-checking",
        "parser": "wf_pdf",
        "pattern": "*.pdf",
    },
}


def parse_new_statements(card_filter: str | None = None) -> dict[str, int]:
    """Parse all new statements and append to parquets.

    Args:
        card_filter: Optional subdirectory name to parse only one card.
                     e.g., "amex", "amazon", "freedom", "wells_fargo", "checkings"

    Returns:
        Dict of card_id -> count of new transactions added.
    """
    results = {}
    parsers_to_run = CARD_PARSERS
    if card_filter:
        parsers_to_run = {k: v for k, v in CARD_PARSERS.items() if k == card_filter}

    for subdir, config in parsers_to_run.items():
        card_id = config["card_id"]
        stmt_dir = STATEMENTS_DIR / subdir

        if not stmt_dir.exists():
            results[card_id] = 0
            continue

        existing = _load_existing(card_id)
        files = sorted(stmt_dir.glob(config["pattern"]))
        new_frames = []

        for f in files:
            if _already_parsed(existing, f.name):
                continue

            if config["parser"] == "amex_excel":
                df = parse_amex_excel(f)
            elif config["parser"] == "chase_pdf":
                df = parse_chase_pdf(f, card_id)
            elif config["parser"] == "wf_pdf":
                df = parse_wf_pdf(f, card_id)
            else:
                continue

            if not df.empty:
                new_frames.append(df)

        if new_frames:
            new_df = pd.concat(new_frames, ignore_index=True)
            combined = pd.concat([existing, new_df], ignore_index=True)
            combined = combined.drop_duplicates(
                subset=["date", "merchant_raw", "amount", "card", "statement_file"],
                keep="first",
            )
            combined = combined.sort_values("date").reset_index(drop=True)
            _save(combined, card_id)
            results[card_id] = len(new_df)
        else:
            results[card_id] = 0

    return results


def load_all_transactions() -> pd.DataFrame:
    """Load all parquet files into a single DataFrame."""
    frames = []
    if TRANSACTIONS_DIR.exists():
        for f in sorted(TRANSACTIONS_DIR.glob("*.parquet")):
            frames.append(pd.read_parquet(f))
    if frames:
        return pd.concat(frames, ignore_index=True).sort_values("date").reset_index(drop=True)
    return _empty_df()
```

- [ ] **Step 2: Write basic test**

```python
###############################################################################
# lib/tests/test_parse.py
###############################################################################
import pandas as pd
import pytest
from lib.parse import _empty_df, TRANSACTION_SCHEMA, parse_amex_excel
from pathlib import Path


def test_empty_df_has_correct_columns():
    df = _empty_df()
    assert list(df.columns) == list(TRANSACTION_SCHEMA.keys())
    assert len(df) == 0


def test_parse_amex_excel_returns_dataframe():
    """Smoke test against real data if available."""
    path = Path("external/card-ops/statements/amex/activity_3.xlsx")
    if not path.exists():
        pytest.skip("No test data available")
    df = parse_amex_excel(path)
    assert isinstance(df, pd.DataFrame)
    assert len(df) > 0
    assert "merchant" in df.columns
    assert "category" in df.columns
    assert df["card"].iloc[0] == "amex-bcp"
```

- [ ] **Step 3: Run tests**

Run: `cd external/card-ops && python -m pytest lib/tests/test_parse.py -v`
Expected: PASS

- [ ] **Step 4: Run full parse on existing statements to seed parquets**

```python
# Run from VS Code cell in external/card-ops/
from lib.parse import parse_new_statements
results = parse_new_statements()
for card_id, count in results.items():
    print(f"  {card_id}: {count} new transactions")
```

This will take a few minutes to parse all 260 statements. Verify each parquet was created in `data/transactions/`.

- [ ] **Step 5: Commit**

```bash
git add lib/parse.py lib/tests/test_parse.py
git commit -m "feat(card-ops): add statement parsers for Amex Excel, Chase PDF, WF PDF with incremental parquet storage"
```

Note: Do NOT commit the parquet files -- they're derived data. Add `data/transactions/*.parquet` to `.gitignore` if not already covered.

---

## Task 4: Spending Profile Module

**Files:**
- Create: `lib/spending.py`

- [ ] **Step 1: Write spending.py**

```python
###############################################################################
# lib/spending.py -- Household spending profile builder
###############################################################################
from pathlib import Path

import pandas as pd
import yaml

from lib.parse import load_all_transactions


CARD_OPS_ROOT = Path(__file__).parent.parent
ANALYSIS_DIR = CARD_OPS_ROOT / "data" / "analysis"


def build_spending_profile(months: int = 12) -> dict:
    """Build household spending summary from transaction parquets.

    Args:
        months: Number of recent months to analyze.

    Returns:
        Dict with category totals, monthly averages, top merchants, card breakdown.
    """
    df = load_all_transactions()
    if df.empty:
        return {"error": "No transaction data. Run scan mode first."}

    # Filter to recent N months
    cutoff = df["date"].max() - pd.DateOffset(months=months)
    df = df[df["date"] >= cutoff].copy()
    df["month"] = df["date"].dt.to_period("M")
    n_months = df["month"].nunique()

    # Category summary
    cat_summary = (
        df.groupby("category")["amount"]
        .agg(["sum", "count"])
        .rename(columns={"sum": "total", "count": "txn_count"})
        .sort_values("total", ascending=False)
    )
    cat_summary["monthly_avg"] = (cat_summary["total"] / n_months).round(0)
    cat_summary["pct"] = (cat_summary["total"] / cat_summary["total"].sum() * 100).round(1)

    # By card
    card_summary = (
        df.groupby("card")["amount"]
        .agg(["sum", "count"])
        .rename(columns={"sum": "total", "count": "txn_count"})
        .sort_values("total", ascending=False)
    )
    card_summary["monthly_avg"] = (card_summary["total"] / n_months).round(0)

    # By cardholder
    holder_summary = (
        df.groupby("cardholder")["amount"]
        .agg(["sum", "count"])
        .rename(columns={"sum": "total", "count": "txn_count"})
        .sort_values("total", ascending=False)
    )

    # Top merchants
    top_merchants = (
        df.groupby("merchant")["amount"]
        .agg(["sum", "count", "mean"])
        .rename(columns={"sum": "total", "count": "txn_count", "mean": "avg_txn"})
        .sort_values("total", ascending=False)
        .head(20)
    )

    # Monthly trend
    monthly_trend = (
        df.groupby("month")["amount"]
        .sum()
        .sort_index()
    )

    # Category by card (for routing analysis)
    cat_card = (
        df.groupby(["category", "card"])["amount"]
        .sum()
        .unstack(fill_value=0)
    )

    profile = {
        "period": f"{df['date'].min().strftime('%Y-%m-%d')} to {df['date'].max().strftime('%Y-%m-%d')}",
        "months_analyzed": int(n_months),
        "total_spend": float(cat_summary["total"].sum()),
        "monthly_avg": float(cat_summary["total"].sum() / n_months),
        "categories": {
            cat: {
                "total": float(row["total"]),
                "monthly_avg": float(row["monthly_avg"]),
                "pct": float(row["pct"]),
                "txn_count": int(row["txn_count"]),
            }
            for cat, row in cat_summary.iterrows()
        },
        "by_card": {
            card: {
                "total": float(row["total"]),
                "monthly_avg": float(row["monthly_avg"]),
                "txn_count": int(row["txn_count"]),
            }
            for card, row in card_summary.iterrows()
        },
        "by_cardholder": {
            holder: {"total": float(row["total"]), "txn_count": int(row["txn_count"])}
            for holder, row in holder_summary.iterrows()
        },
        "top_merchants": {
            m: {
                "total": float(row["total"]),
                "txn_count": int(row["txn_count"]),
                "avg_txn": round(float(row["avg_txn"]), 2),
            }
            for m, row in top_merchants.iterrows()
        },
    }

    # Save to YAML
    ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)
    with open(ANALYSIS_DIR / "spending-profile.yml", "w") as f:
        yaml.dump(profile, f, default_flow_style=False, sort_keys=False)

    return profile


def print_spending_summary(profile: dict | None = None) -> None:
    """Print a formatted spending summary to console."""
    if profile is None:
        profile = build_spending_profile()

    if "error" in profile:
        print(profile["error"])
        return

    print(f"Period: {profile['period']} ({profile['months_analyzed']} months)")
    print(f"Total spend: ${profile['total_spend']:,.0f}")
    print(f"Monthly avg: ${profile['monthly_avg']:,.0f}/mo")
    print()
    print("Category Breakdown:")
    print(f"  {'Category':<20s}  {'Monthly':>9s}  {'Pct':>6s}  {'Txns':>5s}")
    print(f"  {'-'*20}  {'-'*9}  {'-'*6}  {'-'*5}")
    for cat, data in profile["categories"].items():
        print(f"  {cat:<20s}  ${data['monthly_avg']:>7,.0f}  {data['pct']:>5.1f}%  {data['txn_count']:>5d}")
    print()
    print("By Card:")
    for card, data in profile["by_card"].items():
        print(f"  {card:<20s}  ${data['monthly_avg']:>7,.0f}/mo  ({data['txn_count']} txns)")
    print()
    print("Top 10 Merchants:")
    for i, (m, data) in enumerate(profile["top_merchants"].items()):
        if i >= 10:
            break
        print(f"  {m:<30s}  ${data['total']:>10,.0f}  ({data['txn_count']} txns, avg ${data['avg_txn']:,.0f})")
```

- [ ] **Step 2: Commit**

```bash
git add lib/spending.py
git commit -m "feat(card-ops): add spending profile builder with category/card/merchant breakdown"
```

---

## Task 5: Rewards Calculator Module

**Files:**
- Create: `lib/rewards.py`

- [ ] **Step 1: Write rewards.py**

```python
###############################################################################
# lib/rewards.py -- Rewards calculator + routing leak detector
###############################################################################
from pathlib import Path

import pandas as pd
import yaml

from lib.parse import load_all_transactions


CARD_OPS_ROOT = Path(__file__).parent.parent
CONFIG_DIR = CARD_OPS_ROOT / "config"


def _load_card_rates() -> dict[str, dict[str, float]]:
    """Load earn rates from both applicant profiles."""
    rates = {}
    for profile_file in CONFIG_DIR.glob("profile-*.yml"):
        with open(profile_file) as f:
            profile = yaml.safe_load(f)
        for card in profile.get("cards", []):
            card_slug = f"{card['issuer'].lower().replace(' ', '-')}-{card['card'].lower().split()[0]}"
            # Build a lookup from the earn_rates dict
            rates[card_slug] = card.get("earn_rates", {})
    return rates


def _best_rate_for_category(category: str, wallet_routing: dict, card_rates: dict) -> tuple[str, float]:
    """Determine the best card + rate for a category from the household wallet."""
    # Map categories to routing keys
    routing_map = {
        "Groceries": "groceries_primary",
        "Dining": "dining",
        "Delivery": "doordash",
        "Amazon": "amazon",
        "Gas": "gas",
        "Streaming": "streaming",
    }
    # For categories with explicit routing, use that card
    routing_key = routing_map.get(category, "everything_else")
    best_card = wallet_routing.get(routing_key, wallet_routing.get("everything_else", "wf-active-cash"))

    # Look up rate for that card
    card_earn = card_rates.get(best_card, {})

    # Simplified rate lookup -- in practice, modes will use more nuanced logic
    category_rate_map = {
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

    rate_key = category_rate_map.get(category, "other")
    rate = card_earn.get(rate_key, card_earn.get("everything", card_earn.get("other", 0.01)))
    return best_card, float(rate)


def calculate_rewards(months: int = 12) -> dict:
    """Calculate actual rewards earned and identify routing leaks.

    Returns dict with:
    - current_rewards: what each card earned at its actual rate
    - optimal_rewards: what each category COULD earn at the best available rate
    - leaks: categories where spend is on a suboptimal card
    """
    df = load_all_transactions()
    if df.empty:
        return {"error": "No transaction data."}

    # Load household routing
    household_path = CONFIG_DIR / "household.yml"
    with open(household_path) as f:
        household = yaml.safe_load(f)
    wallet_routing = household.get("wallet_routing", {})

    card_rates = _load_card_rates()

    cutoff = df["date"].max() - pd.DateOffset(months=months)
    df = df[df["date"] >= cutoff].copy()
    n_months = df["month"].nunique() if "month" in df.columns else df["date"].dt.to_period("M").nunique()

    # Calculate current rewards by category and card
    current = []
    optimal = []
    leaks = []

    for (cat, card), group in df.groupby(["category", "card"]):
        annual_spend = float(group["amount"].sum()) / n_months * 12
        card_earn = card_rates.get(card, {})

        # Current earn rate (simplified)
        current_rate = card_earn.get("everything", card_earn.get("other", 0.01))
        current_reward = annual_spend * current_rate

        # Best available rate
        best_card, best_rate = _best_rate_for_category(cat, wallet_routing, card_rates)
        optimal_reward = annual_spend * best_rate

        current.append({
            "category": cat,
            "card": card,
            "annual_spend": round(annual_spend, 0),
            "earn_rate": current_rate,
            "annual_reward": round(current_reward, 2),
        })
        optimal.append({
            "category": cat,
            "best_card": best_card,
            "annual_spend": round(annual_spend, 0),
            "best_rate": best_rate,
            "annual_reward": round(optimal_reward, 2),
        })

        if best_rate > current_rate and annual_spend > 100:
            leaks.append({
                "category": cat,
                "current_card": card,
                "current_rate": current_rate,
                "best_card": best_card,
                "best_rate": best_rate,
                "annual_spend": round(annual_spend, 0),
                "annual_leak": round(optimal_reward - current_reward, 2),
            })

    total_current = sum(r["annual_reward"] for r in current)
    total_optimal = sum(r["annual_reward"] for r in optimal)
    total_leak = sum(l["annual_leak"] for l in leaks)

    return {
        "period_months": n_months,
        "total_current_rewards": round(total_current, 2),
        "total_optimal_rewards": round(total_optimal, 2),
        "total_routing_leak": round(total_leak, 2),
        "effective_rate": round(total_current / (sum(r["annual_spend"] for r in current) or 1) * 100, 2),
        "optimal_rate": round(total_optimal / (sum(r["annual_spend"] for r in optimal) or 1) * 100, 2),
        "leaks": sorted(leaks, key=lambda x: x["annual_leak"], reverse=True),
        "by_category": current,
    }
```

- [ ] **Step 2: Commit**

```bash
git add lib/rewards.py
git commit -m "feat(card-ops): add rewards calculator with routing leak detection"
```

---

## Task 6: Subscription Detection + Trends Module

**Files:**
- Create: `lib/subscriptions.py`
- Create: `lib/trends.py`

- [ ] **Step 1: Write subscriptions.py**

```python
###############################################################################
# lib/subscriptions.py -- Recurring charge detection + audit
###############################################################################
import pandas as pd
import yaml
from pathlib import Path

from lib.parse import load_all_transactions


CARD_OPS_ROOT = Path(__file__).parent.parent
ANALYSIS_DIR = CARD_OPS_ROOT / "data" / "analysis"


def detect_subscriptions(months: int = 6) -> list[dict]:
    """Detect recurring charges by finding merchants with regular, similar-amount charges.

    A subscription is defined as: same normalized merchant appearing 3+ times
    in the last N months with amounts within 20% of each other.
    """
    df = load_all_transactions()
    if df.empty:
        return []

    cutoff = df["date"].max() - pd.DateOffset(months=months)
    recent = df[df["date"] >= cutoff].copy()

    subs = []
    for merchant, group in recent.groupby("merchant"):
        if len(group) < 3:
            continue

        # Check amount consistency (within 20% of median)
        median_amt = group["amount"].median()
        if median_amt == 0:
            continue
        within_range = group["amount"].between(median_amt * 0.8, median_amt * 1.2)
        consistent_count = within_range.sum()

        if consistent_count < 3:
            continue

        # Calculate frequency
        dates = group["date"].sort_values()
        if len(dates) >= 2:
            avg_gap = (dates.diff().dropna().dt.days.mean())
        else:
            avg_gap = 30

        # Determine frequency label
        if avg_gap < 10:
            freq = "weekly"
        elif avg_gap < 45:
            freq = "monthly"
        elif avg_gap < 100:
            freq = "quarterly"
        else:
            freq = "annual"

        card = group["card"].mode().iloc[0] if len(group["card"].mode()) > 0 else "unknown"
        category = group["category"].mode().iloc[0] if len(group["category"].mode()) > 0 else "Other"

        subs.append({
            "merchant": merchant,
            "monthly_cost": round(float(median_amt) * (30 / max(avg_gap, 1)), 2),
            "typical_charge": round(float(median_amt), 2),
            "frequency": freq,
            "charges_in_period": int(len(group)),
            "card": card,
            "category": category,
            "first_seen": group["date"].min().strftime("%Y-%m-%d"),
            "last_seen": group["date"].max().strftime("%Y-%m-%d"),
        })

    subs.sort(key=lambda x: x["monthly_cost"], reverse=True)

    # Save audit
    ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)
    audit = {
        "generated": pd.Timestamp.now().strftime("%Y-%m-%d"),
        "total_monthly": round(sum(s["monthly_cost"] for s in subs), 2),
        "total_annual": round(sum(s["monthly_cost"] for s in subs) * 12, 2),
        "count": len(subs),
        "subscriptions": subs,
    }
    with open(ANALYSIS_DIR / "subscription-audit.yml", "w") as f:
        yaml.dump(audit, f, default_flow_style=False, sort_keys=False)

    return subs
```

- [ ] **Step 2: Write trends.py**

```python
###############################################################################
# lib/trends.py -- Trend detection + change flagging
###############################################################################
import pandas as pd
import yaml
from pathlib import Path

from lib.parse import load_all_transactions


CARD_OPS_ROOT = Path(__file__).parent.parent
ANALYSIS_DIR = CARD_OPS_ROOT / "data" / "analysis"
CONFIG_DIR = CARD_OPS_ROOT / "config"


def detect_changes() -> dict:
    """Compare trailing 3 months to prior 3 months and flag significant shifts."""
    df = load_all_transactions()
    if df.empty:
        return {"flags": [], "requires_full_reanalysis": False}

    df["month"] = df["date"].dt.to_period("M")
    latest_month = df["month"].max()

    # Define periods
    current_end = latest_month
    current_start = current_end - 2  # 3 months
    baseline_end = current_start - 1
    baseline_start = baseline_end - 2  # 3 months

    current = df[(df["month"] >= current_start) & (df["month"] <= current_end)]
    baseline = df[(df["month"] >= baseline_start) & (df["month"] <= baseline_end)]

    current_months = current["month"].nunique() or 1
    baseline_months = baseline["month"].nunique() or 1

    flags = []

    # 1. Category spend shifts (>25% in top-5 categories)
    current_cats = current.groupby("category")["amount"].sum() / current_months
    baseline_cats = baseline.groupby("category")["amount"].sum() / baseline_months

    top_cats = baseline_cats.nlargest(5).index.tolist()
    # Also check categories that are top-5 in current period
    top_cats = list(set(top_cats + current_cats.nlargest(5).index.tolist()))

    for cat in top_cats:
        curr_val = current_cats.get(cat, 0)
        base_val = baseline_cats.get(cat, 0)
        if base_val > 50:  # Ignore tiny categories
            change_pct = ((curr_val - base_val) / base_val) * 100
            if abs(change_pct) > 25:
                flags.append({
                    "type": "category_shift",
                    "category": cat,
                    "baseline_monthly": round(float(base_val), 0),
                    "current_monthly": round(float(curr_val), 0),
                    "change_pct": round(float(change_pct), 0),
                    "severity": "high" if abs(change_pct) > 50 else "medium",
                    "recommendation": f"{'Increased' if change_pct > 0 else 'Decreased'} {cat} spending -- review card routing",
                })

    # 2. New recurring merchants
    current_merchants = set(current[current.groupby("merchant")["merchant"].transform("count") >= 3]["merchant"].unique())
    baseline_merchants = set(baseline["merchant"].unique())
    new_merchants = current_merchants - baseline_merchants

    for m in new_merchants:
        m_data = current[current["merchant"] == m]
        monthly_amt = float(m_data["amount"].sum()) / current_months
        severity = "high" if monthly_amt > 500 else "medium" if monthly_amt > 100 else "low"
        flags.append({
            "type": "new_recurring",
            "merchant": m,
            "monthly_amount": round(monthly_amt, 0),
            "first_seen": m_data["date"].min().strftime("%Y-%m-%d"),
            "severity": severity,
            "recommendation": f"New recurring expense: {m} at ${monthly_amt:,.0f}/mo",
        })

    # 3. Geographic shift
    current_states = current["merchant_state"].value_counts(normalize=True)
    baseline_states = baseline["merchant_state"].value_counts(normalize=True)

    if len(current_states) > 0 and len(baseline_states) > 0:
        current_top = current_states.index[0] if len(current_states) > 0 else ""
        baseline_top = baseline_states.index[0] if len(baseline_states) > 0 else ""
        if current_top and baseline_top and current_top != baseline_top:
            current_pct = current_states.get(current_top, 0) * 100
            if current_pct > 50:
                flags.append({
                    "type": "relocation",
                    "from_state": baseline_top,
                    "to_state": current_top,
                    "current_pct": round(float(current_pct), 0),
                    "severity": "high",
                    "recommendation": f"Geographic shift detected: {baseline_top} -> {current_top}",
                })

    # 4. Grocery cap warning (BCP specific)
    current_year = pd.Timestamp.now().year
    ytd_grocery_bcp = df[
        (df["date"].dt.year == current_year)
        & (df["card"] == "amex-bcp")
        & (df["category"] == "Groceries")
    ]["amount"].sum()

    if ytd_grocery_bcp > 4500:
        monthly_grocery_rate = ytd_grocery_bcp / max(pd.Timestamp.now().month, 1)
        projected_cap_month = int(6000 / monthly_grocery_rate) + 1 if monthly_grocery_rate > 0 else 12
        flags.append({
            "type": "cap_warning",
            "card": "amex-bcp",
            "category": "Groceries",
            "ytd_spend": round(float(ytd_grocery_bcp), 0),
            "cap": 6000,
            "projected_cap_month": min(projected_cap_month, 12),
            "severity": "medium",
            "recommendation": f"BCP grocery cap ${ytd_grocery_bcp:,.0f}/$6,000 YTD -- switch to overflow card soon",
        })

    requires_reanalysis = any(f["severity"] == "high" for f in flags)

    result = {
        "generated": pd.Timestamp.now().strftime("%Y-%m-%d"),
        "baseline_period": f"{baseline_start} to {baseline_end}",
        "current_period": f"{current_start} to {current_end}",
        "flags": flags,
        "requires_full_reanalysis": requires_reanalysis,
    }

    ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)
    with open(ANALYSIS_DIR / "change-flags.yml", "w") as f:
        yaml.dump(result, f, default_flow_style=False, sort_keys=False)

    return result
```

- [ ] **Step 3: Commit**

```bash
git add lib/subscriptions.py lib/trends.py
git commit -m "feat(card-ops): add subscription detection and trend/change-flag modules"
```

---

## Task 7: Portfolio Model Module

**Files:**
- Create: `lib/model.py`

- [ ] **Step 1: Write model.py**

```python
###############################################################################
# lib/model.py -- Portfolio scenario modeling
###############################################################################
from typing import TypedDict
import yaml
from pathlib import Path


CARD_OPS_ROOT = Path(__file__).parent.parent
CONFIG_DIR = CARD_OPS_ROOT / "config"


class CardSpec(TypedDict):
    name: str
    annual_fee: float
    earn_rates: dict[str, float]  # category -> rate


class ScenarioResult(TypedDict):
    name: str
    cards: list[str]
    gross_rewards: float
    total_af: float
    net_rewards: float
    effective_rate: float
    routing: dict[str, tuple[str, float]]  # category -> (card_name, rate)


def _load_current_cards() -> list[CardSpec]:
    """Load all cards from both applicant profiles."""
    cards = []
    for profile_file in CONFIG_DIR.glob("profile-*.yml"):
        with open(profile_file) as f:
            profile = yaml.safe_load(f)
        for card in profile.get("cards", []):
            cards.append(CardSpec(
                name=f"{card['issuer']} {card['card']}",
                annual_fee=card.get("annual_fee", 0),
                earn_rates=card.get("earn_rates", {}),
            ))
    return cards


def _best_card_for_category(
    category: str,
    cards: list[CardSpec],
    category_rate_key: str = "other",
) -> tuple[str, float]:
    """Find the card with the highest rate for a given category."""
    best_name = ""
    best_rate = 0.0
    for card in cards:
        rate = card["earn_rates"].get(category_rate_key, card["earn_rates"].get("everything", card["earn_rates"].get("other", 0.01)))
        if rate > best_rate:
            best_rate = rate
            best_name = card["name"]
    return best_name, best_rate


def model_scenario(
    spending: dict[str, float],
    cards: list[CardSpec],
    name: str = "scenario",
) -> ScenarioResult:
    """Model a portfolio scenario given spending by category and available cards.

    Args:
        spending: dict of category -> annual spend
        cards: list of CardSpec dicts
        name: scenario label

    Returns:
        ScenarioResult with routing, gross/net rewards, effective rate.
    """
    # Map categories to earn_rate keys
    cat_key_map = {
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

    routing = {}
    gross_rewards = 0.0
    total_spend = 0.0

    for cat, annual_spend in spending.items():
        rate_key = cat_key_map.get(cat, "other")
        best_name, best_rate = _best_card_for_category(cat, cards, rate_key)

        # Handle grocery cap (BCP-specific)
        if cat == "Groceries":
            for card in cards:
                cap = card["earn_rates"].get("groceries_cap")
                if cap and card["earn_rates"].get("groceries", 0) > best_rate:
                    # Split: first $cap at high rate, rest at best non-capped
                    high_rate = card["earn_rates"]["groceries"]
                    after_rate = card["earn_rates"].get("groceries_after_cap", 0.01)
                    capped_spend = min(annual_spend, cap)
                    overflow = max(annual_spend - cap, 0)

                    # Find best overflow card
                    overflow_cards = [c for c in cards if c["name"] != card["name"]]
                    overflow_name, overflow_rate = _best_card_for_category("Groceries", overflow_cards, "groceries")
                    if overflow_rate < after_rate:
                        overflow_rate = after_rate
                        overflow_name = card["name"]

                    reward = capped_spend * high_rate + overflow * overflow_rate
                    gross_rewards += reward
                    total_spend += annual_spend
                    routing[cat] = (f"{card['name']} (${cap:,.0f} cap) + {overflow_name}", high_rate)
                    break
            else:
                gross_rewards += annual_spend * best_rate
                total_spend += annual_spend
                routing[cat] = (best_name, best_rate)
        else:
            gross_rewards += annual_spend * best_rate
            total_spend += annual_spend
            routing[cat] = (best_name, best_rate)

    total_af = sum(c["annual_fee"] for c in cards)

    return ScenarioResult(
        name=name,
        cards=[c["name"] for c in cards],
        gross_rewards=round(gross_rewards, 2),
        total_af=total_af,
        net_rewards=round(gross_rewards - total_af, 2),
        effective_rate=round(gross_rewards / total_spend * 100, 2) if total_spend > 0 else 0.0,
        routing=routing,
    )


def compare_scenarios(
    spending: dict[str, float],
    scenarios: dict[str, list[CardSpec]],
) -> list[ScenarioResult]:
    """Run multiple scenarios and return sorted by net rewards."""
    results = []
    for name, cards in scenarios.items():
        results.append(model_scenario(spending, cards, name))
    results.sort(key=lambda r: r["net_rewards"], reverse=True)
    return results
```

- [ ] **Step 2: Commit**

```bash
git add lib/model.py
git commit -m "feat(card-ops): add portfolio scenario modeler with grocery cap handling"
```

---

## Task 8: Market Intelligence Module

**Files:**
- Create: `lib/market.py`

- [ ] **Step 1: Write market.py**

This module is intentionally minimal -- it defines the cache schema and staleness logic. The actual web search happens at the mode level (Claude does the searching). The module manages the YAML cache.

```python
###############################################################################
# lib/market.py -- Intelligence cache manager
###############################################################################
from datetime import datetime, timedelta
from pathlib import Path

import yaml


CARD_OPS_ROOT = Path(__file__).parent.parent
MARKET_DIR = CARD_OPS_ROOT / "data" / "market"

STALENESS_DAYS = {
    "signup_bonus": 30,
    "earn_rates": 90,
    "annual_fee": 90,
    "issuer_rules": 180,
}


def _load_cache() -> dict:
    """Load current-offers.yml."""
    path = MARKET_DIR / "current-offers.yml"
    if path.exists():
        with open(path) as f:
            return yaml.safe_load(f) or {"cards": {}}
    return {"cards": {}}


def _save_cache(cache: dict) -> None:
    """Write current-offers.yml."""
    MARKET_DIR.mkdir(parents=True, exist_ok=True)
    with open(MARKET_DIR / "current-offers.yml", "w") as f:
        yaml.dump(cache, f, default_flow_style=False, sort_keys=False)


def is_stale(card_slug: str, field: str = "signup_bonus") -> bool:
    """Check if cached data for a card is stale."""
    cache = _load_cache()
    entry = cache.get("cards", {}).get(card_slug)
    if not entry:
        return True
    fetched_str = entry.get("fetched")
    if not fetched_str:
        return True
    fetched = datetime.strptime(fetched_str, "%Y-%m-%d")
    max_age = timedelta(days=STALENESS_DAYS.get(field, 30))
    return datetime.now() - fetched > max_age


def get_cached(card_slug: str) -> dict | None:
    """Get cached card data, or None if missing."""
    cache = _load_cache()
    return cache.get("cards", {}).get(card_slug)


def update_cache(card_slug: str, data: dict) -> None:
    """Update cache with new card data. Adds fetched timestamp."""
    cache = _load_cache()
    data["fetched"] = datetime.now().strftime("%Y-%m-%d")
    cache.setdefault("cards", {})[card_slug] = data
    _save_cache(cache)


def seed_from_burn_it_all(cards: dict[str, dict]) -> None:
    """Seed the cache from burn-it-all research results.

    Args:
        cards: dict of card_slug -> {signup_bonus, msr, annual_fee, earn_rates, notes, sources}
    """
    cache = _load_cache()
    for slug, data in cards.items():
        data["fetched"] = datetime.now().strftime("%Y-%m-%d")
        cache.setdefault("cards", {})[slug] = data
    _save_cache(cache)
```

- [ ] **Step 2: Commit**

```bash
git add lib/market.py
git commit -m "feat(card-ops): add market intelligence cache manager with staleness checks"
```

---

## Task 9: Mode File Rewrites

**Files:**
- Modify: `modes/scan.md`
- Modify: `modes/optimize.md`
- Modify: `modes/evaluate.md`
- Modify: `modes/compare.md`
- Modify: `modes/tracker.md`
- Create: `modes/sequence.md`

- [ ] **Step 1: Rewrite scan.md**

Replace the entire contents of `modes/scan.md` with the v2 workflow that references lib modules. The mode file tells Claude what to do -- Claude calls the Python functions.

Key changes: scan now builds parquets, runs spending profile, detects subscriptions, flags changes. No card recommendations.

- [ ] **Step 2: Rewrite optimize.md**

Update to reference parquet data, call rewards.py for leak detection, call model.py for scenarios, call market.py for current offers. Add business card consideration when household.yml has `side_business.exists: true`.

- [ ] **Step 3: Update evaluate.md**

Add references to: `market.py` for current card terms (step 1), parquet spending data for Block D value analysis, `model.py` for Block E portfolio comparison. Keep Blocks A-F structure and scoring unchanged.

- [ ] **Step 4: Update compare.md**

Add reference to `model.py` for side-by-side scenario modeling using actual spending data.

- [ ] **Step 5: Update tracker.md**

Add: application history from `profile-*.yml`, change flags summary from `data/analysis/change-flags.yml`, AF renewal date calculation from card open dates.

- [ ] **Step 6: Create sequence.md**

New mode for application planning. References both `profile-*.yml` for eligibility, `model.py` for candidate ranking, `market.py` for current SUBs, issuer velocity rules from wiki + `data/market/rule-updates.yml`.

- [ ] **Step 7: Update CLAUDE.md**

Add `lib/` to system layer in data contract. Add new mode routing for "sequence" trigger. Reference new config file structure (dual profiles + household).

- [ ] **Step 8: Commit**

```bash
git add modes/ CLAUDE.md
git commit -m "feat(card-ops): rewrite mode files for v2 three-layer architecture"
```

---

## Task 10: Seed Market Cache from Burn-It-All Results

**Files:**
- Create: `data/market/current-offers.yml` (via market.py)
- Create: `data/market/rule-updates.yml`

- [ ] **Step 1: Seed current-offers.yml**

Use `market.seed_from_burn_it_all()` with the research data from the 27-agent analysis. Include: Citi Custom Cash, Citi Costco Anywhere, Chase Freedom Flex, Capital One Savor, US Bank Altitude Go, BofA Customized Cash, Discover it Cash Back, WF Autograph, Chase Ink Business Cash, Chase Ink Business Unlimited, DoorDash Rewards Mastercard.

- [ ] **Step 2: Create rule-updates.yml**

Write the issuer rule changes discovered during the burn-it-all that contradict or supplement the wiki:

```yaml
updates:
  - issuer: "US Bank"
    rule: "Altitude Go dining cap"
    change: "4% dining capped at $2,000/quarter as of April 2025"
    fetched: "2026-04-12"
    wiki_article: "issuer-rules.md"
    wiki_still_accurate: false

  - issuer: "Citi"
    rule: "Costco Visa gas rate increase"
    change: "5% at Costco gas stations (up from 4%) as of January 2025"
    fetched: "2026-04-12"
    wiki_article: "issuer-rules.md"
    wiki_still_accurate: false

  - issuer: "Chase"
    rule: "Sapphire 48-month rule eliminated"
    change: "Replaced with once-per-lifetime per product + proprietary pop-up system as of Jan 2026"
    fetched: "2026-04-12"
    wiki_article: "issuer-rules.md"
    wiki_still_accurate: false

  - issuer: "Capital One"
    rule: "SavorOne renamed"
    change: "No-AF card renamed to 'Savor' (Oct 2024). New 'SavorOne' is $39 AF for fair credit."
    fetched: "2026-04-12"
    wiki_article: "issuer-rules.md"
    wiki_still_accurate: false

  - issuer: "Wells Fargo"
    rule: "5/24-style rule"
    change: "WF adopted 5/24-style rule similar to Chase. Enforcement data points still accumulating."
    fetched: "2026-04-12"
    wiki_article: "issuer-rules.md"
    wiki_still_accurate: false
```

- [ ] **Step 3: Commit**

```bash
git add data/market/
git commit -m "feat(card-ops): seed market intelligence cache from burn-it-all research"
```

---

## Task 11: Gitignore + Cleanup

**Files:**
- Modify: `.gitignore` (card-ops level)
- Remove: temp analysis scripts left by burn-it-all agents

- [ ] **Step 1: Update .gitignore**

Ensure these are ignored:
```
data/transactions/*.parquet
data/analysis/*.yml
__pycache__/
*.pyc
```

Config files and market cache are tracked (they're curated, not derived).

- [ ] **Step 2: Remove temp scripts**

Clean up any `.py` files the burn-it-all agents left in the card-ops root or reports/ that aren't part of the v2 architecture (e.g., `amex_bcp_analysis.py`, `checking_analysis.py`, `grocery_routing_analysis.py`, `travel_spend_analysis.py`, `reports/subscription_audit.py`).

- [ ] **Step 3: Archive old profile.yml**

Rename `config/profile.yml` to `config/profile-v1-archive.yml` so it's preserved but not confused with the v2 profiles.

- [ ] **Step 4: Commit**

```bash
git add .gitignore
git rm config/profile.yml  # or git mv
git add config/profile-v1-archive.yml
git commit -m "chore(card-ops): gitignore derived data, archive v1 profile, cleanup temp scripts"
```

---

## Task 12: Integration Smoke Test

- [ ] **Step 1: Run full ingest**

```python
from lib.parse import parse_new_statements, load_all_transactions

results = parse_new_statements()
print("Parse results:", results)

df = load_all_transactions()
print(f"Total transactions: {len(df)}")
print(f"Date range: {df['date'].min()} to {df['date'].max()}")
print(f"Cards: {df['card'].unique().tolist()}")
print(f"Categories: {df['category'].value_counts().to_dict()}")
```

- [ ] **Step 2: Run spending profile**

```python
from lib.spending import build_spending_profile, print_spending_summary

profile = build_spending_profile(months=12)
print_spending_summary(profile)
```

- [ ] **Step 3: Run subscription audit**

```python
from lib.subscriptions import detect_subscriptions

subs = detect_subscriptions(months=6)
print(f"Found {len(subs)} subscriptions")
for s in subs[:10]:
    print(f"  {s['merchant']:30s}  ${s['monthly_cost']:>8.2f}/mo  on {s['card']}  ({s['frequency']})")
```

- [ ] **Step 4: Run change detection**

```python
from lib.trends import detect_changes

changes = detect_changes()
print(f"Flags: {len(changes['flags'])}")
print(f"Requires reanalysis: {changes['requires_full_reanalysis']}")
for f in changes["flags"]:
    print(f"  [{f['severity']}] {f['type']}: {f.get('recommendation', '')}")
```

- [ ] **Step 5: Run rewards calculator**

```python
from lib.rewards import calculate_rewards

rewards = calculate_rewards(months=12)
print(f"Current rewards: ${rewards['total_current_rewards']:,.0f}/yr ({rewards['effective_rate']:.1f}%)")
print(f"Optimal rewards: ${rewards['total_optimal_rewards']:,.0f}/yr ({rewards['optimal_rate']:.1f}%)")
print(f"Routing leaks: ${rewards['total_routing_leak']:,.0f}/yr")
for leak in rewards["leaks"][:5]:
    print(f"  {leak['category']:20s}  ${leak['annual_leak']:>7,.0f}  ({leak['current_card']} {leak['current_rate']:.0%} -> {leak['best_card']} {leak['best_rate']:.0%})")
```

- [ ] **Step 6: Commit if all pass**

```bash
git add -A
git commit -m "feat(card-ops): v2 three-layer architecture complete -- ingest, analysis, strategy layers operational"
```
