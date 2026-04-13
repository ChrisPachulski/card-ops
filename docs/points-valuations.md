
# Points & Miles Valuations

Reference valuations (cents-per-point) for all major transferable currencies and airline/hotel programs. For which programs each currency can reach, see [[transfer-partners]]. For how these valuations feed into card scoring, see [[scoring-benchmarks]].

Valuations vary by redemption method. Always use the tier that matches the user's stated `reward_strategy.primary_goal` in their profile. When uncertain, use the **Baseline** column -- it reflects typical mixed-use redemption, not best-case cherry-picking.

## Transferable Credit Card Currencies

| Program | Cash-Out (cpp) | Portal (cpp) | Transfer (cpp) | Baseline (cpp) | Source |
|---------|---------------|--------------|----------------|----------------|--------|
| Chase Ultimate Rewards | 1.0 | 1.25 (CSP) / 1.5 (CSR) | 1.8-2.3 | 2.0 | [TPG Apr 2026], [NerdWallet 2026] |
| Amex Membership Rewards | 0.6 (statement) | 1.0 (flights) / 0.7 (hotels) | 1.8-2.2 | 2.0 | [TPG Apr 2026], [NerdWallet 2026] |
| Citi ThankYou Points | 1.0 (cash) | 1.0 | 1.6-2.0 | 1.9 | [TPG Apr 2026], [NerdWallet 2026] |
| Capital One Miles | 1.0 (travel eraser) | 1.0 | 1.6-2.0 | 1.85 | [TPG Apr 2026] |
| Bilt Rewards | 1.0 | 1.25 (Bilt Travel) | 1.8-2.4 | 2.2 | [TPG Apr 2026] |
| Wells Fargo Rewards | 1.0 | 1.5 (Autograph) | 1.4-1.8 | 1.65 | [TPG Apr 2026] |

## Key Transfer Partner Programs

| Program | Valuation (cpp) | Best Transfer Sources | Notes |
|---------|----------------|----------------------|-------|
| World of Hyatt | 1.7 (avg), 2.4-3.2 (luxury) | Chase UR (1:1) | Highest-value hotel currency. Peak pricing increasing May 2026 |
| United MileagePlus | 1.35-1.5 | Chase UR (1:1) | Europe saver awards are sweet spots |
| Air France/KLM Flying Blue | 1.3-1.5 | Amex MR, Capital One, Citi TYP (all 1:1) | Frequent promo awards to Europe |
| Alaska Mileage Plan | 1.4 | None direct (earn via co-brand) | Partner award chart sweet spots |
| Aeroplan | 1.4 | Amex MR, Chase UR (1:1) | Strong for Star Alliance awards |
| Avianca LifeMiles | 1.4 | Amex MR, Citi TYP, Capital One (1:1) | Cheap Star Alliance redemptions |
| British Airways Avios | 1.4 | Chase UR, Amex MR (1:1) | Best for short-haul, distance-based |
| Delta SkyMiles | 1.2 | Amex MR (1:1) | Unpredictable pricing, no award chart |
| Southwest Rapid Rewards | 1.25 | Chase UR (1:1) | Fixed cpp, no devaluation risk |
| Marriott Bonvoy | 0.75 | Amex MR (1:1 but poor value) | 5th night free on 5+ night awards |
| Hilton Honors | 0.4-0.5 | Amex MR (1:2 ratio) | High point costs, devaluation-prone |
| IHG One Rewards | 0.6 | Chase UR (1:1 via co-brand only) | Fourth reward night free perk |

## Valuation Methodology

These valuations are derived from published data-driven analyses, not opinion:
- **TPG method**: Thousands of routes over a rolling 3-month window, weighted by BTS passenger traffic data. Updated monthly. [WEB] thepointsguy.com/news/new-valuations/
- **NerdWallet method**: Median cpp from real cash vs award booking comparisons across many dates and cities. Not best-case scenarios. [WEB] nerdwallet.com/travel/learn/how-to-use-points-valuations
- **Basic formula**: `cpp = ((Cash_Price - Taxes_and_Fees) / Points_Required) * 100`

Why Baseline column exists: Different sources give different valuations (TPG tends higher, NerdWallet more conservative). The Baseline column represents a defensible middle ground for scoring. When the user's redemption behavior is known, use the matching tier column instead.

## Valuation Rules

1. **Match redemption tier to user behavior.** If `reward_strategy.primary_goal` is `cash_back`, use the Cash-Out column. If `travel_points`, use Transfer column. If unspecified, use Baseline.
2. **Never use best-case transfer valuations for scoring.** The Transfer column is a range. Use the low end unless the user has demonstrated transfer partner usage. Most cardholders redeem via portals, not transfers -- this is where the NerdWallet vs TPG gap comes from.
3. **Portal redemptions are the realistic floor for travel users.** Most travel users will at minimum book through issuer portals. Use portal cpp as the conservative travel valuation. For Chase: 1.25 cpp (CSP) or 1.5 cpp (CSR). For Amex: 1.0 cpp flights, 0.7 cpp hotels.
4. **Cash-out is the guaranteed floor.** Always compare net value against cash-out as the risk-free baseline. This is the "worst case" valuation.
5. **Devaluation discount.** For points balances held >12 months, apply a 10% haircut to transfer valuations. Points are a depreciating asset -- issuers devalue annually. [INFERRED heuristic -- no published source, but directionally supported by expert consensus to "earn and burn"]
6. **Transfer bonuses are temporary.** Do not factor transfer bonuses (typically 20-30% periodic promotions) into baseline scoring. Note them as upside in the report.
7. **Two-valuation reporting.** For every point-based value calculation, show BOTH the conservative valuation (Cash-Out or Portal) and the optimistic valuation (Transfer Baseline). This gives the user a range to make decisions with, rather than a single number that may over- or under-estimate.
8. **Transfer partner sweet spots are not the norm.** A 5 cpp Hyatt redemption at a Park Hyatt exists, but the median redemption is ~1.7 cpp. Score based on median, note sweet spots as upside in the report narrative.

## Devaluation Risk Awareness

Track these active/upcoming devaluations in evaluations:
- **Hyatt (May 2026):** New 5-tier peak/off-peak chart. Top European properties up ~67% in peak pricing.
- **Citi (Apr 2026):** Choice Privileges and Preferred Hotels transfer ratio reductions.
- **Amex (June 2026):** Ending Etihad Guest transfer partnership. Prior: Emirates and Cathay Pacific ratio reductions.
- **General trend:** Transfer ratios worsening across programs. The "earn and burn" strategy (redeem quickly rather than hoard) is increasingly favored by experts.

## Valuation Source Dates

These valuations are from **April 2026**. Refresh from TPG monthly valuations, NerdWallet, or Upgraded Points if evaluating more than 3 months after this date. Key sources:
- The Points Guy monthly valuations (thepointsguy.com/loyalty-programs/monthly-valuations/)
- Upgraded Points valuations (upgradedpoints.com/travel/points-and-miles-valuations/)
- NerdWallet program guides (nerdwallet.com/travel/learn/)
