
# MSR & Bonus Strategy

Covers minimum spend requirement achievement, clawback risk, referral bonuses, retention offers, and upgrade/downgrade paths. For eligibility rules that govern which bonuses you can receive, see [[issuer-rules]]. For cpp valuations used in bonus value calculations, see [[points-valuations]].

## MSR Achievement Framework

When evaluating whether a user can hit MSR (minimum spend requirement), use this tiered approach:

**Tier 1: Organic Spend (preferred, zero risk)**
- Map user's monthly spending from `config/profile.yml` to MSR window
- Formula: `monthly_spending.total * MSR_window_months >= MSR_amount` -> can hit organically
- If organic covers 80%+, flag as "likely achievable with minor timing adjustments"

**Tier 2: Safe Acceleration (low risk)**
These methods accelerate spend without manufactured spending:
- Prepay recurring bills (insurance, utilities, phone -- 3-6 months ahead)
- Shift timing: make planned large purchases during MSR window (furniture, electronics, travel)
- Pay taxes via credit card (IRS accepts via pay1040.com, ~1.87% fee -- only worth it for large bonuses)
- Buy gift cards for stores you already shop at (Amazon, grocery)
- Add authorized users who have their own organic spend

**Tier 3: Manufactured Spending Awareness (higher risk, disclosure required)**
Card-ops does NOT recommend MS, but evaluations should acknowledge it exists:
- Buying prepaid Visa/MC gift cards and liquidating via money order is the classic MS method
- Plastiq (up to 2.9% fee) enables card payments for rent/mortgage
- **Amex specifically excludes** from MSR: prepaid cards, gift cards, P2P payments, cash equivalents
- **Risk**: Account closure, bonus clawback, relationship damage with issuer
- **Rule**: If a user asks about MS, describe the risks. Never present MS as a recommended strategy.

## Clawback Risk Framework

Issuers can reclaim welcome bonuses. Know the triggers:

| Issuer | Clawback Trigger | Mitigation | Source |
|--------|-----------------|------------|--------|
| **Amex** | Close/downgrade within 12 months; returns of purchases used for MSR; excessive gift card purchases; self-referrals | Keep card open 13+ months minimum. Do not return MSR-qualifying purchases. | [WEB] TPG, DoC |
| **Chase** | Returning purchases that brought you below MSR after bonus posts; account abuse | Keep spend above MSR threshold even after bonus posts | [WEB] TPG |
| **Citi** | Less aggressive on clawbacks, but can claw back for fraud/abuse | Standard precautions apply | [TRAINING -- lower confidence] |
| **General** | All issuers reserve contractual right to clawback for "abuse" | Wait 12+ months before closing any card with a welcome bonus | [WEB] TPG |

## Referral Bonus Overlay

Referral bonuses add value beyond the welcome offer. Factor these into evaluations when the user has existing cards:

| Issuer | Referral Bonus (typical) | Annual Cap | Notes | Source |
|--------|------------------------|------------|-------|--------|
| **Chase** | 10,000-20,000 UR per referral | 100,000 UR/year (Sapphire cards) | Covers most Chase cards including co-brands | [WEB] TPG |
| **Amex** | 10,000-30,000 MR per referral | 55,000 MR/year (Platinum); varies by card | Self-referrals BANNED -- Amex actively claws back | [WEB] DoC |
| **Capital One** | Varies by card | 100,000 miles/year (Venture X), 50,000 (Venture) | | [WEB] TPG |

**Rule**: When evaluating a card the user already holds a card in the same family, note the referral opportunity ("refer from your existing CSP before applying for CSR").

## Retention Offer Strategy

Annual fee cards should be evaluated for retention before closing/downgrading:

| Issuer | Best Timing | Typical Offers | Frequency | Source |
|--------|-------------|---------------|-----------|--------|
| **Chase** | When AF posts, or 60 days after approval | 3,000-10,000 UR; AF waiver at year 1 | ~Every 12 months | [WEB] DoC |
| **Amex** | 12-month mark; call during daytime | 3,000-10,000 MR; can ask every 90 days | Multiple per year possible | [WEB] DoC |
| **Citi** | 60 days, 180 days, new calendar year, 360 days | 3,000-10,000 miles; $95 credit | Multiple per year | [WEB] DoC |
| **BofA** | When AF posts; 6-month mark | AF waiver; small mileage bonuses | ~Every 6-12 months | [WEB] DoC |
| **Capital One** | Limited | AF waivers only | Infrequent | [WEB] DoC |

**Script**: "I'm considering my options for this card. The annual fee is coming up, and I want to make sure the card still makes sense for me. Are there any offers available on my account?"

## Upgrade/Downgrade Paths

Product changes preserve credit history and avoid hard inquiries:

**Chase paths:**
- CSR -> CSP -> Freedom Unlimited or Freedom Flex (must hold 12+ months before change)
- CSP -> CSR (upgrade; new AF applies, may get upgrade bonus offer)
- One Sapphire rule: cannot hold CSR and CSP simultaneously

**Amex paths:**
- Platinum -> Gold (downgrade within same brand family)
- Gold -> Green or Blue Business Plus
- Delta Platinum -> Delta Gold -> Delta Blue
- Must stay within same card family (Delta -> Delta, not Delta -> Hilton)

**Citi paths:**
- Premier -> Custom Cash or Double Cash
- Product change rules vary; call to check available options

**General rules:**
- Wait 12+ months before any product change (clawback risk)
- Product changes do NOT trigger new welcome bonuses (in most cases)
- Upgrade offers from issuer (via email/app) MAY include a bonus -- these are exceptions worth taking
- Downgrading preserves: credit line, account age, points balance
- Downgrading does NOT preserve: card-specific perks, earn rates
