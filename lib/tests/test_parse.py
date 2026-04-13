"""Smoke tests for lib/parse.py statement parsers."""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from lib.parse import (
    CARD_PARSERS,
    SCHEMA_COLUMNS,
    _already_parsed,
    _empty_df,
    _extract_state,
    parse_amex_excel,
)


###############################################################################
# Schema Tests
###############################################################################

def test_empty_df_has_correct_columns():
    df = _empty_df()
    assert list(df.columns) == SCHEMA_COLUMNS


def test_empty_df_has_zero_rows():
    df = _empty_df()
    assert len(df) == 0


def test_empty_df_date_is_datetime():
    df = _empty_df()
    assert pd.api.types.is_datetime64_any_dtype(df["date"])


def test_empty_df_amount_is_float64():
    df = _empty_df()
    assert df["amount"].dtype == "float64"


def test_empty_df_is_recurring_is_bool():
    df = _empty_df()
    assert df["is_recurring"].dtype == "bool"


###############################################################################
# Helper Tests
###############################################################################

def test_extract_state_returns_last_two_uppercase():
    assert _extract_state("WALMART SUPERCENTER  WARWICK RI") == "RI"


def test_extract_state_returns_empty_for_no_state():
    assert _extract_state("NETFLIX.COM") == ""


def test_extract_state_returns_empty_for_empty_string():
    assert _extract_state("") == ""


def test_already_parsed_true():
    df = _empty_df()
    df = pd.concat([df, pd.DataFrame([{
        "date": pd.Timestamp("2024-01-01"),
        "merchant_raw": "TEST",
        "merchant": "TEST",
        "amount": 10.0,
        "category": "Other",
        "subcategory": "Uncategorized",
        "cardholder": "chris",
        "card": "test",
        "earn_rate": 0.0,
        "reward_amount": 0.0,
        "is_recurring": False,
        "merchant_state": "",
        "statement_file": "activity.xlsx",
    }])], ignore_index=True)
    assert _already_parsed(df, "activity.xlsx") is True


def test_already_parsed_false_when_empty():
    df = _empty_df()
    assert _already_parsed(df, "activity.xlsx") is False


###############################################################################
# Card Parser Registry
###############################################################################

def test_card_parsers_has_five_entries():
    assert len(CARD_PARSERS) == 5


def test_card_parsers_keys():
    expected = {"amex", "amazon", "freedom", "wells_fargo", "checkings"}
    assert set(CARD_PARSERS.keys()) == expected


###############################################################################
# Amex Excel Parser (requires real file)
###############################################################################

AMEX_DIR = Path(__file__).parent.parent.parent / "statements" / "amex"


@pytest.mark.skipif(
    not list(AMEX_DIR.glob("*.xlsx")) if AMEX_DIR.exists() else True,
    reason="No amex xlsx files found -- skipping live parse test",
)
def test_parse_amex_excel_returns_dataframe():
    xlsx_files = sorted(AMEX_DIR.glob("*.xlsx"))
    df = parse_amex_excel(xlsx_files[0])
    assert isinstance(df, pd.DataFrame)
    assert set(SCHEMA_COLUMNS).issubset(set(df.columns))


@pytest.mark.skipif(
    not list(AMEX_DIR.glob("*.xlsx")) if AMEX_DIR.exists() else True,
    reason="No amex xlsx files found -- skipping live parse test",
)
def test_parse_amex_excel_has_correct_card_id():
    xlsx_files = sorted(AMEX_DIR.glob("*.xlsx"))
    df = parse_amex_excel(xlsx_files[0])
    if not df.empty:
        assert (df["card"] == "amex-bcp").all()


@pytest.mark.skipif(
    not list(AMEX_DIR.glob("*.xlsx")) if AMEX_DIR.exists() else True,
    reason="No amex xlsx files found -- skipping live parse test",
)
def test_parse_amex_excel_no_negative_amounts():
    xlsx_files = sorted(AMEX_DIR.glob("*.xlsx"))
    df = parse_amex_excel(xlsx_files[0])
    if not df.empty:
        assert (df["amount"] >= 0).all()
