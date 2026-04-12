# Mode: Evaluate Card Offer

## Trigger
User provides a card offer (URL, screenshot, or pasted details).

## Inputs Required
1. Card offer details (from URL, text, or user description)
2. `config/profile.yml` (financial profile)
3. `modes/_profile.md` (user overrides)
4. `data/cards.md` (existing tracker -- to check for duplicates and portfolio context)

## Execution Steps

### 1. Extract Offer Details
- If URL: fetch the page and extract card terms
- If text: parse the offer details
- Identify: issuer, card name, annual fee, signup bonus, MSR, earn rates, key perks

### 2. Classify Card Type
Per `_shared.md` card types. May be hybrid (e.g., "Travel Points + Premium Perks").

### 3. Block A: Card Summary
Build the summary table. Include:
- Card type classification
- Annual fee (and waived first year?)
- Signup bonus + MSR + MSR window
- Key earn rates by category
- Intro APR offer (if any)
- Foreign transaction fee
- Notable perks (lounge access, credits, insurance)

### 4. Block B: Eligibility Match
- Read user's credit score from `config/profile.yml`
- Check ALL applicable issuer-specific rules from `wiki/card-ops/issuer-rules.md`:
  - **Chase:** 5/24 count (from profile `chase_524_status` + `current_cards` opened dates), 2/30 velocity, Sapphire pop-up eligibility, credit reallocation opportunity
  - **Amex:** Once-per-lifetime check (`amex_once_per_lifetime` list), 5-credit-card limit check, 2/90 velocity, pop-up jail risk assessment
  - **Citi:** 48-month bonus eligibility (from bonus receipt date, not approval), 1/8 and 2/65 velocity, 6/6 inquiry check
  - **Capital One:** 48-month same-card check, ~2 personal card limit, 3-bureau pull warning, biz card 5/24 impact
  - **Barclays:** 6/24 inquiry count, spending history on existing cards
  - **US Bank:** Inquiry sensitivity assessment, existing relationship check (mandatory for Altitude Reserve)
  - **BofA:** 2/3/4 velocity rule, deposit relationship status
- Check income requirements (if stated)
- For business card applications: note whether the card reports to personal credit (affects 5/24)
- Assess approval probability: **High** (strong match, all rules clear) / **Medium** (borderline on 1+ rules) / **Low** (fails a hard rule like 5/24)

### 5. Block C: Bonus Strategy
- **MSR achievability** (use `wiki/card-ops/bonus-strategy.md`):
  - Calculate: `monthly_spending.total * MSR_window_months` vs `MSR_amount`
  - Tier 1 (organic): if >= 100%, flag "achievable from normal spending"
  - Tier 1.5 (organic borderline): if 80-99%, flag "likely achievable with timing adjustments"
  - Tier 2 (acceleration needed): if < 80%, suggest safe acceleration strategies from `wiki/card-ops/bonus-strategy.md`
  - Tier 3: do NOT recommend manufactured spending. If MSR is unreachable organically, factor that into the Bonus Value score.
- **Bonus value calculation** (use `wiki/card-ops/points-valuations.md`):
  - Cash back: face value
  - Points/miles: look up the program in the Transferable Currencies table
  - Use the column matching the user's `reward_strategy.primary_goal`:
    - `cash_back` -> Cash-Out cpp
    - `travel_points` / `airline_miles` / `hotel_perks` -> Transfer cpp (low end of range)
    - Unspecified -> Baseline cpp
  - Show the range: "75,000 UR = $750 (cash) to $1,725 (transfer partners) -- baseline $1,500"
- **Referral check**: If user holds a card in the same family, note referral bonus opportunity and value (see `wiki/card-ops/bonus-strategy.md#Referral Bonus Overlay`)
- **Elevated offer check**: Is this a limited-time elevated bonus vs standard? If standard, note the typical elevated bonus for comparison.
- **Clawback warning**: Note the issuer's clawback rules (see `wiki/card-ops/bonus-strategy.md#Clawback Risk Framework`). Minimum: "Keep card open 12+ months."
- **Devaluation risk**: Note if points are in a program with active/upcoming devaluations (see `wiki/card-ops/points-valuations.md#Devaluation Risk Awareness`)

### 6. Block D: Value Analysis
- Map each spending category from `config/profile.yml` to card earn rates
- Calculate monthly and annual projected rewards using `wiki/card-ops/points-valuations.md`:
  - Multiply points earned per category by the appropriate cpp from `wiki/card-ops/points-valuations.md`
  - Always show rewards in BOTH points and dollar-equivalent
- Subtract annual fee
- Compare net value to user's current best card for each category
- Calculate break-even point (months of spending to recoup fee)
- For annual fee cards: show "Year 1 value" (includes bonus) and "Year 2+ value" (ongoing only) separately
- **Statement credit programs**: Check if card participates in Amex Offers, Chase Offers, or issuer credit stack (see `wiki/card-ops/scoring-benchmarks.md#Statement Credit Programs`). Estimate realistic annual value based on user's redemption profile (50-70% active, 20-40% casual). Include in Perks Fit scoring.
- **Calibration check**: Compare your score against `wiki/card-ops/scoring-benchmarks.md` for a similar user profile. If significantly divergent, re-examine dimension scores.

### 7. Block E: Portfolio Optimization
- Check `current_cards` in profile for overlap
- Identify which slot this card fills (daily driver, category specialist, perks card)
- Check ecosystem fit (e.g., Chase trifecta: CSR + CFF + CFU)
- Flag if this replaces or complements an existing card
- Note any product change paths (e.g., downgrade path to no-fee version)

### 8. Block F: Application Plan
**MANDATORY PRE-APPLICATION CHECK**: If user's current utilization is >10%, recommend paying down balances before applying. Utilization is a snapshot -- one month of low utilization before the application is sufficient. This single action has the highest impact on approval odds of anything in this section.

Using `wiki/card-ops/application-timing.md`:
- **Approval probability** (revisit with full eligibility + risk context)
- **Bureau impact**: Which bureau will this issuer pull? (see Bureau Preferences table). How many inquiries does the user have on that bureau already?
- **Inquiry sensitivity**: Where does this issuer rank? (see `wiki/card-ops/application-timing.md`). If applying to a sensitive issuer, check total recent inquiries.
- **Utilization check**: User's current utilization. If >30%, recommend paying down before applying.
- **Timing recommendation**: Use Application Spacing rules and Application Timing Calendar. Flag if user has a mortgage/auto/rental coming up.
- **Bust-out prevention**: If MSR is high relative to credit limit, warn about bust-out flags. Recommend not hitting more than 50% of expected limit in first month.
- If denied: reconsideration line number + strategy (see Issuer Rules reference)
- Alternative: product change from existing card (if applicable, see Upgrade/Downgrade Paths)
- Note: inquiry will appear on credit report for 2 years, but FICO impact diminishes after 12 months

### 9. Score
Apply scoring weights from `_shared.md` (or overrides from `_profile.md`).
Show the breakdown table:

| Dimension | Score | Weight | Weighted |
|-----------|-------|--------|----------|
| Eligibility | X.X | 25% | X.XX |
| Bonus Value | X.X | 20% | X.XX |
| Ongoing Value | X.X | 25% | X.XX |
| Perks Fit | X.X | 15% | X.XX |
| Opportunity Cost | X.X | 15% | X.XX |
| **Global** | | | **X.X/5** |

### 10. Adversarial Gate (scores >= 4.0)

If the global score is 4.0 or above, invoke `/devils-advocate` on the evaluation before presenting the final recommendation. Hard inquiries cost credit score -- challenge the recommendation before the user acts on it.

### 11. Output

1. Save report to `reports/{###}-{issuer-slug}-{YYYY-MM-DD}.md`
2. Write tracker TSV to `batch/tracker-additions/{num}-{issuer-slug}.tsv`
3. Present recommendation:
   - Score >= 4.5: "Strong match. Apply soon, especially if bonus is time-limited."
   - Score 4.0-4.4: "Good match. Worth applying if you have inquiry budget."
   - Score 3.5-3.9: "Decent but not ideal. Consider only if no better options."
   - Score < 3.5: "Poor fit. Recommend against applying -- hard inquiry not worth it."

## After Evaluation
- Run `node merge-tracker.mjs` to update cards.md
- If user says "score is too high/low", note the feedback in `modes/_profile.md`
- If the card replaces an existing fee card: remind user to call for retention offer before closing/downgrading (see `wiki/card-ops/bonus-strategy.md#Retention Offer Strategy`)
- If a product change path exists for the replaced card: note it in the report (see `wiki/card-ops/bonus-strategy.md#Upgrade/Downgrade Paths`)
