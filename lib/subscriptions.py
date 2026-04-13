"""
Subscription detection from credit card transaction data.

Scans recent transactions for recurring charges, identifies subscription
patterns, and calculates monthly cost estimates.
"""

from datetime import datetime, timedelta
from pathlib import Path
from statistics import median

import pandas as pd
import yaml

from lib.parse import load_all_transactions


###############################################################################
# Constants
###############################################################################

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_OUTPUT_PATH = _PROJECT_ROOT / "data" / "analysis" / "subscription-audit.yml"

_MIN_OCCURRENCES = 3
_AMOUNT_TOLERANCE = 0.20  # charges within 20% of median count as recurring

# avg gap (days) -> frequency label
_FREQUENCY_BANDS: list[tuple[float, float, str]] = [
    (0, 10, "weekly"),
    (10, 45, "monthly"),
    (45, 120, "quarterly"),
    (120, 400, "annual"),
]


###############################################################################
# Internal Helpers
###############################################################################

def _classify_frequency(avg_gap_days: float) -> str:
    """Map average gap between charges to a human-readable frequency label."""
    for low, high, label in _FREQUENCY_BANDS:
        if low < avg_gap_days <= high:
            return label
    return "irregular"


def _calculate_monthly_cost(median_amount: float, avg_gap_days: float) -> float:
    """Estimate monthly cost from median charge amount and average gap."""
    if avg_gap_days <= 0:
        return 0.0
    return round(median_amount * 30 / avg_gap_days, 2)


def _filter_recent(
    df: pd.DataFrame,
    months: int,
    now: datetime | None = None,
) -> pd.DataFrame:
    """Keep only transactions within the last N months."""
    ref = now or datetime.now()
    cutoff = pd.Timestamp(ref - timedelta(days=months * 30))
    return df[df["date"] >= cutoff].copy()


def _is_recurring(amounts: list[float], median_amount: float) -> bool:
    """Check whether all amounts fall within tolerance of the median."""
    if median_amount == 0:
        return False
    return all(
        abs(a - median_amount) / median_amount <= _AMOUNT_TOLERANCE
        for a in amounts
    )


def _build_subscription_record(
    merchant: str,
    df_merchant: pd.DataFrame,
) -> dict | None:
    """
    Evaluate a merchant's transactions and return a subscription record
    if the pattern qualifies, otherwise None.
    """
    if len(df_merchant) < _MIN_OCCURRENCES:
        return None

    amounts = df_merchant["amount"].tolist()
    median_amount = round(median(amounts), 2)

    if not _is_recurring(amounts, median_amount):
        return None

    dates = sorted(df_merchant["date"].tolist())
    gaps = [
        (dates[i + 1] - dates[i]).days
        for i in range(len(dates) - 1)
    ]
    avg_gap = sum(gaps) / len(gaps) if gaps else 0

    # pick the card and category from the most recent transaction
    most_recent = df_merchant.loc[df_merchant["date"].idxmax()]

    return {
        "merchant": merchant,
        "monthly_cost": _calculate_monthly_cost(median_amount, avg_gap),
        "typical_charge": median_amount,
        "frequency": _classify_frequency(avg_gap),
        "charges_in_period": len(df_merchant),
        "card": most_recent.get("card", "unknown"),
        "category": most_recent.get("category", "Other"),
        "first_seen": df_merchant["date"].min().strftime("%Y-%m-%d"),
        "last_seen": df_merchant["date"].max().strftime("%Y-%m-%d"),
    }


def _save_yaml(records: list[dict], path: Path) -> None:
    """Write subscription records to YAML."""
    path.parent.mkdir(parents=True, exist_ok=True)
    output = {
        "generated": datetime.now().strftime("%Y-%m-%d"),
        "subscription_count": len(records),
        "total_monthly_cost": round(
            sum(r["monthly_cost"] for r in records), 2
        ),
        "subscriptions": records,
    }
    path.write_text(yaml.dump(output, default_flow_style=False, sort_keys=False))


###############################################################################
# Public API
###############################################################################

def detect_subscriptions(
    months: int = 6,
    now: datetime | None = None,
) -> list[dict]:
    """
    Detect recurring charges from transaction history.

    Parameters
    ----------
    months : int
        Number of trailing months to scan (default 6).
    now : datetime | None
        Reference date for "recent" cutoff. Defaults to today.

    Returns
    -------
    list[dict]
        Subscription records sorted by monthly_cost descending.
        Each dict contains: merchant, monthly_cost, typical_charge,
        frequency, charges_in_period, card, category, first_seen,
        last_seen.
    """
    df_all = load_all_transactions()
    if df_all.empty:
        return []

    df_recent = _filter_recent(df_all, months, now=now)
    if df_recent.empty:
        return []

    subscriptions = []
    for merchant, df_merchant in df_recent.groupby("merchant"):
        record = _build_subscription_record(merchant, df_merchant)
        if record is not None:
            subscriptions.append(record)

    subscriptions.sort(key=lambda r: r["monthly_cost"], reverse=True)
    _save_yaml(subscriptions, _OUTPUT_PATH)
    return subscriptions
