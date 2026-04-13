# Mode: Portfolio Optimization

## Trigger
User asks to optimize their card portfolio, audit their rewards, find gaps, or after scan detects significant changes.

## Inputs
- Parquets in `data/transactions/`
- `config/profile-chris.yml`, `config/profile-dana.yml`
- `config/household.yml`
- `data/market/current-offers.yml`, `data/market/rule-updates.yml`
- Wiki docs in `docs/`

## Execution Steps

### 1. Check Data Freshness
If new statement files exist in `statements/` that are not yet parsed, prompt: "New statements detected. Run scan first to update the spending database."

### 2. Current Spending Profile
Load or rebuild the spending profile:

```python
from lib.spending import build_spending_profile, print_spending_summary
profile = build_spending_profile(months=12)
print_spending_summary(profile)
```

### 3. Current Rewards + Routing Leaks
Calculate what the current portfolio earns and where money is leaking:

```python
from lib.rewards import calculate_rewards
rewards = calculate_rewards(months=12)
```

Print: current rewards, effective rate, optimal rate, and the leak table (category, current card/rate, best card/rate, annual leak amount).

### 4. Portfolio Scenario Modeling
Run scenarios using the portfolio modeler:

```python
from lib.model import model_scenario, compare_scenarios, _load_current_cards

current_cards = _load_current_cards()
# Build spending dict from profile categories
# Run: current optimized, +1 best card, +2 best cards, +3 best cards
```

For candidate cards, check `data/market/current-offers.yml`. If stale (>30 days), run targeted web searches for the top candidates and update the cache via `lib/market.py`.

### 5. Eligibility Check
Read both `profile-chris.yml` and `profile-dana.yml` for:
- 5/24 status
- Inquiry counts by bureau
- Issuer-specific status (Amex lifetime bonuses, Citi cards held, etc.)

Cross-reference with `docs/issuer-rules.md` and `data/market/rule-updates.yml`.

### 6. Business Card Consideration
If `household.yml` has `side_business.exists: true`, include business card scenarios (Chase Ink Cash, Ink Unlimited, etc.) in the modeling. Note that business cards typically do not count toward 5/24.

### 7. Output
Produce a ranked recommendation with:
1. **Routing fixes** (free, no new cards): which categories to move to which card, annual savings
2. **New card recommendations** ranked by incremental annual value, with signup bonus value
3. **Application sequence** considering issuer velocity rules and bureau management
4. **Dollar math** for every recommendation (current vs proposed, annual delta)

### 8. Clear Change Flags
After completing the review, clear `data/analysis/change-flags.yml` by setting `requires_full_reanalysis: false`.
