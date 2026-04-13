
# Application Timing & Risk

This page covers bureau pull preferences, inquiry sensitivity by issuer, utilization math, and the application timing calendar. For the underlying rules that govern which issuers are sensitive to what, see [[issuer-rules]]. For credit freeze and bureau management tactics, see [[advanced-techniques]].

## Hard Pull Bureau Preferences by Issuer

Knowing which bureau each issuer pulls helps manage inquiry distribution:

| Issuer | Primary Bureau | Notes | Source |
|--------|---------------|-------|--------|
| **Chase** | Varies by state | Check DoC state-by-state data for your location | [WEB] DoC |
| **Amex** | Experian (~90%) | Occasionally TransUnion | [WEB] DoC |
| **Citi** | Equifax or Experian | Varies by state | [WEB] DoC |
| **Capital One** | All 3 (Experian + TransUnion + Equifax) | Always multi-pull -- counts as 1 inquiry per bureau | [WEB] DoC |
| **Barclays** | TransUnion (~90%) | Good for spreading inquiries away from Experian | [WEB] DoC |
| **US Bank** | TransUnion (~52%), Experian (~25%), Equifax (~24%) | Varies by state | [WEB] DoC |
| **BofA** | Experian (primary) | Occasionally TransUnion or Equifax | [WEB] DoC |

**Strategy**: Sequence applications to distribute inquiries across bureaus. Example: Apply to Amex (Experian pull) and Barclays (TransUnion pull) rather than Amex + BofA (both Experian). Capital One's triple-pull means it always adds to all bureau counts.

## Inquiry-Sensitive Issuers (ordered most to least sensitive)

1. **US Bank**: Most inquiry-sensitive. Existing banking relationship strongly recommended. Recent inquiries can cause denial even with excellent credit.
2. **Barclays**: 6/24 rule (inconsistently applied). Prefers low inquiry count on TransUnion.
3. **Capital One**: Inconsistent, but multiple recent inquiries can trigger denial. Triple-pull means they see everything.
4. **Chase**: 5/24 counts accounts, not inquiries -- but high inquiry count on pull bureau can be a negative factor.
5. **Citi**: 6/6 rule (6+ inquiries in 6 months may cause denial). Inconsistently enforced.
6. **BofA**: 2/3/4 rule limits accounts. Inquiry count matters less than account count.
7. **Amex**: Least inquiry-sensitive. Most applicants with good credit get approved regardless of inquiry count.

**Application order for a multi-card strategy**: US Bank -> Barclays -> Chase -> Citi -> BofA -> Amex (most sensitive first, while inquiry count is lowest).

## Optimal Application Spacing

| Pace | Monthly Cards | Who It's For | Risk Level |
|------|--------------|--------------|------------|
| Conservative | 1 card per quarter | Building credit, maintaining AAoA, score-conscious | Low |
| Moderate | 1 card every 2 months | Standard rewards optimization | Low-Medium |
| Aggressive | 1 card per month | Experienced churners with high organic spend | Medium |
| Very aggressive | 2+ cards per month | Expert level, requires careful bureau management | High |

**General spacing rules:**
- Same issuer: 2-3 months minimum (except Amex same-day double-dip)
- Different issuers: 1 month minimum for spacing
- After a denial: wait 3-6 months before reapplying to the same issuer
- After multiple approvals: pause for 3-6 months to let inquiries age and AAoA stabilize

## Bust-Out Risk Flags

Banks monitor for patterns that resemble bust-out fraud (opening cards and maxing them out). Avoid these red flags:

| Flag | What Triggers It | Consequence | Source |
|------|-----------------|-------------|--------|
| Immediate maxing | Hitting credit limit shortly after approval | Account review, fraud hold, shutdown | [WEB] TPG |
| Credit cycling | Paying down and re-spending above credit limit | Points forfeiture, account closure | [WEB] OMAAT |
| High velocity | Many new accounts in short period with large balances | Financial review (Amex), shutdown (Chase) | [WEB] TPG |
| Low utilization then spike | Going from 5% to 90% utilization suddenly | Issuer alert, limit reduction | [WEB] NerdWallet |
| Gift card heavy spend | Large volume of gift card purchases (especially at Simon, grocery) | MSR may not count (Amex), account review | [WEB] DoC |

**Amex Financial Review**: Amex can request full financial documentation (tax returns, bank statements) if spending patterns trigger internal review. This is rare but invasive. Triggered by very high spend relative to stated income or sudden spending pattern changes.

## Credit Utilization Math

| Utilization Range | Score Impact | Strategy |
|-------------------|-------------|----------|
| 0% (all zero balances) | Slightly negative | Keep at least 1 card reporting a small balance |
| 1-9% | Optimal | Best for FICO scoring |
| 10-29% | Good | Acceptable range |
| 30-49% | Moderate negative | Start paying down |
| 50%+ | Significant negative | Prioritize paying down before new applications |

**Per-card vs overall**: FICO considers BOTH overall utilization (total balances / total limits) AND individual card utilization. One card at 90% hurts even if overall is 10%.

**Timing trick**: Utilization is a snapshot, not a trend. Pay down balances to <10% the month before applying for a new card. The score will reflect the lower utilization even if you normally carry higher balances.

**New card impact**: A new credit line increases total available credit, which REDUCES overall utilization (positive). But the new inquiry and young account age are negatives. Net effect is usually positive if utilization was high.

## Application Timing Calendar

When to apply relative to life events:

| Event | Wait Before Applying | Reason |
|-------|---------------------|--------|
| Mortgage application | 6-12 months before: STOP applying | Mortgage lenders scrutinize inquiries heavily |
| Auto loan | 3-6 months before: pause | Less scrutiny than mortgage but still matters |
| Apartment rental | 1-3 months before: pause | Landlords check credit; inquiries and young accounts look bad |
| After denial | 3-6 months | Let inquiry age; address denial reason first |
| After approval | 30-90 days | Standard spacing before next application |
| Year-end (Nov-Dec) | Good time to apply | Issuers often have elevated holiday bonuses |
| New year (Jan-Feb) | Good time to apply | Fresh velocity windows reset |
