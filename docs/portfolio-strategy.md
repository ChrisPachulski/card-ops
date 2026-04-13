
# Portfolio Strategy

Covers ecosystem trifecta selection, annual fee math, and optimal card count relative to credit score impact. For the transfer partner overlap that drives trifecta differentiation, see [[transfer-partners]]. For cpp valuations used in annual fee math, see [[points-valuations]]. For MSR strategy and upgrade/downgrade paths, see [[bonus-strategy]]. For application spacing relative to portfolio growth, see [[application-timing]].

## Ecosystem Trifectas

Each major issuer offers a 3-card combination that maximizes earning across all categories within one points currency:

| Ecosystem | Cards | Total AF | Base Earn Coverage | Key Advantage | Source |
|-----------|-------|----------|-------------------|---------------|--------|
| **Chase** | CSR ($550) + CFU (1.5x base, $0) + CFF (5x rotating, $0) | $550 | 1.5x everywhere, 3x dining/travel, 5x rotating | Hyatt transfers (highest-value hotel), 1.5x portal via CSR | [WEB] NerdWallet, TPG |
| **Amex** | Platinum ($695) + Gold ($325) + BBP (2x everything, $0) | $1,020 | 2x everywhere, 4x dining/grocery, 5x flights (Plat) | Broadest transfer partner network, premium travel perks | [WEB] TPG |
| **Citi** | Premier ($95) + Custom Cash (5x top category, $0) + Double Cash (2x, $0) | $95 | 2x everywhere, 3x travel/gas/dining, 5x top category | Lowest total AF, AAdvantage exclusivity | [WEB] NerdWallet, TPG |
| **Capital One** | Venture X ($395) + Savor ($95) + SavorOne ($0) | $490 | 2x everything, 3-4% dining/entertainment/grocery | Priority Pass, 10,000 anniversary miles | [WEB] TPG |

**Decision framework:**
- High organic spend ($5K+/mo) + travel: Amex (maximize perks + credits to offset AF)
- Moderate spend ($3-5K/mo) + travel: Chase (Hyatt transfers are unmatched, lower AF)
- Lower spend ($1.5-3K/mo) or cash-back preference: Citi (lowest AF, strong base rates)
- Dining/entertainment heavy: Capital One (Savor + Venture X combo)

## Transfer Partner Overlap

See [[transfer-partners]] for the full 15-partner, 4-currency overlap matrix with exclusivity analysis.

## Annual Fee Stacking Math

The keep/cancel/downgrade decision for fee cards:

**Annual Value Formula:**
```
Net_Value = (Annual_Rewards) + (Perk_Value_Used) + (Retention_Offer) - (Annual_Fee)
```

- `Annual_Rewards`: projected from spending (use valuation table cpp)
- `Perk_Value_Used`: ONLY count perks the user actually redeems (lounge access, travel credits, airline incidentals). Do NOT count perks that sound nice but go unused.
- `Retention_Offer`: amortized value of retention offers (see Retention Offer Strategy)
- If `Net_Value < 0`: downgrade or cancel

**AF Refund Windows (act within these after fee posts):**

| Issuer | Cancel/Downgrade Window | Prorated Refund? | Source |
|--------|------------------------|-----------------|--------|
| Chase | 30 days | No | [WEB] OMAAT |
| Amex | 30 days (cancel); downgrade may get prorated beyond 30 | Yes for downgrades | [WEB] OMAAT |
| Citi | 37 days | No | [WEB] OMAAT |
| Barclays | 60 days | No | [WEB] OMAAT |

## Optimal Card Count & AAoA Impact

**Credit score factors (FICO):**
- Payment history: 35% (most important -- never miss a payment)
- Credit utilization: 30% (keep below 10% for optimal scoring, 30% max)
- Length of credit history: 15% (average age of accounts + oldest account age)
- Credit mix: 10% (having both revolving and installment accounts)
- New inquiries: 10% (recent hard pulls)

**AAoA math:**
- Each new card reduces average age. Example: 5 cards with 8-year average -> opening 1 new card drops average to ~6.7 years.
- Impact is proportionally larger with fewer existing accounts
- FICO considers: age of oldest account, age of newest, average across all
- Closing old accounts: account remains on report for 10 years (FICO), but VantageScore drops it immediately
- **Rule of thumb**: If AAoA is >7 years, a new card's impact is minimal. If <3 years, be strategic.

**Practical guidance:**
- 5+ accounts = thick credit file (good for scoring)
- 3-5 active cards = manageable for most people
- 5-8 active cards = typical for rewards optimizers
- 10+ cards = aggressive churner territory (higher management overhead, but AAoA impact diminishes with more accounts)
- **Never close your oldest card** unless it has an unavoidable fee and no downgrade path

Sources: [WEB] NerdWallet credit factors, DoC AAoA calculation guide -- accessed 2026-04-12.
