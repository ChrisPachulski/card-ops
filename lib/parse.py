"""
Statement parsers for Amex Excel, Chase PDF, and Wells Fargo PDF formats.
Writes parsed transactions to parquet files in data/transactions/.
"""
from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

try:
    from lib.normalize import normalize_merchant
except ImportError:
    def normalize_merchant(raw: str) -> tuple[str, str, str]:
        """Stub -- returns (raw, 'Other', 'Uncategorized') until normalize.py exists."""
        return (raw, "Other", "Uncategorized")


###############################################################################
# Paths
###############################################################################

CARD_OPS_ROOT = Path(__file__).parent.parent
STATEMENTS_DIR = CARD_OPS_ROOT / "statements"
TRANSACTIONS_DIR = CARD_OPS_ROOT / "data" / "transactions"


###############################################################################
# Transaction Schema
###############################################################################

SCHEMA_COLUMNS: list[str] = [
    "date",
    "merchant_raw",
    "merchant",
    "amount",
    "category",
    "subcategory",
    "cardholder",
    "card",
    "earn_rate",
    "reward_amount",
    "is_recurring",
    "merchant_state",
    "statement_file",
]

SCHEMA_DTYPES: dict[str, str] = {
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


###############################################################################
# Card Parser Registry
###############################################################################

# Maps statement subdirectory -> (card_id, parser_type, file_pattern)
CARD_PARSERS: dict[str, tuple[str, str, str]] = {
    "amex": ("amex-bcp", "amex_excel", "*.xlsx"),
    "amazon": ("chase-amazon", "chase_pdf", "*.pdf"),
    "freedom": ("chase-freedom", "chase_pdf", "*.pdf"),
    "wells_fargo": ("wf-active-cash", "wf_pdf", "*.pdf"),
    "checkings": ("wf-checking", "wf_checking_pdf", "*.pdf"),
}


###############################################################################
# Helper Functions
###############################################################################

def _empty_df() -> pd.DataFrame:
    """Return an empty DataFrame with the canonical transaction schema."""
    df = pd.DataFrame(columns=SCHEMA_COLUMNS)
    df["date"] = pd.to_datetime(df["date"])
    for col, dtype in SCHEMA_DTYPES.items():
        df[col] = df[col].astype(dtype)
    return df


def _parquet_path(card_id: str) -> Path:
    """Return the parquet file path for a given card_id."""
    return TRANSACTIONS_DIR / f"{card_id}.parquet"


def _load_existing(card_id: str) -> pd.DataFrame:
    """Load existing parquet for a card, or return empty DataFrame."""
    path = _parquet_path(card_id)
    if path.exists():
        return pd.read_parquet(path)
    return _empty_df()


def _save(df: pd.DataFrame, card_id: str) -> None:
    """Save DataFrame to parquet, creating directories as needed."""
    TRANSACTIONS_DIR.mkdir(parents=True, exist_ok=True)
    df.to_parquet(_parquet_path(card_id), index=False)


def _already_parsed(df: pd.DataFrame, filename: str) -> bool:
    """Check if a statement file has already been parsed into the DataFrame."""
    if df.empty:
        return False
    return filename in df["statement_file"].values


def _extract_state(merchant_raw: str) -> str:
    """Extract the 2-letter state code from the end of a merchant string.

    Looks for a pattern like ' XX' at the end, where XX is two uppercase
    letters preceded by a space (to avoid matching domain suffixes like .COM).
    """
    if not merchant_raw:
        return ""
    match = re.search(r"\s([A-Z]{2})$", merchant_raw.strip())
    return match.group(1) if match else ""


def _build_row(
    date: pd.Timestamp,
    merchant_raw: str,
    amount: float,
    cardholder: str,
    card: str,
    statement_file: str,
) -> dict:
    """Build a single transaction row dict with normalization applied."""
    merchant, category, subcategory = normalize_merchant(merchant_raw)
    return {
        "date": date,
        "merchant_raw": merchant_raw,
        "merchant": merchant,
        "amount": float(amount),
        "category": category,
        "subcategory": subcategory,
        "cardholder": cardholder,
        "card": card,
        "earn_rate": 0.0,
        "reward_amount": 0.0,
        "is_recurring": False,
        "merchant_state": _extract_state(merchant_raw),
        "statement_file": statement_file,
    }


###############################################################################
# Amex Excel Parser
###############################################################################

def parse_amex_excel(filepath: Path) -> pd.DataFrame:
    """
    Parse an Amex Blue Cash Preferred Excel statement.

    Reads xlsx with no header, filters to rows where column 0 matches
    a date pattern (MM/DD/YYYY), maps columns, and skips payments (negatives).
    """
    raw = pd.read_excel(filepath, header=None)
    date_pattern = re.compile(r"^\d{2}/\d{2}/\d{4}$")

    rows = []
    for _, row in raw.iterrows():
        date_str = str(row.iloc[0]).strip()
        if not date_pattern.match(date_str):
            continue

        amount = pd.to_numeric(row.iloc[4], errors="coerce")
        if pd.isna(amount) or amount < 0:
            continue

        merchant_raw = str(row.iloc[1]).strip()
        cardholder_name = str(row.iloc[2]).strip().upper()
        cardholder = "dana" if "DANA" in cardholder_name else "chris"

        rows.append(_build_row(
            date=pd.to_datetime(date_str, format="%m/%d/%Y"),
            merchant_raw=merchant_raw,
            amount=amount,
            cardholder=cardholder,
            card="amex-bcp",
            statement_file=filepath.name,
        ))

    if not rows:
        return _empty_df()

    df = pd.DataFrame(rows)
    df["date"] = pd.to_datetime(df["date"])
    return df


###############################################################################
# Chase PDF Parser
###############################################################################

def _chase_extract_year(text: str, filepath: Path) -> int:
    """
    Extract the statement year from Chase PDF text or filename.

    Tries 'Opening/Closing Date' line first, falls back to YYYYMMDD filename.
    """
    # Try Opening/Closing Date line
    match = re.search(r"(?:Opening|Closing)\s+Date\s+\d{2}/\d{2}/(\d{2,4})", text)
    if match:
        year_str = match.group(1)
        year = int(year_str)
        if year < 100:
            year += 2000
        return year

    # Fallback: YYYYMMDD from filename
    fname_match = re.search(r"(\d{4})\d{4}", filepath.stem)
    if fname_match:
        return int(fname_match.group(1))

    return pd.Timestamp.now().year


def _chase_extract_closing_month(text: str, filepath: Path) -> int:
    """Extract closing month from Chase PDF for year rollover detection."""
    match = re.search(r"Closing\s+Date\s+(\d{2})/\d{2}/\d{2,4}", text)
    if match:
        return int(match.group(1))

    fname_match = re.search(r"\d{4}(\d{2})\d{2}", filepath.stem)
    if fname_match:
        return int(fname_match.group(1))

    return 0


def parse_chase_pdf(filepath: Path, card_id: str) -> pd.DataFrame:
    """
    Parse a Chase credit card PDF statement (Amazon or Freedom).

    Finds the PURCHASE section, extracts transactions via regex,
    handles year rollover for Dec transactions on Jan-closing statements.
    """
    import pdfplumber

    text = ""
    with pdfplumber.open(filepath) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"

    if not text.strip():
        return _empty_df()

    year = _chase_extract_year(text, filepath)
    closing_month = _chase_extract_closing_month(text, filepath)

    # Split into lines and find transaction sections
    lines = text.split("\n")
    in_purchase_section = False
    txn_pattern = re.compile(r"^(\d{2}/\d{2})\s+(.+?)\s+([\-]?\d[\d,]*\.\d{2})\s*$")

    rows = []
    for line in lines:
        stripped = line.strip()

        # Enter purchase section
        if re.search(r"\bPURCHASE", stripped, re.IGNORECASE):
            in_purchase_section = True
            continue

        # Exit on payments/credits section
        if re.search(r"PAYMENTS AND OTHER CREDITS", stripped, re.IGNORECASE):
            in_purchase_section = False
            continue

        if not in_purchase_section:
            continue

        # Skip order number lines
        if "Order Number" in stripped:
            continue

        match = txn_pattern.match(stripped)
        if not match:
            continue

        date_str = match.group(1)
        merchant_raw = match.group(2).strip()
        amount_str = match.group(3).replace(",", "")
        amount = float(amount_str)

        # Skip credits/refunds (negative amounts)
        if amount < 0:
            continue

        # Parse month/day and handle year rollover
        txn_month = int(date_str.split("/")[0])
        txn_year = year
        if closing_month == 1 and txn_month == 12:
            txn_year = year - 1

        full_date_str = f"{date_str}/{txn_year}"
        txn_date = pd.to_datetime(full_date_str, format="%m/%d/%Y")

        rows.append(_build_row(
            date=txn_date,
            merchant_raw=merchant_raw,
            amount=amount,
            cardholder="chris",
            card=card_id,
            statement_file=filepath.name,
        ))

    if not rows:
        return _empty_df()

    return pd.DataFrame(rows)


###############################################################################
# Wells Fargo PDF Parser
###############################################################################

def _wf_extract_year(text: str, filepath: Path) -> int:
    """
    Extract statement year from Wells Fargo PDF text or filename.

    Tries 'Statement Period' line first, falls back to MMDDYY filename.
    """
    match = re.search(r"Statement\s+Period\s+\d{2}/\d{2}/(\d{2,4})", text)
    if match:
        year_str = match.group(1)
        year = int(year_str)
        if year < 100:
            year += 2000
        return year

    # Fallback: MMDDYY from filename (e.g., "012825 WellsFargo.pdf")
    fname_match = re.search(r"(\d{6})", filepath.stem)
    if fname_match:
        yy = int(fname_match.group(1)[4:6])
        return 2000 + yy

    return pd.Timestamp.now().year


def parse_wf_pdf(filepath: Path, card_id: str) -> pd.DataFrame:
    """
    Parse a Wells Fargo credit card or checking PDF statement.

    Finds the 'Purchases, Balance Transfers' section, extracts transactions
    via the WF-specific regex format, stops at 'TOTAL PURCHASES' or 'Fees Charged'.
    """
    import pdfplumber

    text = ""
    with pdfplumber.open(filepath) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"

    if not text.strip():
        return _empty_df()

    year = _wf_extract_year(text, filepath)

    lines = text.split("\n")
    in_purchase_section = False
    txn_pattern = re.compile(
        r"^\d{4}\s+(\d{2}/\d{2})\s+\d{2}/\d{2}\s+\S+\s+(.+?)\s+([\d,]+\.\d{2})\s*$"
    )

    rows = []
    for line in lines:
        stripped = line.strip()

        # Enter purchase section
        if re.search(r"Purchases,?\s*Balance\s*Transfers", stripped, re.IGNORECASE):
            in_purchase_section = True
            continue

        # Exit on total or fees section
        if re.search(r"TOTAL\s+PURCHASES|Fees\s+Charged", stripped, re.IGNORECASE):
            in_purchase_section = False
            continue

        if not in_purchase_section:
            continue

        match = txn_pattern.match(stripped)
        if not match:
            continue

        date_str = match.group(1)
        merchant_raw = match.group(2).strip()
        amount_str = match.group(3).replace(",", "")
        amount = float(amount_str)

        full_date_str = f"{date_str}/{year}"
        txn_date = pd.to_datetime(full_date_str, format="%m/%d/%Y")

        rows.append(_build_row(
            date=txn_date,
            merchant_raw=merchant_raw,
            amount=amount,
            cardholder="chris",
            card=card_id,
            statement_file=filepath.name,
        ))

    if not rows:
        return _empty_df()

    return pd.DataFrame(rows)


###############################################################################
# Chase Checking PDF Parser
###############################################################################

def _checking_extract_year(text: str, filepath: Path) -> int:
    """
    Extract the statement year from a Chase checking PDF.

    Tries the date range header ('Month DD, YYYYthroughMonth DD, YYYY')
    first, falls back to YYYYMMDD filename prefix.
    """
    # Try "through" date range header -- grab the end date year
    match = re.search(
        r"through\s*[A-Za-z]+\s+\d{1,2},?\s+(\d{4})",
        text,
    )
    if match:
        return int(match.group(1))

    # Fallback: YYYYMMDD filename prefix
    fname_match = re.search(r"^(\d{4})\d{4}", filepath.stem)
    if fname_match:
        return int(fname_match.group(1))

    return pd.Timestamp.now().year


# Patterns to skip -- these are not spending transactions
_CHECKING_SKIP_PATTERNS: list[re.Pattern[str]] = [
    re.compile(p, re.IGNORECASE) for p in [
        r"Online\s*Transfer\s*To\s*Sav",        # internal savings xfer
        r"Transfer\s*From\s*(Chk|Sav)",          # internal account xfer
        r"Wells\s*Fargo\s*Card\s*Ccpymt",        # CC payment
        r"American\s*Express\s*ACH\s*Pmt",       # CC payment
        r"Payment\s*To\s*Chase\s*Card",           # CC payment
        r"Paypal\s*Acctverify",                   # PayPal verification
        r"Remote\s*Online\s*Deposit",             # deposit
        r"Real\s*Time\s*Transfer\s*Recd",         # incoming transfer
        r"Payroll\s*PPD",                         # payroll deposit
        r"^Deposit\b",                            # generic deposit
        r"Check\s*OR\s*Supply\s*Order",           # check order fee
    ]
]


def parse_wf_checking_pdf(filepath: Path, card_id: str) -> pd.DataFrame:
    """
    Parse a Chase checking account PDF statement.

    Despite the card_id 'wf-checking', these are Chase Total Checking
    statements. Extracts DEBIT transactions only (negative amounts),
    skipping deposits, internal transfers, and credit card payments.

    The transaction format is:
        MM/DD Description Amount Balance
    where debits are negative (prefixed with -).
    """
    import pdfplumber

    text = ""
    with pdfplumber.open(filepath) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"

    if not text.strip():
        return _empty_df()

    year = _checking_extract_year(text, filepath)

    lines = text.split("\n")
    in_transaction_section = False

    # Matches: MM/DD Description -Amount Balance  OR  MM/DD MM/DD Description -Amount Balance
    # The date-prefixed payment lines look like: "02/23 02/21 Payment To Chase Card..."
    txn_pattern = re.compile(
        r"^(\d{2}/\d{2})\s+"           # transaction date
        r"(?:\d{2}/\d{2}\s+)?"         # optional second date (posting date)
        r"(.+?)\s+"                     # description
        r"(-?[\d,]+\.\d{2})\s+"        # amount
        r"-?[\d,]+\.\d{2}\s*$"         # balance (ignored)
    )

    rows = []
    for line in lines:
        stripped = line.strip()

        # Enter transaction section
        if re.search(r"TRANSACTION\s+DETAIL", stripped, re.IGNORECASE):
            in_transaction_section = True
            continue

        # Exit on post-transaction message or end marker
        if re.search(
            r"Ending\s+Balance|"
            r"\*end\*transac|"
            r"A\s+Monthly\s+Service\s+Fee",
            stripped,
            re.IGNORECASE,
        ):
            if in_transaction_section and "Ending Balance" in stripped:
                in_transaction_section = False
                continue

        if not in_transaction_section:
            continue

        # Skip header/label lines
        if stripped.startswith("DATE") or stripped.startswith("Beginning Balance"):
            continue

        match = txn_pattern.match(stripped)
        if not match:
            continue

        date_str = match.group(1)
        description = match.group(2).strip()
        amount_str = match.group(3).replace(",", "")
        amount = float(amount_str)

        # Only keep debits (negative amounts = money going out)
        if amount >= 0:
            continue

        # Check skip patterns (CC payments, internal transfers, deposits)
        skip = False
        for skip_re in _CHECKING_SKIP_PATTERNS:
            if skip_re.search(description):
                skip = True
                break
        if skip:
            continue

        # Convert to positive for consistency with credit card transactions
        amount = abs(amount)

        # Clean up the description to extract merchant name
        # Remove common suffixes like PPD ID:, Web ID:, CCD ID:
        merchant_raw = re.sub(
            r"\s*(PPD|Web|CCD)\s*ID:\s*\S+",
            "",
            description,
        ).strip()
        # Remove trailing reference numbers
        merchant_raw = re.sub(r"\s+\d{10,}$", "", merchant_raw).strip()

        full_date_str = f"{date_str}/{year}"
        # Handle year rollover: if statement covers Dec-Jan
        txn_month = int(date_str.split("/")[0])
        txn_year = year
        # Check if the statement period spans a year boundary
        closing_match = re.search(
            r"through\s*([A-Za-z]+)\s+\d{1,2},?\s+\d{4}",
            text,
        )
        if closing_match:
            closing_month_name = closing_match.group(1).lower()
            closing_month_map = {
                "january": 1, "february": 2, "march": 3, "april": 4,
                "may": 5, "june": 6, "july": 7, "august": 8,
                "september": 9, "october": 10, "november": 11, "december": 12,
            }
            closing_month = closing_month_map.get(closing_month_name, 0)
            if closing_month <= 2 and txn_month >= 11:
                txn_year = year - 1

        full_date_str = f"{date_str}/{txn_year}"
        txn_date = pd.to_datetime(full_date_str, format="%m/%d/%Y")

        rows.append(_build_row(
            date=txn_date,
            merchant_raw=merchant_raw,
            amount=amount,
            cardholder="chris",
            card=card_id,
            statement_file=filepath.name,
        ))

    if not rows:
        return _empty_df()

    return pd.DataFrame(rows)


###############################################################################
# Orchestration
###############################################################################

PARSER_DISPATCH: dict[str, callable] = {
    "amex_excel": lambda fp, card_id: parse_amex_excel(fp),
    "chase_pdf": parse_chase_pdf,
    "wf_pdf": parse_wf_pdf,
    "wf_checking_pdf": parse_wf_checking_pdf,
}


def parse_new_statements(card_filter: str | None = None) -> dict[str, int]:
    """
    Parse new (unprocessed) statement files for each card.

    For each card in CARD_PARSERS (optionally filtered by card_filter),
    loads the existing parquet, identifies unparsed statement files,
    parses them, appends to existing data, deduplicates, sorts by date,
    and saves the updated parquet.

    Returns a dict of card_id -> count of new transactions added.
    """
    results: dict[str, int] = {}

    for subdir, (card_id, parser_type, file_pattern) in CARD_PARSERS.items():
        if card_filter and card_id != card_filter:
            continue

        stmt_dir = STATEMENTS_DIR / subdir
        if not stmt_dir.exists():
            continue

        existing = _load_existing(card_id)
        parser_fn = PARSER_DISPATCH[parser_type]

        new_dfs: list[pd.DataFrame] = []
        for filepath in sorted(stmt_dir.glob(file_pattern)):
            if _already_parsed(existing, filepath.name):
                continue

            try:
                df_new = parser_fn(filepath, card_id)
                if not df_new.empty:
                    new_dfs.append(df_new)
            except Exception as e:
                print(f"[parse] Error parsing {filepath.name}: {e}")
                continue

        if not new_dfs:
            results[card_id] = 0
            continue

        df_all_new = pd.concat(new_dfs, ignore_index=True)
        new_count = len(df_all_new)

        combined = pd.concat([existing, df_all_new], ignore_index=True)
        combined = combined.drop_duplicates(
            subset=["date", "merchant_raw", "amount", "card", "statement_file"],
            keep="first",
        )
        combined = combined.sort_values("date").reset_index(drop=True)

        _save(combined, card_id)
        results[card_id] = new_count

    return results


def load_all_transactions() -> pd.DataFrame:
    """Load all parquet files from data/transactions/ into one DataFrame."""
    if not TRANSACTIONS_DIR.exists():
        return _empty_df()

    parquets = list(TRANSACTIONS_DIR.glob("*.parquet"))
    if not parquets:
        return _empty_df()

    dfs = [pd.read_parquet(p) for p in parquets]
    combined = pd.concat(dfs, ignore_index=True)
    return combined.sort_values("date").reset_index(drop=True)
