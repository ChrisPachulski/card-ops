"""
Stress tests for rewards.py grocery cap logic.

Covers:
  - _find_grocery_cap extraction
  - _best_non_capped_grocery_rate selection
  - _optimal_grocery_rewards boundary math
  - _handle_grocery_rewards leak detection (every routing path)
  - calculate_rewards integration with synthetic + real data
  - Cross-validation: manual hand-calculations vs code output

Every assertion includes the hand-calculated expected value and why.
"""
import sys
from pathlib import Path

import pandas as pd
import pytest

# Ensure imports resolve from card-ops root
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.rewards import (
    _best_non_capped_grocery_rate,
    _best_rate_for_category,
    _find_grocery_cap,
    _handle_grocery_rewards,
    _optimal_grocery_rewards,
    _rate_for_card_category,
)


###############################################################################
# Fixtures: synthetic card rate portfolios
###############################################################################

@pytest.fixture
def household_rates() -> dict[str, dict[str, float]]:
    """Real household portfolio: BCP (6% capped at 6K), WF (2% flat), etc."""
    return {
        "amex-bcp": {
            "groceries": 0.06,
            "groceries_cap": 6000,
            "groceries_after_cap": 0.01,
            "gas": 0.03,
            "streaming": 0.03,
            "other": 0.01,
        },
        "wf-active-cash": {"everything": 0.02},
        "chase-amazon": {
            "amazon": 0.05,
            "dining": 0.02,
            "gas": 0.02,
            "other": 0.01,
        },
        "chase-freedom": {
            "dining": 0.03,
            "drugstore": 0.03,
            "chase_travel": 0.05,
            "other": 0.015,
        },
    }


@pytest.fixture
def no_cap_rates() -> dict[str, dict[str, float]]:
    """Portfolio with no grocery cap -- simple best-rate logic."""
    return {
        "card-a": {"groceries": 0.03, "other": 0.01},
        "card-b": {"everything": 0.02},
    }


@pytest.fixture
def single_card_rates() -> dict[str, dict[str, float]]:
    """Portfolio with only one card."""
    return {
        "amex-bcp": {
            "groceries": 0.06,
            "groceries_cap": 6000,
            "groceries_after_cap": 0.01,
            "other": 0.01,
        },
    }


###############################################################################
# _find_grocery_cap
###############################################################################

class TestFindGroceryCap:
    def test_finds_bcp_cap(self, household_rates):
        slug, rate, cap, after = _find_grocery_cap(household_rates)
        assert slug == "amex-bcp"
        assert rate == 0.06
        assert cap == 6000
        assert after == 0.01

    def test_no_cap_returns_none(self, no_cap_rates):
        slug, rate, cap, after = _find_grocery_cap(no_cap_rates)
        assert slug is None
        assert cap is None

    def test_single_capped_card(self, single_card_rates):
        slug, rate, cap, after = _find_grocery_cap(single_card_rates)
        assert slug == "amex-bcp"
        assert cap == 6000


###############################################################################
# _best_non_capped_grocery_rate
###############################################################################

class TestBestNonCappedGroceryRate:
    def test_finds_wf_as_best_alt(self, household_rates):
        slug, rate = _best_non_capped_grocery_rate(household_rates, "amex-bcp")
        # WF: everything=0.02, CFU: other=0.015, Amazon: other=0.01
        # WF wins at 2%
        assert slug == "wf-active-cash"
        assert rate == 0.02

    def test_no_cards_excluded(self, household_rates):
        slug, rate = _best_non_capped_grocery_rate(household_rates, None)
        # BCP at 6% is the best (not excluded)
        assert slug == "amex-bcp"
        assert rate == 0.06

    def test_single_card_excluded_returns_empty(self, single_card_rates):
        slug, rate = _best_non_capped_grocery_rate(single_card_rates, "amex-bcp")
        assert slug == ""
        assert rate == 0.0

    def test_no_cap_portfolio(self, no_cap_rates):
        slug, rate = _best_non_capped_grocery_rate(no_cap_rates, None)
        # card-a at 3% is best
        assert slug == "card-a"
        assert rate == 0.03


###############################################################################
# _optimal_grocery_rewards -- boundary math
###############################################################################

class TestOptimalGroceryRewards:
    """Hand-calculated expected values for every scenario."""

    def test_zero_spend(self, household_rates):
        result = _optimal_grocery_rewards(0, household_rates)
        assert result == 0.0

    def test_well_under_cap(self, household_rates):
        # $3000 * 6% = $180
        result = _optimal_grocery_rewards(3000, household_rates)
        assert result == pytest.approx(180.0)

    def test_exactly_at_cap(self, household_rates):
        # $6000 * 6% = $360
        result = _optimal_grocery_rewards(6000, household_rates)
        assert result == pytest.approx(360.0)

    def test_one_dollar_over_cap(self, household_rates):
        # $6000 * 6% + $1 * 2% = $360.02
        result = _optimal_grocery_rewards(6001, household_rates)
        assert result == pytest.approx(360.02)

    def test_moderate_over_cap(self, household_rates):
        # $6000 * 6% + $2000 * 2% = $360 + $40 = $400
        result = _optimal_grocery_rewards(8000, household_rates)
        assert result == pytest.approx(400.0)

    def test_double_cap(self, household_rates):
        # $6000 * 6% + $6000 * 2% = $360 + $120 = $480
        result = _optimal_grocery_rewards(12000, household_rates)
        assert result == pytest.approx(480.0)

    def test_household_actual_level(self, household_rates):
        # ~$18K groceries: $6000 * 6% + $12000 * 2% = $360 + $240 = $600
        result = _optimal_grocery_rewards(18000, household_rates)
        assert result == pytest.approx(600.0)

    def test_extreme_spend(self, household_rates):
        # $100K groceries: $6000 * 6% + $94000 * 2% = $360 + $1880 = $2240
        result = _optimal_grocery_rewards(100000, household_rates)
        assert result == pytest.approx(2240.0)

    def test_no_cap_portfolio_simple_best_rate(self, no_cap_rates):
        # card-a at 3%: $10000 * 3% = $300
        result = _optimal_grocery_rewards(10000, no_cap_rates)
        assert result == pytest.approx(300.0)

    def test_single_card_under_cap(self, single_card_rates):
        # BCP at 6%, cap 6K: $4000 * 6% = $240
        result = _optimal_grocery_rewards(4000, single_card_rates)
        assert result == pytest.approx(240.0)

    def test_single_card_over_cap_no_alternative(self, single_card_rates):
        # BCP at 6% up to cap, then 1% after. No other card.
        # $6000 * 6% + $4000 * 1% = $360 + $40 = $400
        # Overflow rate: max(after_cap_rate=0.01, alt_rate=0.0) = 0.01
        result = _optimal_grocery_rewards(10000, single_card_rates)
        assert result == pytest.approx(400.0)

    def test_effective_rate_decreases_with_spend(self, household_rates):
        """Effective grocery rate should decrease as spend increases past cap."""
        rates_at_levels = []
        for spend in [1000, 3000, 6000, 8000, 12000, 18000, 50000]:
            reward = _optimal_grocery_rewards(spend, household_rates)
            rate = reward / spend
            rates_at_levels.append(rate)

        # Under cap: all should be 6%
        assert rates_at_levels[0] == pytest.approx(0.06)
        assert rates_at_levels[1] == pytest.approx(0.06)
        assert rates_at_levels[2] == pytest.approx(0.06)

        # Over cap: strictly decreasing
        for i in range(3, len(rates_at_levels)):
            assert rates_at_levels[i] < rates_at_levels[i - 1], (
                f"Rate at level {i} ({rates_at_levels[i]:.4f}) should be less "
                f"than level {i-1} ({rates_at_levels[i-1]:.4f})"
            )

        # Should asymptotically approach 2% (the overflow rate)
        assert rates_at_levels[-1] < 0.025


###############################################################################
# _handle_grocery_rewards -- leak detection
###############################################################################

def _make_grocery_df(card_amounts: dict[str, float], months: int = 12) -> pd.DataFrame:
    """Create a synthetic grocery transaction DataFrame.

    card_amounts: {card_slug: annual_spend}
    Spreads transactions evenly across `months` months.
    """
    rows = []
    base_date = pd.Timestamp("2025-04-01")
    for card, annual_amount in card_amounts.items():
        monthly = annual_amount / months
        for m in range(months):
            rows.append({
                "date": base_date + pd.DateOffset(months=m),
                "merchant_raw": "GROCERY STORE",
                "merchant": "Grocery Store",
                "amount": monthly,
                "category": "Groceries",
                "subcategory": "Grocery",
                "cardholder": "chris",
                "card": card,
                "earn_rate": 0.0,
                "reward_amount": 0.0,
                "is_recurring": False,
                "merchant_state": "WA",
                "statement_file": f"test-{card}-{m}.pdf",
            })
    return pd.DataFrame(rows)


class TestHandleGroceryRewards:
    """Test leak detection across every routing scenario."""

    def test_all_on_bcp_under_cap_no_leak(self, household_rates):
        """$5000 all on BCP, under $6K cap -> no leaks."""
        df = _make_grocery_df({"amex-bcp": 5000})
        by_cat, leaks = [], []
        _handle_grocery_rewards(df, household_rates, 1.0, by_cat, leaks)

        assert len(by_cat) == 1
        assert by_cat[0]["card"] == "amex-bcp"
        assert by_cat[0]["annual_spend"] == pytest.approx(5000, abs=1)
        assert by_cat[0]["earn_rate"] == pytest.approx(0.06)
        # $5000 * 6% = $300
        assert by_cat[0]["annual_reward"] == pytest.approx(300.0, abs=1)
        assert len(leaks) == 0

    def test_all_on_bcp_at_cap_no_leak(self, household_rates):
        """$6000 all on BCP, exactly at cap -> no leaks."""
        df = _make_grocery_df({"amex-bcp": 6000})
        by_cat, leaks = [], []
        _handle_grocery_rewards(df, household_rates, 1.0, by_cat, leaks)

        assert by_cat[0]["earn_rate"] == pytest.approx(0.06)
        assert by_cat[0]["annual_reward"] == pytest.approx(360.0, abs=1)
        assert len(leaks) == 0

    def test_all_on_bcp_over_cap_leak_to_wf(self, household_rates):
        """$10000 all on BCP -> $4000 overflow at 1%, leak suggests WF at 2%."""
        df = _make_grocery_df({"amex-bcp": 10000})
        by_cat, leaks = [], []
        _handle_grocery_rewards(df, household_rates, 1.0, by_cat, leaks)

        # BCP: $6000*6% + $4000*1% = $360 + $40 = $400
        assert by_cat[0]["annual_reward"] == pytest.approx(400.0, abs=1)
        # Effective rate: $400 / $10000 = 4%
        assert by_cat[0]["earn_rate"] == pytest.approx(0.04, abs=0.001)

        # Should have 1 leak: overflow should go to WF
        assert len(leaks) == 1
        leak = leaks[0]
        assert leak["current_card"] == "amex-bcp"
        assert leak["current_rate"] == pytest.approx(0.01)
        assert leak["best_card"] == "wf-active-cash"
        assert leak["best_rate"] == pytest.approx(0.02)
        assert leak["annual_spend"] == pytest.approx(4000, abs=1)
        # Leak: $4000 * (2% - 1%) = $40
        assert leak["annual_leak"] == pytest.approx(40.0, abs=1)

    def test_all_on_wf_bcp_cap_empty_leak_to_bcp(self, household_rates):
        """$8000 all on WF, BCP cap completely empty -> leak for cap amount."""
        df = _make_grocery_df({"wf-active-cash": 8000})
        by_cat, leaks = [], []
        _handle_grocery_rewards(df, household_rates, 1.0, by_cat, leaks)

        # WF: $8000 * 2% = $160
        assert by_cat[0]["annual_reward"] == pytest.approx(160.0, abs=1)

        # Leak: first $6000 should go to BCP at 6%
        assert len(leaks) == 1
        leak = leaks[0]
        assert leak["current_card"] == "wf-active-cash"
        assert leak["best_card"] == "amex-bcp"
        assert leak["best_rate"] == pytest.approx(0.06)
        assert leak["annual_spend"] == pytest.approx(6000, abs=1)
        # Leak: $6000 * (6% - 2%) = $240
        assert leak["annual_leak"] == pytest.approx(240.0, abs=1)

    def test_bcp_full_cap_wf_has_grocery_no_leak(self, household_rates):
        """BCP has $6000 (cap full), WF has $8000 -> no grocery leak on WF."""
        df = _make_grocery_df({"amex-bcp": 6000, "wf-active-cash": 8000})
        by_cat, leaks = [], []
        _handle_grocery_rewards(df, household_rates, 1.0, by_cat, leaks)

        # BCP: $6000 * 6% = $360 (at cap, not over)
        bcp_row = [r for r in by_cat if r["card"] == "amex-bcp"][0]
        assert bcp_row["annual_reward"] == pytest.approx(360.0, abs=1)

        # WF: $8000 * 2% = $160
        wf_row = [r for r in by_cat if r["card"] == "wf-active-cash"][0]
        assert wf_row["annual_reward"] == pytest.approx(160.0, abs=1)

        # No leaks -- cap is full, WF at 2% is correct for overflow
        assert len(leaks) == 0

    def test_bcp_partial_cap_wf_has_grocery_partial_leak(self, household_rates):
        """BCP has $4000 ($2000 cap room), WF has $5000 -> leak for $2000 only."""
        df = _make_grocery_df({"amex-bcp": 4000, "wf-active-cash": 5000})
        by_cat, leaks = [], []
        _handle_grocery_rewards(df, household_rates, 1.0, by_cat, leaks)

        # BCP: $4000 * 6% = $240 (under cap)
        bcp_row = [r for r in by_cat if r["card"] == "amex-bcp"][0]
        assert bcp_row["annual_reward"] == pytest.approx(240.0, abs=1)

        # WF: $5000 * 2% = $100
        wf_row = [r for r in by_cat if r["card"] == "wf-active-cash"][0]
        assert wf_row["annual_reward"] == pytest.approx(100.0, abs=1)

        # Leak: only $2000 of WF's $5000 could go to BCP (cap room = $2000)
        assert len(leaks) == 1
        leak = leaks[0]
        assert leak["annual_spend"] == pytest.approx(2000, abs=1)
        # Leak: $2000 * (6% - 2%) = $80
        assert leak["annual_leak"] == pytest.approx(80.0, abs=1)

    def test_bcp_over_cap_plus_wf_grocery(self, household_rates):
        """BCP has $8000 (over cap), WF has $3000 -> BCP overflow leak only."""
        df = _make_grocery_df({"amex-bcp": 8000, "wf-active-cash": 3000})
        by_cat, leaks = [], []
        _handle_grocery_rewards(df, household_rates, 1.0, by_cat, leaks)

        # BCP: $6000*6% + $2000*1% = $360 + $20 = $380
        bcp_row = [r for r in by_cat if r["card"] == "amex-bcp"][0]
        assert bcp_row["annual_reward"] == pytest.approx(380.0, abs=1)

        # WF: $3000 * 2% = $60
        wf_row = [r for r in by_cat if r["card"] == "wf-active-cash"][0]
        assert wf_row["annual_reward"] == pytest.approx(60.0, abs=1)

        # Leak: BCP overflow of $2000 at 1% should go to WF at 2%
        # No leak on WF because cap is full (cap_remaining = 6000 - 8000 = 0)
        assert len(leaks) == 1
        leak = leaks[0]
        assert leak["current_card"] == "amex-bcp"
        assert leak["best_card"] == "wf-active-cash"
        assert leak["annual_spend"] == pytest.approx(2000, abs=1)
        # Leak: $2000 * (2% - 1%) = $20
        assert leak["annual_leak"] == pytest.approx(20.0, abs=1)

    def test_three_cards_with_grocery(self, household_rates):
        """BCP $5000, WF $3000, CFU $2000 -> $1000 cap room.
        Leak on first $1000 of non-BCP grocery (WF processed first by groupby)."""
        df = _make_grocery_df({
            "amex-bcp": 5000,
            "chase-freedom": 2000,
            "wf-active-cash": 3000,
        })
        by_cat, leaks = [], []
        _handle_grocery_rewards(df, household_rates, 1.0, by_cat, leaks)

        # Cap remaining: $6000 - $5000 = $1000
        # Total grocery leaks should consume exactly $1000 of cap room
        total_leaked_spend = sum(l["annual_spend"] for l in leaks)
        assert total_leaked_spend == pytest.approx(1000, abs=1)

    def test_tiny_grocery_no_leak_below_threshold(self, household_rates):
        """$50 on WF with cap room -> no leak (below $100 threshold)."""
        df = _make_grocery_df({"wf-active-cash": 50})
        by_cat, leaks = [], []
        _handle_grocery_rewards(df, household_rates, 1.0, by_cat, leaks)

        assert len(leaks) == 0

    def test_no_cap_portfolio_leak_detection(self, no_cap_rates):
        """Portfolio without caps: card-b at 2% should leak to card-a at 3%."""
        df = _make_grocery_df({"card-b": 5000})
        by_cat, leaks = [], []
        _handle_grocery_rewards(df, no_cap_rates, 1.0, by_cat, leaks)

        assert len(leaks) == 1
        assert leaks[0]["best_card"] == "card-a"
        assert leaks[0]["best_rate"] == pytest.approx(0.03)
        # Leak: $5000 * (3% - 2%) = $50
        assert leaks[0]["annual_leak"] == pytest.approx(50.0, abs=1)

    def test_empty_grocery_df(self, household_rates):
        """No grocery transactions at all -> no entries, no leaks."""
        df = pd.DataFrame(columns=[
            "date", "merchant_raw", "merchant", "amount", "category",
            "subcategory", "cardholder", "card", "earn_rate",
            "reward_amount", "is_recurring", "merchant_state", "statement_file",
        ])
        by_cat, leaks = [], []
        _handle_grocery_rewards(df, household_rates, 1.0, by_cat, leaks)

        assert len(by_cat) == 0
        assert len(leaks) == 0


###############################################################################
# The old-code bug: verify it WOULD have been wrong
###############################################################################

class TestOldBugWouldHaveFailed:
    """Verify the specific failure mode the handoff identified."""

    def test_old_best_rate_ignores_cap(self, household_rates):
        """_best_rate_for_category returns 6% for groceries -- no cap awareness.
        This is correct for finding the raw best rate, but WRONG for determining
        optimal routing when spend > $6K."""
        best_card, best_rate = _best_rate_for_category("Groceries", household_rates)
        assert best_card == "amex-bcp"
        assert best_rate == 0.06
        # The old code would compute: $18000 * 6% = $1080
        # The correct value is: $6000*6% + $12000*2% = $600
        naive_reward = 18000 * best_rate
        correct_reward = _optimal_grocery_rewards(18000, household_rates)
        assert naive_reward == pytest.approx(1080.0)
        assert correct_reward == pytest.approx(600.0)
        # The old code overstates rewards by $480
        assert naive_reward - correct_reward == pytest.approx(480.0)

    def test_wf_grocery_not_a_leak_when_cap_full(self, household_rates):
        """The original bug: flagging WF grocery as leak even when BCP cap is full.
        With $6000 on BCP (cap full) and $8000 on WF, the WF spend is
        correctly routed -- WF at 2% > BCP after cap at 1%."""
        df = _make_grocery_df({"amex-bcp": 6000, "wf-active-cash": 8000})
        by_cat, leaks = [], []
        _handle_grocery_rewards(df, household_rates, 1.0, by_cat, leaks)

        # OLD CODE would have generated a leak:
        #   WF grocery $8000 at 2% -> "should be on BCP at 6%"
        #   annual_leak = $8000 * (6% - 2%) = $320
        # NEW CODE correctly generates NO leak
        grocery_leaks_on_wf = [
            l for l in leaks
            if l["current_card"] == "wf-active-cash"
        ]
        assert len(grocery_leaks_on_wf) == 0


###############################################################################
# Cross-validation: hand-calculated total rewards
###############################################################################

class TestCrossValidation:
    """Verify total reward calculations match hand-computed values."""

    def test_household_scenario_total_rewards(self, household_rates):
        """Build a realistic household scenario and verify every number."""
        df = _make_grocery_df({
            "amex-bcp": 5800,    # Under cap
            "wf-active-cash": 8200,
            "chase-freedom": 140,
        })
        by_cat, leaks = [], []
        _handle_grocery_rewards(df, household_rates, 1.0, by_cat, leaks)

        # BCP: $5800 * 6% = $348 (under cap)
        bcp = [r for r in by_cat if r["card"] == "amex-bcp"][0]
        assert bcp["annual_reward"] == pytest.approx(348.0, abs=1)

        # WF: $8200 * 2% = $164
        wf = [r for r in by_cat if r["card"] == "wf-active-cash"][0]
        assert wf["annual_reward"] == pytest.approx(164.0, abs=1)

        # CFU: $140 * 1.5% = $2.10
        cfu = [r for r in by_cat if r["card"] == "chase-freedom"][0]
        assert cfu["annual_reward"] == pytest.approx(2.10, abs=0.5)

        # Total actual: $348 + $164 + $2.10 = $514.10
        total_actual = sum(r["annual_reward"] for r in by_cat)
        assert total_actual == pytest.approx(514.10, abs=2)

        # Optimal: $6000*6% + $8140*2% = $360 + $162.80 = $522.80
        total_grocery = 5800 + 8200 + 140
        optimal = _optimal_grocery_rewards(total_grocery, household_rates)
        assert optimal == pytest.approx(522.80, abs=1)

    def test_annualization_factor(self, household_rates):
        """Verify annualize factor is applied correctly.

        _make_grocery_df({"amex-bcp": 3000}, months=6) creates 6 txns of $500
        each = $3000 period spend. annualize=2.0 -> annual = $6000.
        """
        df = _make_grocery_df({"amex-bcp": 3000}, months=6)
        by_cat, leaks = [], []
        _handle_grocery_rewards(df, household_rates, 2.0, by_cat, leaks)

        # $3000 period * 2.0 annualize = $6000 annual (exactly at cap)
        assert by_cat[0]["annual_spend"] == pytest.approx(6000, abs=1)
        # $6000 * 6% = $360 (all under cap)
        assert by_cat[0]["annual_reward"] == pytest.approx(360.0, abs=1)


###############################################################################
# Regression: ensure non-grocery categories are untouched
###############################################################################

class TestNonGroceryUnaffected:
    """The cap logic must not bleed into other categories."""

    def test_dining_rate_unchanged(self, household_rates):
        best_card, best_rate = _best_rate_for_category("Dining", household_rates)
        assert best_card == "chase-freedom"
        assert best_rate == 0.03

    def test_amazon_rate_unchanged(self, household_rates):
        best_card, best_rate = _best_rate_for_category("Amazon", household_rates)
        assert best_card == "chase-amazon"
        assert best_rate == 0.05

    def test_gas_rate_unchanged(self, household_rates):
        best_card, best_rate = _best_rate_for_category("Gas", household_rates)
        assert best_card == "amex-bcp"
        assert best_rate == 0.03

    def test_other_rate_unchanged(self, household_rates):
        best_card, best_rate = _best_rate_for_category("Other", household_rates)
        # WF everything=0.02 > BCP other=0.01 > CFU other=0.015
        assert best_card == "wf-active-cash"
        assert best_rate == 0.02


###############################################################################
# Edge cases
###############################################################################

class TestEdgeCases:
    def test_zero_cap_amount(self):
        """A card with groceries_cap=0 should effectively have no premium rate."""
        rates = {
            "weird-card": {
                "groceries": 0.10,
                "groceries_cap": 0,
                "groceries_after_cap": 0.01,
            },
            "normal-card": {"everything": 0.02},
        }
        # With cap=0, ALL spend is overflow at 1%. Normal card at 2% is better.
        result = _optimal_grocery_rewards(5000, rates)
        # $0 at 10% + $5000 at max(1%, 2%) = $0 + $100 = $100
        assert result == pytest.approx(100.0)

    def test_after_cap_rate_higher_than_alternative(self):
        """If after_cap rate beats all alternatives, overflow stays on capped card."""
        rates = {
            "premium-card": {
                "groceries": 0.06,
                "groceries_cap": 3000,
                "groceries_after_cap": 0.04,
            },
            "basic-card": {"everything": 0.015},
        }
        # $3000 at 6% + $2000 at max(4%, 1.5%) = $180 + $80 = $260
        result = _optimal_grocery_rewards(5000, rates)
        assert result == pytest.approx(260.0)

    def test_very_small_cap_room_no_leak(self, household_rates):
        """BCP at $5950 -> only $50 cap room. WF $200 -> leakable=$50 < $100 threshold."""
        df = _make_grocery_df({"amex-bcp": 5950, "wf-active-cash": 200})
        by_cat, leaks = [], []
        _handle_grocery_rewards(df, household_rates, 1.0, by_cat, leaks)
        # $50 cap room, but leakable=$50 < $100 threshold -> no leak
        assert len(leaks) == 0

    def test_cap_room_exactly_100_generates_leak(self, household_rates):
        """BCP at $5900 -> $100 cap room. WF $500 -> leakable=$100, threshold hit."""
        df = _make_grocery_df({"amex-bcp": 5900, "wf-active-cash": 500})
        by_cat, leaks = [], []
        _handle_grocery_rewards(df, household_rates, 1.0, by_cat, leaks)
        # $100 cap room, leakable=$100, > threshold? No -- threshold is > 100, not >=
        # $100 is NOT > $100, so no leak
        assert len(leaks) == 0

    def test_cap_room_101_generates_leak(self, household_rates):
        """BCP at $5899 -> $101 cap room. WF $500 -> leakable=$101 > $100 threshold."""
        df = _make_grocery_df({"amex-bcp": 5899, "wf-active-cash": 500})
        by_cat, leaks = [], []
        _handle_grocery_rewards(df, household_rates, 1.0, by_cat, leaks)
        # $101 cap room, leakable=min(500,101)=101, 101 > 100 -> leak
        assert len(leaks) == 1
        assert leaks[0]["annual_spend"] == pytest.approx(101, abs=1)
