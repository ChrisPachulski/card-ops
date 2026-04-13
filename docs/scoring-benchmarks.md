
# Scoring Benchmarks & Statement Credits

Reference benchmarks for validating the card scoring system, plus the statement credit programs that feed into Perks Fit scoring. For the cpp valuations used in bonus value calculations, see [[points-valuations]]. For how scores translate to portfolio decisions, see [[portfolio-strategy]].

## Scoring Calibration Benchmarks

These reference scores validate that the scoring system produces results aligned with expert consensus. If your scoring diverges significantly from these benchmarks for a similar user profile, re-examine your dimension scores.

**Profile: Moderate spender ($4K/mo), travel 2-3x/year, 740+ credit, under 5/24**

| Card | Expected Score | Rationale | Source |
|------|---------------|-----------|--------|
| CSP ($95 AF) | 4.2-4.5 | Low AF, strong bonus, good earn rates. 2026 expert consensus: better value than CSR for most users. | [WEB] NerdWallet 2026 |
| CSR ($795 AF) | 3.4-3.8 | High AF hard to offset at moderate travel. Only scores 4.0+ if user fully redeems $800+ in credits. Expert shift: "Reserve dethroned" for most cardholders. | [WEB] NerdWallet, Upgraded Points 2026 |
| CFF ($0 AF) | 4.3-4.6 | No-fee category king. 5x rotating + 3x dining. Almost always a strong add. | [WEB] TPG 2026 |
| Amex Gold ($325 AF) | 3.8-4.2 | Strong for dining + grocery heavy spenders. Needs $500+/mo in groceries to clear fee. | [WEB] TPG 2026 |
| Amex Platinum ($695 AF) | 3.0-3.6 | Premium perks card. Only scores 4.0+ for frequent travelers who use lounge access, airline credit, hotel credit, and Uber credit. | [WEB] NerdWallet 2026 |
| Citi Double Cash ($0 AF) | 4.0-4.3 | Solid no-fee 2x everywhere. Strong default card. | [WEB] NerdWallet 2026 |
| Capital One Venture X ($395 AF) | 3.8-4.2 | 10K anniversary miles + $300 travel credit offset most of fee. Priority Pass included. | [WEB] TPG 2026 |

**Profile: Low spender ($2K/mo), rarely travels, 720+ credit**

| Card | Expected Score | Rationale |
|------|---------------|-----------|
| Any $0 AF cash back card | 4.0-4.5 | No fee to clear, instant value |
| Any $95+ AF card | 2.5-3.5 | Hard to offset fee at low spend |
| Any $500+ AF card | 1.5-2.5 | Fee almost certainly not offset |

**Anti-pattern: If the scoring system gives CSR a higher score than CSP for a moderate spender who travels 2-3x/year, the Perks Fit or Opportunity Cost dimensions are likely miscalibrated.**

## Statement Credit Programs (Ongoing Value Factor)

These issuer-specific offer programs add real ongoing value that should be factored into Perks Fit scoring:

| Program | Cards | Typical Annual Value | How It Works | Source |
|---------|-------|---------------------|-------------|--------|
| **Amex Offers** | All Amex cards | $200-500+/year | Targeted merchant deals: spend $X, get $Y back or bonus points. Register in app. | [WEB] OMAAT, Upgraded Points |
| **Chase Offers** | All Chase cards | $50-200/year | Similar to Amex Offers but smaller selection and lower values | [WEB] DoC |
| **Citi Merchant Offers** | Citi cards | $50-150/year | Merchant-linked cashback offers | [TRAINING -- lower confidence] |
| **CSR Credit Stack (2026)** | CSR only | Up to $800+ | $300 travel + $250 Edit + $250 hotel one-time. Triple-stackable on qualifying hotel stays. | [WEB] DoC 2026 |
| **Amex Plat Credit Stack (2026)** | Amex Platinum | Up to $1,400+ | $200 hotel + $200 airline + $200 Uber + $200 entertainment + more. Calendar-year resets. | [WEB] Upgraded Points 2026 |
| **Amex Gold Credits** | Amex Gold | Up to $240/year | $120 dining + $120 Uber | [WEB] TPG 2026 |

**Rule**: When scoring Perks Fit, estimate the user's realistic credit redemption rate (typically 50-70% for an active optimizer, 20-40% for a casual user). Never assume 100% utilization.
