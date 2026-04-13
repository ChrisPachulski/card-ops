###############################################################################
# SPENDING PROFILE BUILDER
# Reads all parquet transaction data and produces a structured spending profile
# with category totals, card breakdown, cardholder breakdown, and top merchants.
###############################################################################

import pandas as pd
import yaml
from datetime import datetime
from pathlib import Path
from dateutil.relativedelta import relativedelta

from lib.parse import load_all_transactions

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ANALYSIS_DIR = PROJECT_ROOT / "data" / "analysis"
PROFILE_PATH = ANALYSIS_DIR / "spending-profile.yml"


###############################################################################
# HELPER FUNCTIONS
###############################################################################


def _filter_recent_months(df: pd.DataFrame, months: int) -> pd.DataFrame:
    """Filter DataFrame to transactions within the last N months."""
    cutoff = datetime.now() - relativedelta(months=months)
    return df.loc[df["date"] >= cutoff].copy()


def _compute_category_totals(
    df: pd.DataFrame, months_actual: int
) -> dict[str, dict]:
    """Aggregate spend by category with monthly averages and percentages."""
    total_spend = df["amount"].sum()
    grouped = df.groupby("category").agg(
        total=("amount", "sum"),
        txn_count=("amount", "count"),
    )
    result: dict[str, dict] = {}
    for cat, row in grouped.sort_values("total", ascending=False).iterrows():
        result[cat] = {
            "total": round(float(row["total"]), 2),
            "monthly_avg": round(float(row["total"]) / months_actual, 2),
            "pct": round(float(row["total"]) / total_spend * 100, 1) if total_spend else 0.0,
            "txn_count": int(row["txn_count"]),
        }
    return result


def _compute_card_breakdown(
    df: pd.DataFrame, months_actual: int
) -> dict[str, dict]:
    """Aggregate spend by card slug."""
    grouped = df.groupby("card").agg(
        total=("amount", "sum"),
        txn_count=("amount", "count"),
    )
    result: dict[str, dict] = {}
    for card, row in grouped.sort_values("total", ascending=False).iterrows():
        result[card] = {
            "total": round(float(row["total"]), 2),
            "monthly_avg": round(float(row["total"]) / months_actual, 2),
            "txn_count": int(row["txn_count"]),
        }
    return result


def _compute_cardholder_breakdown(df: pd.DataFrame) -> dict[str, dict]:
    """Aggregate spend by cardholder."""
    if "cardholder" not in df.columns:
        return {}
    grouped = df.groupby("cardholder").agg(
        total=("amount", "sum"),
        txn_count=("amount", "count"),
    )
    result: dict[str, dict] = {}
    for holder, row in grouped.sort_values("total", ascending=False).iterrows():
        result[holder] = {
            "total": round(float(row["total"]), 2),
            "txn_count": int(row["txn_count"]),
        }
    return result


def _compute_top_merchants(df: pd.DataFrame, top_n: int = 20) -> dict[str, dict]:
    """Top N merchants by total spend with average transaction size."""
    grouped = df.groupby("merchant").agg(
        total=("amount", "sum"),
        txn_count=("amount", "count"),
    )
    top = grouped.sort_values("total", ascending=False).head(top_n)
    result: dict[str, dict] = {}
    for merchant, row in top.iterrows():
        result[merchant] = {
            "total": round(float(row["total"]), 2),
            "txn_count": int(row["txn_count"]),
            "avg_txn": round(float(row["total"]) / int(row["txn_count"]), 2),
        }
    return result


def _count_actual_months(df: pd.DataFrame) -> int:
    """Count distinct calendar months present in the data."""
    if df.empty:
        return 0
    periods = df["date"].dt.to_period("M")
    return int(periods.nunique())


###############################################################################
# MAIN FUNCTIONS
###############################################################################


def build_spending_profile(months: int = 12) -> dict:
    """Build a full spending profile from parsed transaction data.

    Loads all parquet transactions, filters to the most recent N months,
    and produces category totals, card breakdown, cardholder breakdown,
    and top 20 merchants. Saves the result as YAML.

    Args:
        months: Number of months to look back from today.

    Returns:
        Structured dict with period, totals, categories, cards, and merchants.
    """
    df_all = load_all_transactions()
    df = _filter_recent_months(df_all, months)

    if df.empty:
        print(f"WARNING: No transactions found in the last {months} months.")
        return {}

    months_actual = _count_actual_months(df)
    total_spend = round(float(df["amount"].sum()), 2)
    date_min = df["date"].min().strftime("%Y-%m-%d")
    date_max = df["date"].max().strftime("%Y-%m-%d")

    profile: dict = {
        "period": f"{date_min} to {date_max}",
        "months_analyzed": months_actual,
        "total_spend": total_spend,
        "monthly_avg": round(total_spend / months_actual, 2) if months_actual else 0.0,
        "categories": _compute_category_totals(df, months_actual),
        "by_card": _compute_card_breakdown(df, months_actual),
        "by_cardholder": _compute_cardholder_breakdown(df),
        "top_merchants": _compute_top_merchants(df, top_n=20),
    }

    ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)
    with open(PROFILE_PATH, "w", encoding="utf-8") as f:
        yaml.dump(profile, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
    print(f"Spending profile saved to {PROFILE_PATH}")

    return profile


def print_spending_summary(profile: dict | None = None) -> None:
    """Print a formatted spending summary to the console.

    If no profile is provided, builds one via build_spending_profile().

    Args:
        profile: Pre-built spending profile dict, or None to generate fresh.
    """
    if profile is None:
        profile = build_spending_profile()

    if not profile:
        print("No spending data available.")
        return

    print(f"\n{'=' * 70}")
    print(f"  SPENDING PROFILE  |  {profile['period']}")
    print(f"  {profile['months_analyzed']} months  |  ${profile['total_spend']:,.2f} total  |  ${profile['monthly_avg']:,.2f}/mo")
    print(f"{'=' * 70}")

    # -- Category breakdown --
    print(f"\n{'CATEGORY':<25} {'MONTHLY AVG':>12} {'PCT':>7} {'TXN COUNT':>10}")
    print(f"{'-' * 25} {'-' * 12} {'-' * 7} {'-' * 10}")
    for cat, stats in profile.get("categories", {}).items():
        print(
            f"{cat:<25} ${stats['monthly_avg']:>10,.2f} {stats['pct']:>6.1f}% {stats['txn_count']:>10,}"
        )

    # -- Card breakdown --
    print(f"\n{'CARD':<25} {'MONTHLY AVG':>12} {'TOTAL':>12} {'TXN COUNT':>10}")
    print(f"{'-' * 25} {'-' * 12} {'-' * 12} {'-' * 10}")
    for card, stats in profile.get("by_card", {}).items():
        print(
            f"{card:<25} ${stats['monthly_avg']:>10,.2f} ${stats['total']:>10,.2f} {stats['txn_count']:>10,}"
        )

    # -- Top 10 merchants --
    print(f"\n{'MERCHANT':<30} {'TOTAL':>12} {'AVG TXN':>10} {'TXN COUNT':>10}")
    print(f"{'-' * 30} {'-' * 12} {'-' * 10} {'-' * 10}")
    merchants = list(profile.get("top_merchants", {}).items())[:10]
    for merchant, stats in merchants:
        print(
            f"{merchant:<30} ${stats['total']:>10,.2f} ${stats['avg_txn']:>8,.2f} {stats['txn_count']:>10,}"
        )

    print()
