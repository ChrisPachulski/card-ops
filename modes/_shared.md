# Card-Ops Shared Rules

## Card Types (Archetypes)

When evaluating a card offer, classify it into one or more of these types:

| Type | Signals | Best For |
|------|---------|----------|
| **Cash Back Flat** | 1.5-2% everything, no categories | Simplicity, default spending |
| **Cash Back Category** | 3-5% rotating or fixed categories | Heavy spend in specific categories |
| **Travel Points** | Transferable points (UR, MR, TYP, C1 Miles) | Flexible travel redemption |
| **Hotel Co-brand** | Earn hotel points, free night certs | Frequent hotel stays at one chain |
| **Airline Co-brand** | Earn airline miles, bag waivers, priority boarding | Loyal to one airline |
| **Business** | Employee cards, higher limits, business categories | Business expenses, category separation |
| **Balance Transfer** | 0% intro APR, low BT fees | Debt payoff strategy |
| **Premium Perks** | Lounge access, travel credits, concierge, high AF | High spenders who redeem perks fully |

## Scoring System

**Global Score (1-5)** = weighted average of:

| Dimension | Weight | What It Measures |
|-----------|--------|------------------|
| **Eligibility** | 25% | Credit score fit, income requirement, issuer rules (5/24, once-per-lifetime) |
| **Bonus Value** | 20% | Signup bonus attainability (can you hit MSR?), bonus dollar value |
| **Ongoing Value** | 25% | Annual rewards based on YOUR spending categories vs card earn rates |
| **Perks Fit** | 15% | Do you actually use the perks? (lounge access, credits, insurance) |
| **Opportunity Cost** | 15% | Hard inquiry impact, annual fee vs alternatives, slot cost |

### Score Interpretation

| Score | Meaning |
|-------|---------|
| 4.5+ | Strong match -- apply soon, especially if limited-time offer |
| 4.0-4.4 | Good match -- worth applying if within inquiry budget |
| 3.5-3.9 | Decent but not optimal -- consider only if no better options |
| Below 3.5 | Poor fit -- recommend against applying. Hard inquiry not worth it. |

### Scoring Rules

1. **Never round up to cross a threshold.** 3.49 is "below 3.5", not "approximately 3.5".
2. **Eligibility is a gate.** If the user clearly won't be approved (e.g., over 5/24 for Chase), cap at 2.0 regardless of other dimensions.
3. **Annual fee cards must clear their fee.** If projected annual value < annual fee, deduct from Ongoing Value.
4. **Signup bonus is one-time.** Score Bonus Value based on attainability, but weight Ongoing Value higher for long-term holds.
5. **Opportunity cost includes alternatives.** If a $0-fee card delivers 90% of the value, the $95-fee card's opportunity cost is high.
6. **Statement credits count as value ONLY if redeemed.** Include Amex Offers, Chase Offers, and card-specific credits (travel, dining, streaming, etc.) in Perks Fit only for credits the user will actually use. See Statement Credit Programs below.
7. **Premium card credit stacking.** Cards like CSR ($300 travel + $250 Edit + $250 hotel) and Amex Platinum ($200 hotel + $200 airline + $200 Uber + more) can offset most of the AF -- but ONLY if the user naturally spends in those categories. Never assume full credit utilization.

### Scoring Calibration & Statement Credits

> **Wiki reference**: Read [[scoring-benchmarks]] (`docs/scoring-benchmarks.md`) for calibration benchmarks (10 reference card scores across 2 user profiles) and statement credit programs (Amex Offers, Chase Offers, credit stacks). Load this page when scoring Perks Fit or validating scoring output.

## Evaluation Report Structure

Every evaluation produces a report with these blocks:

### Block A: Card Summary
Table with: card type, issuer, annual fee, signup bonus, MSR (minimum spend requirement), MSR window, intro APR, regular APR, foreign transaction fee, key earn rates.

### Block B: Eligibility Match
- Credit score requirement vs user's range
- Income requirement (if any)
- Issuer-specific rules: Chase 5/24 status, Amex once-per-lifetime, Citi 48-month
- Existing relationship considerations
- Hard inquiry impact assessment

### Block C: Bonus Strategy
- MSR amount and window (e.g., $4,000 in 3 months)
- Can user hit MSR from organic spend? Show the math.
- If not: safe strategies (prepay bills, buy gift cards for planned purchases)
- Bonus value calculation (points x cpp valuation or cash equivalent)
- Time-limited offer check: is this an elevated bonus?

### Block D: Value Analysis
- Map user's spending categories to card earn rates
- Calculate projected annual rewards (category by category)
- Compare to current card in same slot
- Net value = rewards + perks value - annual fee
- Break-even analysis: how much spend to justify the fee?

### Block E: Portfolio Optimization
- Where does this card fit in the portfolio? (daily driver, category specialist, sock drawer for perks)
- Does it overlap with existing cards?
- Which current card does it replace or complement?
- Ecosystem considerations (Chase trifecta, Amex ecosystem, etc.)

### Block F: Application Plan
- Approval probability assessment (High / Medium / Low)
- Optimal timing (relative to recent inquiries, account age)
- Reconsideration line strategy if denied
- Product change options as alternative

## Risk & Timing Awareness

> **Wiki reference**: Read [[application-timing]] (`docs/application-timing.md`) for bureau pull preferences, inquiry sensitivity rankings, application spacing rules, bust-out risk flags, utilization math, and life-event timing calendar. Load this page when assessing Block F (Application Plan).

## Issuer Application Rules

> **Wiki reference**: Read [[issuer-rules]] (`docs/issuer-rules.md`) for the complete rules database covering 7 issuers with 25+ specific rules. Load this page when assessing Block B (Eligibility Match). Covers: Chase 5/24 + Sapphire pop-up, Amex once-per-lifetime + 5-card limit, Citi 48-month + velocity, Capital One, Barclays, US Bank, BofA.

## Points & Miles Valuations

> **Wiki reference**: Read [[points-valuations]] (`docs/points-valuations.md`) for transferable currency valuations (6 programs), transfer partner valuations (12 programs), valuation methodology, 8 valuation rules, and devaluation risk tracking. Load this page when calculating bonus value (Block C) or ongoing value (Block D).

## Portfolio Strategy

> **Wiki reference**: Read [[portfolio-strategy]] (`docs/portfolio-strategy.md`) for ecosystem trifectas, AF stacking math, AAoA impact, and card count guidance. Read [[transfer-partners]] (`docs/transfer-partners.md`) for the 15-partner, 4-currency overlap matrix. Load these pages for Block E (Portfolio Optimization) and the optimize mode.

## MSR & Bonus Strategy

> **Wiki reference**: Read [[bonus-strategy]] (`docs/bonus-strategy.md`) for MSR achievability framework (3 tiers), clawback risk by issuer, referral bonus overlay, retention offer strategy, and upgrade/downgrade paths. Load this page when writing Block C (Bonus Strategy) and when advising on card lifecycle decisions.

## Advanced Techniques

> **Wiki reference**: Read [[advanced-techniques]] (`docs/advanced-techniques.md`) for expert-level strategies: credit freeze/bureau lock, AU strategy, NLL offers, in-branch pre-approvals, gardening. Mention these when relevant but do not build scoring around them.

## Global Rules

1. **Read `config/profile.yml` fresh every evaluation.** Never cache or assume.
2. **Read `modes/_profile.md` for user overrides.** User preferences always win.
3. **Statement data supplements profile data.** If statements are parsed, use actual spend; otherwise use profile estimates.
4. **All monetary values in USD** unless user specifies otherwise.
5. **Credit score ranges, not points.** Say "740-760 range" not "exactly 750".
6. **Never guarantee approval.** Always frame as probability, never certainty.
7. **Flag time-sensitive offers.** If a bonus is elevated or expiring, note the deadline prominently.
