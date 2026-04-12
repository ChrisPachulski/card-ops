# Mode: Portfolio Optimization

## Trigger
User asks to optimize their card portfolio, or after enough evaluations to have context.

## Inputs
- `config/profile.yml` (current cards + spending)
- `data/cards.md` (evaluated offers)
- Parsed statement data (if available)

## Execution Steps

### 1. Current Portfolio Audit
For each card in `current_cards`:
- Calculate annual rewards based on current spending assignment
- Calculate perk value (what perks does the user actually redeem?)
- Calculate net value (rewards + perks - annual fee)
- Flag underperforming cards (net value < $0)

### 2. Spending Assignment Optimization
- For each spending category, identify which held card earns the most
- Build optimal spending assignment matrix:

| Category | Monthly Spend | Best Card | Earn Rate | Monthly Rewards |
|----------|---------------|-----------|-----------|-----------------|
| Groceries | $600 | Amex Gold | 4x MR | 2,400 MR |
| Dining | $400 | CSR | 3x UR | 1,200 UR |
| ... | | | | |

### 3. Gap Analysis
- Identify categories earning only 1x (no bonus)
- Calculate annual rewards lost to 1x earn
- Suggest cards that would fill each gap
- Prioritize by gap size (largest $ value first)

### 4. Fee Audit
For each card with an annual fee:
- Does the user fully offset the fee with rewards + perks?
- Is there a no-fee downgrade path?
- When is the fee anniversary? (to plan downgrades before renewal)

### 5. Ecosystem & Transfer Partner Analysis
Using `wiki/card-ops/portfolio-strategy.md`:
- Check current cards against the Ecosystem Trifectas table -- is the user in one ecosystem? Partially?
- Check `wiki/card-ops/transfer-partners.md` -- which exclusive partners does the user currently access?
- Identify if user is 1 card away from completing a trifecta
- If user has cards across multiple ecosystems: flag potential for points fragmentation (small balances in multiple programs are harder to redeem at high value)
- Recommend primary ecosystem based on spending pattern and transfer partner preference

### 6. Annual Fee Audit (Enhanced)
Using `wiki/card-ops/portfolio-strategy.md#Annual Fee Stacking Math`:
- For each fee card: calculate `Net_Value = Annual_Rewards + Perk_Value_Used + Retention_Offer - Annual_Fee`
- Only count perks the user ACTUALLY redeems (not theoretical value)
- Flag cards where `Net_Value < 0` as downgrade/cancel candidates
- Check AF refund windows and alert if approaching deadline
- Total portfolio AF: sum all annual fees. Compare to total portfolio value.
- Show total net portfolio value (rewards + perks - all fees)

### 7. AAoA & Credit Health Check
- Calculate current AAoA from `current_cards` opened dates
- Model impact of recommended new cards on AAoA
- Flag if closing any card would remove the oldest account
- Recommend downgrade over close when possible (preserves account age)
- Check utilization impact of adding/removing credit lines

### 8. Recommendation
Output a prioritized action plan:
1. **Keep and optimize**: Cards earning their slot, optimal spending assignment
2. **Apply for**: Gap-filling cards, ranked by value add. Note which trifecta they complete.
3. **Downgrade**: Fee cards not earning their keep (call retention first -- see `wiki/card-ops/bonus-strategy.md#Retention Offer Strategy`)
4. **Close**: Cards with no value and no downgrade path (watch AAoA impact)
5. **Timing**: Sequence applications per issuer rules (Chase first due to 5/24, then others). Space 30-90 days apart. Note combined inquiry impact on AAoA and score.
