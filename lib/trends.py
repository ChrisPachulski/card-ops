"""
Trend detection and change-flag analysis for credit card transactions.

Compares trailing 3-month window to prior 3-month baseline and flags
significant spending shifts, new recurring merchants, geographic changes,
and BCP grocery cap warnings.
"""

from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import yaml

from lib.parse import load_all_transactions


###############################################################################
# Constants
###############################################################################

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_OUTPUT_PATH = _PROJECT_ROOT / "data" / "analysis" / "change-flags.yml"

_BCP_GROCERY_ANNUAL_CAP = 6000
_TOP_N_CATEGORIES = 5


###############################################################################
# Period Helpers
###############################################################################

def _period_bounds(
    now: datetime | None = None,
) -> tuple[pd.Timestamp, pd.Timestamp, pd.Timestamp]:
    """
    Return (baseline_start, split_point, current_end) for a 6-month window.

    current_period = [split_point, current_end]
    baseline_period = [baseline_start, split_point)
    """
    ref = now or datetime.now()
    current_end = pd.Timestamp(ref)
    split_point = pd.Timestamp(ref - timedelta(days=90))
    baseline_start = pd.Timestamp(ref - timedelta(days=180))
    return baseline_start, split_point, current_end


def _split_periods(
    df: pd.DataFrame,
    now: datetime | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Split transactions into baseline and current period DataFrames."""
    baseline_start, split_point, current_end = _period_bounds(now)
    mask_baseline = (df["date"] >= baseline_start) & (df["date"] < split_point)
    mask_current = (df["date"] >= split_point) & (df["date"] <= current_end)
    return df[mask_baseline].copy(), df[mask_current].copy()


def _period_label(dt: pd.Timestamp) -> str:
    """Format a timestamp as YYYY-MM for display."""
    return dt.strftime("%Y-%m")


###############################################################################
# Detection: Category Spend Shifts
###############################################################################

def _category_totals(df: pd.DataFrame) -> dict[str, float]:
    """Sum spending by category."""
    if df.empty:
        return {}
    return df.groupby("category")["amount"].sum().to_dict()


def _detect_category_shifts(
    df_baseline: pd.DataFrame,
    df_current: pd.DataFrame,
) -> list[dict]:
    """Flag categories with >25% spend change in top-5 categories."""
    base_totals = _category_totals(df_baseline)
    curr_totals = _category_totals(df_current)

    # top-5 by combined spend across both periods
    all_cats: dict[str, float] = {}
    for cat, amt in base_totals.items():
        all_cats[cat] = all_cats.get(cat, 0) + amt
    for cat, amt in curr_totals.items():
        all_cats[cat] = all_cats.get(cat, 0) + amt

    top_cats = sorted(all_cats, key=lambda c: all_cats[c], reverse=True)[
        :_TOP_N_CATEGORIES
    ]

    flags = []
    for cat in top_cats:
        base_amt = base_totals.get(cat, 0)
        curr_amt = curr_totals.get(cat, 0)
        if base_amt == 0:
            if curr_amt > 0:
                pct_change = 1.0  # new category -- treat as 100% increase
            else:
                continue
        else:
            pct_change = (curr_amt - base_amt) / base_amt

        if abs(pct_change) <= 0.25:
            continue

        severity = "high" if abs(pct_change) > 0.50 else "medium"
        direction = "increased" if pct_change > 0 else "decreased"
        flags.append({
            "type": "category_shift",
            "severity": severity,
            "category": cat,
            "baseline_amount": round(base_amt, 2),
            "current_amount": round(curr_amt, 2),
            "pct_change": round(pct_change * 100, 1),
            "direction": direction,
            "description": (
                f"{cat} spending {direction} {abs(round(pct_change * 100, 1))}% "
                f"(${round(base_amt, 2)} -> ${round(curr_amt, 2)})"
            ),
        })

    return flags


###############################################################################
# Detection: New Recurring Merchants
###############################################################################

def _merchant_counts(df: pd.DataFrame) -> dict[str, int]:
    """Count occurrences per merchant."""
    if df.empty:
        return {}
    return df["merchant"].value_counts().to_dict()


def _merchant_monthly_spend(
    df: pd.DataFrame,
    merchant: str,
) -> float:
    """Estimate monthly spend for a merchant over a 3-month window."""
    total = df.loc[df["merchant"] == merchant, "amount"].sum()
    return round(total / 3, 2)


def _detect_new_recurring(
    df_baseline: pd.DataFrame,
    df_current: pd.DataFrame,
) -> list[dict]:
    """Flag merchants appearing 3+ times in current but absent from baseline."""
    base_merchants = set(df_baseline["merchant"].unique()) if not df_baseline.empty else set()
    curr_counts = _merchant_counts(df_current)

    flags = []
    for merchant, count in curr_counts.items():
        if count < 3:
            continue
        if merchant in base_merchants:
            continue

        monthly = _merchant_monthly_spend(df_current, merchant)
        if monthly > 500:
            severity = "high"
        elif monthly > 100:
            severity = "medium"
        else:
            severity = "low"

        flags.append({
            "type": "new_recurring",
            "severity": severity,
            "merchant": merchant,
            "occurrences": count,
            "est_monthly_spend": monthly,
            "description": (
                f"New recurring merchant: {merchant} "
                f"({count} charges, ~${monthly}/mo)"
            ),
        })

    return flags


###############################################################################
# Detection: Geographic Shift
###############################################################################

def _detect_geographic_shift(
    df_baseline: pd.DataFrame,
    df_current: pd.DataFrame,
) -> list[dict]:
    """Flag if >50% of current transactions are in a new state."""
    def state_distribution(df: pd.DataFrame) -> dict[str, int]:
        states = df["merchant_state"].dropna()
        states = states[states != ""]
        if states.empty:
            return {}
        return states.value_counts().to_dict()

    base_states = state_distribution(df_baseline)
    curr_states = state_distribution(df_current)

    if not curr_states:
        return []

    total_current = sum(curr_states.values())
    base_state_set = set(base_states.keys())

    flags = []
    for state, count in curr_states.items():
        share = count / total_current
        if share > 0.50 and state not in base_state_set:
            flags.append({
                "type": "relocation",
                "severity": "high",
                "new_state": state,
                "share_of_transactions": round(share * 100, 1),
                "description": (
                    f"Possible relocation: {round(share * 100, 1)}% of "
                    f"transactions in {state} (not seen in baseline)"
                ),
            })

    return flags


###############################################################################
# Detection: BCP Grocery Cap Warning
###############################################################################

def _detect_bcp_grocery_cap(
    df: pd.DataFrame,
    now: datetime | None = None,
) -> list[dict]:
    """Warn if YTD grocery spend on amex-bcp approaches the $6K annual cap."""
    ref = now or datetime.now()
    year_start = pd.Timestamp(datetime(ref.year, 1, 1))

    mask = (
        (df["card"] == "amex-bcp")
        & (df["category"] == "Groceries")
        & (df["date"] >= year_start)
    )
    ytd_grocery = df.loc[mask, "amount"].sum()

    if ytd_grocery < _BCP_GROCERY_ANNUAL_CAP * 0.75:
        return []

    remaining = max(_BCP_GROCERY_ANNUAL_CAP - ytd_grocery, 0)
    months_left = max(12 - ref.month, 1)
    monthly_budget = round(remaining / months_left, 2)

    return [{
        "type": "cap_warning",
        "severity": "medium",
        "card": "amex-bcp",
        "category": "Groceries",
        "ytd_spend": round(ytd_grocery, 2),
        "annual_cap": _BCP_GROCERY_ANNUAL_CAP,
        "remaining": round(remaining, 2),
        "monthly_budget_remaining": monthly_budget,
        "description": (
            f"BCP grocery cap: ${round(ytd_grocery, 2)} of "
            f"${_BCP_GROCERY_ANNUAL_CAP} YTD "
            f"(${round(remaining, 2)} remaining, ~${monthly_budget}/mo budget)"
        ),
    }]


###############################################################################
# Output
###############################################################################

def _save_yaml(result: dict, path: Path) -> None:
    """Write change-flag report to YAML."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.dump(result, default_flow_style=False, sort_keys=False))


###############################################################################
# Public API
###############################################################################

def detect_changes(now: datetime | None = None) -> dict:
    """
    Compare trailing 3 months to prior 3 months and flag significant shifts.

    Parameters
    ----------
    now : datetime | None
        Reference date. Defaults to today.

    Returns
    -------
    dict
        Report with keys: generated, baseline_period, current_period,
        flags (list of flag dicts), requires_full_reanalysis (bool).
    """
    ref = now or datetime.now()
    df_all = load_all_transactions()

    if df_all.empty:
        baseline_start, split_point, current_end = _period_bounds(ref)
        return {
            "generated": ref.strftime("%Y-%m-%d"),
            "baseline_period": f"{_period_label(baseline_start)} to {_period_label(split_point)}",
            "current_period": f"{_period_label(split_point)} to {_period_label(current_end)}",
            "flags": [],
            "requires_full_reanalysis": False,
        }

    df_baseline, df_current = _split_periods(df_all, now=ref)
    baseline_start, split_point, current_end = _period_bounds(ref)

    flags: list[dict] = []
    flags.extend(_detect_category_shifts(df_baseline, df_current))
    flags.extend(_detect_new_recurring(df_baseline, df_current))
    flags.extend(_detect_geographic_shift(df_baseline, df_current))
    flags.extend(_detect_bcp_grocery_cap(df_all, now=ref))

    has_high = any(f["severity"] == "high" for f in flags)

    result = {
        "generated": ref.strftime("%Y-%m-%d"),
        "baseline_period": (
            f"{_period_label(baseline_start)} to {_period_label(split_point)}"
        ),
        "current_period": (
            f"{_period_label(split_point)} to {_period_label(current_end)}"
        ),
        "flags": flags,
        "requires_full_reanalysis": has_high,
    }

    _save_yaml(result, _OUTPUT_PATH)
    return result
