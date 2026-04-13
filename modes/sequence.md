# Mode: Application Sequencing

## Trigger
User asks "when should I apply", "what's next", "application plan", or "sequence".

## Inputs
- `config/profile-chris.yml`, `config/profile-dana.yml` (eligibility)
- `config/household.yml` (spending, strategy, side business)
- `data/analysis/spending-profile.yml` (monthly spend for MSR feasibility)
- `data/market/current-offers.yml` (current signup bonuses)
- `docs/issuer-rules.md` + `data/market/rule-updates.yml` (velocity rules)
- `docs/application-timing.md` (bureau pulls, inquiry sensitivity)

## Execution Steps

### 1. Eligibility Snapshot
Read both applicant profiles. For each person, report:
- Current 5/24 count
- Inquiry counts by bureau (last 6 months)
- Cards held by issuer
- Issuer-specific restrictions (Amex lifetime, Citi 48-month, etc.)

### 2. Candidate Ranking
Use `lib/model.py` to rank candidate cards by year-1 value (signup bonus + ongoing rewards - AF) against actual spending data.

Check `data/market/current-offers.yml` for current SUBs. If stale, run targeted web searches.

Include business cards if `household.yml` has `side_business.exists: true`.

### 3. Velocity Rules
Apply issuer-specific spacing rules from `docs/issuer-rules.md`:
- Chase: 2/30, 3-month spacing between business cards
- Citi: 1/8, 2/65
- Capital One: save for last (triple-pull)
- US Bank: inquiry-sensitive, sequence early when profile is clean
- BofA: 2/3/4 rule
- Amex: 1/5, 2/90

### 4. Bureau Management
Map each candidate card to its likely bureau pull (from `docs/application-timing.md`). Spread inquiries across Experian, TransUnion, Equifax.

### 5. MSR Feasibility
For each month in the sequence, check: can the household hit MSR from organic spend? Use monthly spending from `data/analysis/spending-profile.yml`. Flag months where MSR exceeds 70% of monthly spend.

### 6. Output
Produce a month-by-month calendar:

| Month | Applicant | Card | Signup Bonus | MSR | Bureau | 5/24 After |
|---|---|---|---|---|---|---|

Include:
- Total year-1 value (all bonuses + ongoing)
- Year-2+ ongoing value
- Final 5/24 status for both applicants
- Any timing constraints (mortgage planned, AU impact, etc.)
