# Mode: Compare Card Offers

## Trigger
User wants to compare 2+ card offers side by side.

## Inputs
- Card offers (URLs, names, or report numbers from tracker)
- `config/profile-chris.yml`, `config/profile-dana.yml` (financial profiles)
- `config/household.yml` (shared spending, wallet routing)
- Existing reports in `reports/` (if previously evaluated)
- Parquets in `data/transactions/` (actual spending data)

## Execution Steps

### 1. Gather Card Details
- If already evaluated: read existing reports
- If new: run quick evaluation (Blocks A + D only) for each card

### 2. Build Comparison Table

| Dimension | Card A | Card B | Card C |
|-----------|--------|--------|--------|
| Issuer | | | |
| Annual Fee | | | |
| Signup Bonus | | | |
| MSR / Window | | | |
| Effective 1st-Year Value | | | |
| Ongoing Annual Value | | | |
| Top Category Rate | | | |
| 2nd Category Rate | | | |
| Flat Rate | | | |
| Key Perks | | | |
| Approval Probability | | | |
| Score | X.X/5 | X.X/5 | X.X/5 |

### 3. Head-to-Head Analysis
Use `lib/model.compare_scenarios()` with actual spending data from parquets for side-by-side value comparison.

For each pair, identify:
- Which wins on first-year value (bonus + rewards - fee)? Use `docs/points-valuations.md` for point conversions.
- Which wins on ongoing value (year 2+ rewards - fee)?
- Which has better approval odds?
- Which fits the portfolio better?
- Which points currency has better long-term value (transfer partner depth, devaluation risk)?

### 4. Recommendation
- Rank cards by overall fit
- If close: frame as "Card A for short-term value, Card B for long-term hold"
- If one dominates: clear recommendation with reasoning
- If neither fits well: say so and suggest what to look for instead

### 5. Application Sequencing
If user wants multiple cards, use `docs/issuer-rules.md` and `docs/portfolio-strategy.md`:
- Order by issuer sensitivity: Chase first (5/24), then US Bank/Barclays (inquiry-sensitive), then Amex/Citi/others
- Respect velocity limits: Chase 2/30, Amex 2/90, Citi 1/8 + 2/65, BofA 2/3/4
- Space applications 30-90 days apart (minimum)
- Model AAoA impact of adding multiple cards
- Note combined hard inquiry impact on score and future applications
- If cards are from the same ecosystem: note trifecta completion opportunity
