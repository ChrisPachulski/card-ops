# Card-Ops v2: Three-Layer Architecture

**Date:** 2026-04-12
**Status:** Approved
**Scope:** Restructure card-ops from shallow mode-driven workflows into a three-layer system (ingest, analysis, strategy) that delivers burn-it-all-depth analysis from normal mode invocations.

---

## Problem

Card-ops v1 modes are shallow. Scan mode parses statements one card at a time with no persistence. Optimize mode hand-waves at gap analysis without real math. Evaluate mode requires the user to provide card terms. Getting a proper household analysis required dispatching 27 parallel agents (burn-it-all) to independently parse 260 statement files, research 8 card products, model portfolio scenarios, and reconstruct spending patterns. The system should produce that depth from a single `/card-ops optimize` invocation.

## Architecture

Three layers with clear boundaries:

```
Raw Statements (PDFs, Excel)
        |
        v
  INGEST LAYER (parse.py, normalize.py)
        |
        v
  Parquet Database (data/transactions/)
        |
        v
  ANALYSIS LAYER (spending, subscriptions, trips, trends, rewards, model, market)
        |
        v
  STRATEGY LAYER (scan, evaluate, compare, optimize, tracker, sequence modes)
        |
        v
  Reports, Recommendations, Application Calendar
```

Each layer has one job. Modes compose analyses instead of reimplementing them.

---

## Layer 1: Ingest

### Purpose
Parse raw statements into structured, persistent transaction data. Runs once per batch of new statements. Purely mechanical -- no analysis, no recommendations.

### Files

| File | Purpose |
|---|---|
| `lib/parse.py` | Statement parsing (PDF + Excel). Issuer-specific parsers for Chase PDF, WF PDF, Amex Excel. Detects new statements by comparing filenames to `statement_file` column in existing parquets. Appends only new transactions. |
| `lib/normalize.py` | Merchant normalization + categorization. Regex-based mapping dict from raw merchant strings to (clean_name, category, subcategory). Flags unknowns for manual categorization. Map grows over time. |

### Output
One parquet file per card issuer in `data/transactions/`:
- `amex-bcp.parquet`
- `chase-amazon.parquet`
- `chase-freedom.parquet`
- `wf-active-cash.parquet`
- `wf-checking.parquet`

### Transaction Schema

| Column | Type | Source | Example |
|---|---|---|---|
| `date` | date | statement | 2026-03-15 |
| `merchant_raw` | string | statement | `WEGMANS NAZARETH #94EASTON PA` |
| `merchant` | string | normalize.py | `Wegmans` |
| `amount` | float | statement | 114.52 |
| `category` | string | normalize.py | `Groceries` |
| `subcategory` | string | normalize.py | `Supermarket` |
| `cardholder` | string | statement | `dana` |
| `card` | string | filename/config | `amex-bcp` |
| `earn_rate` | float | rewards.py | 0.06 |
| `reward_amount` | float | computed | 6.87 |
| `is_recurring` | bool | subscriptions.py | False |
| `merchant_state` | string | statement | `PA` |
| `statement_file` | string | filename | `2023-01-27.pdf` |

### Standard Categories (19)

| Category | What it captures |
|---|---|
| Groceries | Wegmans, Trader Joe's, Fred Meyer, Costco (in-store), QFC, Acme |
| Dining | Restaurants, coffee shops, breweries, fast food |
| Delivery | DoorDash, Uber Eats, Grubhub |
| Amazon | Amazon.com, Marketplace, Prime, Audible, AWS |
| Gas | Sheetz, Fred Meyer Fuel, Costco Gas, Union 76 |
| Streaming | Netflix, Spotify, Disney+, Hulu, YouTube Premium |
| Software | DigitalOcean, OpenAI, Docker, Adobe, Cursor, Coursera |
| Telecom | DirecTV Stream, Comcast, phone plans |
| Shopping | Target, TJMaxx, Marshalls, Old Navy, online retail |
| Home | Home Depot, IKEA, contractors, furniture |
| Healthcare | Vet, medical, dental, pharmacy |
| Travel | Airlines, hotels, Airbnb, car rental, Chase Travel |
| Entertainment | MagicCon, events, recreation |
| Alcohol | Wine & Spirits, liquor stores (NOT grocery-bundled) |
| Childcare | KinderCare, daycare |
| Insurance | Progressive, auto insurance |
| Utilities | Electric, gas, water, sewer, trash |
| Shipping | Pirate Ship, USPS, UPS |
| Other | Everything else |

Dining and Delivery are separate because they earn different rates on some cards and DoorDash MCC coding is a risk factor on certain issuers.

### Merchant Normalization Map

`normalize.py` maintains a dict:

```python
MERCHANT_MAP = {
    r"WEGMANS.*": ("Wegmans", "Groceries", "Supermarket"),
    r"DD \*DOORDASH.*": ("DoorDash", "Delivery", "Food Delivery"),
    r"APPLE\.COM/BILL.*": ("Apple.com/Bill", "Software", "Subscription"),
    r"COSTCO WHSE.*": ("Costco", "Groceries", "Warehouse"),
    r"SHEETZ.*": ("Sheetz", "Gas", "Gas Station"),
    r"TRADER JOE.*": ("Trader Joes", "Groceries", "Supermarket"),
    r"NETFLIX.*": ("Netflix", "Streaming", "Video"),
    r"SPOTIFY.*": ("Spotify", "Streaming", "Music"),
    r"DIGITALOCEAN.*": ("DigitalOcean", "Software", "Cloud Hosting"),
    r"OPENAI.*|CHATGPT.*": ("OpenAI", "Software", "AI"),
    r"ANTHROPIC.*": ("Anthropic", "Software", "AI"),
    # ... grows over time
}
```

New merchants not matching any pattern get `category="Other"` and are flagged in parse output: "X new merchants need categorization."

---

## Layer 2: Analysis

### Purpose
Read the parquet database and produce structured findings. These are Python modules with pure functions -- no side effects beyond writing cached output files. Any mode can call any module.

### Module Inventory

| Module | Input | Output | Purpose |
|---|---|---|---|
| `lib/spending.py` | All parquets + household.yml | `data/analysis/spending-profile.yml` | Household spending summary: monthly by category, by card, by cardholder. Category totals, trends, top merchants. |
| `lib/subscriptions.py` | All parquets | `data/analysis/subscription-audit.yml` | Detect recurring charges (same merchant, similar amount, regular frequency). Flag duplicates, total burn rate, optimal card per subscription. |
| `lib/trips.py` | All parquets | `data/analysis/trips.yml` | Cluster airline + hotel + car rental + location-specific charges into trip objects with dates, destination, travelers, total cost. |
| `lib/trends.py` | All parquets + last analysis date | `data/analysis/change-flags.yml` | Compare trailing 3 months to prior 3 months. Flag category shifts, new/stopped recurring merchants, geographic changes, cap warnings. |
| `lib/rewards.py` | All parquets + household.yml + profiles | Rewards summary dict | Calculate actual rewards earned per card per category. Identify leaks (spend earning below best available rate). Produce routing optimization table. |
| `lib/model.py` | Spending profile + candidate cards | Scenario comparison dicts | Portfolio modeler. Takes current portfolio + N candidate cards, computes optimal routing and net rewards for each scenario. Pure math, no web search. |
| `lib/market.py` | Card name or issuer | Updated `data/market/current-offers.yml` | Web search for current signup bonus, earn rates, AF. Writes to cache with timestamp. Checks staleness before searching. |

### Change Detection (trends.py)

#### Detection Rules

| Signal | Threshold | Flag Type | Severity |
|---|---|---|---|
| Category spend shift | >25% in top-5 category, trailing 3mo vs prior 3mo | `category_shift` | high |
| New recurring merchant | Same merchant 3+ times in 3 months, not seen before | `new_recurring` | high if >$500/mo, medium otherwise |
| Stopped recurring merchant | Previously monthly merchant absent 2+ months | `stopped_recurring` | low |
| Geographic shift | >50% of transactions in new state | `relocation` | high |
| Portfolio change | Card added/removed in profile | `portfolio_change` | high |
| Grocery cap approaching | BCP grocery spend >$4,500 YTD | `cap_warning` | medium |
| Subscription cost spike | Recurring charges up >15% MoM | `subscription_spike` | medium |

#### change-flags.yml Format

```yaml
generated: "2026-04-12"
baseline_period: "2025-10 to 2025-12"
current_period: "2026-01 to 2026-03"

flags:
  - type: "category_shift"
    category: "Delivery"
    baseline_monthly: 201
    current_monthly: 706
    change_pct: 251
    severity: "high"
    recommendation: "Run optimize -- DoorDash spending tripled post-move"

  - type: "new_recurring"
    merchant: "KinderCare"
    monthly_amount: 1450
    first_seen: "2026-01"
    severity: "high"
    recommendation: "New $1,450/mo expense -- update household.yml and re-run optimize"

  - type: "cap_warning"
    card: "amex-bcp"
    category: "Groceries"
    ytd_spend: 4800
    cap: 6000
    projected_cap_date: "2026-06"
    severity: "medium"
    recommendation: "BCP grocery cap will hit ~June -- switch overflow to next-best card"

requires_full_reanalysis: true
```

#### How Modes Use Flags

- Any mode checks `change-flags.yml` on startup
- If `requires_full_reanalysis: true` and mode is NOT optimize: print suggestion, proceed anyway
- Optimize mode clears flags after completing a full review
- Scan mode generates flags, never consumes them

### Intelligence Layer (market.py)

#### Staleness Rules

| Data type | Stale after | Rationale |
|---|---|---|
| Signup bonus | 30 days | Change frequently, elevated offers expire |
| Earn rates | 90 days | Changes announced in advance |
| Issuer rules | 180 days | Change ~1-2x/year |
| Annual fee | 90 days | Rarely changes mid-year |

#### current-offers.yml Format

```yaml
cards:
  citi-custom-cash:
    fetched: "2026-04-12"
    signup_bonus: "$200"
    msr: "$1,500 in 6 months"
    annual_fee: 0
    earn_rates:
      top_category: "5% (up to $500/billing cycle)"
      other: "1%"
    eligible_categories: [restaurants, gas, grocery, drugstores, home_improvement, fitness, live_entertainment, travel, transit, streaming]
    notes: "DoorDash codes as dining in practice (MCC 5812) despite terms excluding delivery. One per person via direct application."
    sources: ["citi.com", "doctorofcredit.com"]
```

#### rule-updates.yml Format

```yaml
updates:
  - issuer: "US Bank"
    rule: "Altitude Go dining cap"
    change: "4% dining capped at $2,000/quarter as of April 2025"
    fetched: "2026-04-12"
    wiki_article: "issuer-rules.md"
    wiki_still_accurate: false
```

Modes check `rule-updates.yml` first, fall back to wiki. When a rule update contradicts the wiki, mode uses the update.

#### market.py Behavior

```
market.fetch("citi-custom-cash"):
  1. Check current-offers.yml for entry
  2. If fresh (within staleness threshold): return cached
  3. If stale or missing:
     a. Web search: "{card name} signup bonus {current year}"
     b. Web search: "{card name} earn rates"
     c. Parse into structured format
     d. Write to current-offers.yml with timestamp
     e. Return new data
```

Always on-demand, always targeted. No batch refresh.

---

## Layer 3: Strategy (Modes)

### Mode Composition

Each mode is a workflow that calls analysis modules in a specific order. The depth comes from the modules, not the mode.

#### scan.md (Statement Ingestion)

1. `parse.py` -- parse new statements, update parquets
2. `normalize.py` -- called by parse.py per transaction
3. `spending.py` -- rebuild spending profile
4. `subscriptions.py` -- detect recurring charges
5. `trends.py` -- compare to prior baseline, write change flags
6. Print: new transactions added, spending summary, change flags
7. If flags exist: "Spending patterns shifted. Run optimize for a full review."

Scan is purely about ingesting data and detecting changes. No card recommendations.

#### optimize.md (Portfolio Review)

1. Check parquet freshness -- prompt scan if new statements exist
2. `spending.py` -- current spending profile
3. `rewards.py` -- current rewards + leak table
4. `model.py` -- run scenarios (current routing fix, +1 card, +2 cards, +3 cards)
5. `market.py` -- refresh current offers for recommended candidates (if stale)
6. Read `profile-*.yml` for eligibility
7. If `household.yml` has `side_business.exists: true`, include business card scenarios
8. Output: current rewards, routing fixes, ranked recommendations with dollar math, sequence suggestion

#### evaluate.md (Single Card)

1. `market.py` -- current card terms
2. Read parquets + spending profile
3. `rewards.py` -- project annual value with candidate added
4. `model.py` -- portfolio with vs without
5. Read `profile-*.yml` for eligibility (5/24, issuer rules)
6. Score per existing Block A-F framework
7. Write report + tracker TSV

Existing Block A-F structure and scoring system unchanged.

#### compare.md (Multi-Card)

Same structure as v1 but calls `model.py` for side-by-side value using actual spending data.

#### tracker.md (Overview)

Existing functionality plus:
- Application history from `profile-*.yml`
- Next recommended application window
- Upcoming AF renewal dates from card open dates
- Change flags summary if any exist

#### sequence.md (New -- Application Planning)

1. Read both `profile-*.yml` for 5/24, inquiry counts, issuer history
2. `model.py` -- rank candidates by year-1 value
3. `market.py` -- current SUBs for candidates
4. Apply issuer velocity rules (wiki + rule-updates.yml)
5. Bureau management (spread inquiries across EX/TU/EQ)
6. Output: month-by-month calendar, MSR feasibility vs spending profile, projected 5/24 at each step, year-1 value estimate

---

## Configuration

### profile-chris.yml / profile-dana.yml

Per-applicant credit data. One file per person.

```yaml
identity:
  name: "Chris Pachulski"
  role: "primary"

credit:
  score: 778
  score_bureau: "Experian"
  score_date: "2026-04-12"
  annual_income: 137500
  bonus_pct: 20

cards:
  - issuer: "Chase"
    card: "Amazon Prime Visa Signature"
    opened: "2017-01"
    credit_limit: 12800
  - issuer: "Wells Fargo"
    card: "Active Cash"
    opened: "2024-10"
    credit_limit: 16000
  - issuer: "American Express"
    card: "Blue Cash Preferred"
    opened: "2022-12"
    credit_limit: null

applications:
  history: []
  five_24_count: 0
  inquiries_6mo:
    experian: 0
    transunion: 0
    equifax: 0

issuer_status:
  chase:
    sapphire_ever: false
    ink_ever: false
  amex:
    lifetime_bonuses: ["Blue Cash Preferred"]
    credit_card_count: 1
  citi:
    cards_ever: []
  capital_one:
    cards_held: 0
```

### household.yml

Shared household data.

```yaml
location:
  current: "Covington, WA"
  state: "WA"
  moved_from: "Palmer Township, PA"
  move_date: "2026-01-01"

income:
  household_gross: 257500

memberships:
  - "Costco (warehouse, no Citi card)"
  - "Amazon Prime"
  - "Audible"
  - "DashPass"

side_business:
  exists: true
  type: "sole_proprietorship"
  description: "MTG card sales via TCGPlayer"
  qualifies_for_business_cards: true

strategy:
  primary_goal: "cash_back"
  anti_goals: ["travel_points"]

wallet_routing:
  groceries_primary: "amex-bcp"
  groceries_overflow: "wf-active-cash"
  dining: "chase-freedom"
  doordash: "chase-freedom"
  amazon: "chase-amazon"
  gas: "amex-bcp"
  streaming: "amex-bcp"
  costco: "wf-active-cash"
  everything_else: "wf-active-cash"

life_events:
  - date: "2026-01-01"
    type: "relocation"
    detail: "PA to WA"
    impact: "grocery stores changed, no state income tax, new utility providers"
  - date: "2026-01-01"
    type: "new_expense"
    detail: "KinderCare daycare $1,450/mo"
  - date: "2026-01-01"
    type: "asset_event"
    detail: "PA home sold, $127,890 net proceeds"

analysis:
  last_full_analysis: null
  last_parse: null
  pending_flags: []
```

---

## Data Contract (unchanged)

**User Layer (NEVER auto-updated):**
- `config/profile-chris.yml`, `config/profile-dana.yml`, `config/household.yml`
- `modes/_profile.md`
- `data/*`, `reports/*`, `statements/*`

**System Layer (safe to update):**
- `modes/_shared.md`, `modes/evaluate.md`, all other mode files
- `lib/*.py` (analysis modules)
- `CLAUDE.md`, `*.mjs` scripts, `templates/*`

When the user asks to customize anything, write to config files or `_profile.md`. Never edit `_shared.md` for user-specific content.

---

## What Stays Unchanged

- Report format and numbering (`{###}-{issuer-slug}-{YYYY-MM-DD}.md`)
- Tracker (cards.md) and pipeline (pipeline.md)
- Batch processing system and .mjs scripts
- Wiki reference articles (docs/)
- Templates (states.yml, issuers.example.yml)
- Scoring system (5-dimension weighted, Blocks A-F)
- Ethical guardrails (never apply, discourage poor-fit, quality over quantity)

---

## Implementation Order

1. **Ingest layer first** -- parse.py + normalize.py + parquet schema. This is the foundation everything else depends on. Seed the merchant map from the burn-it-all analysis (we already identified 341 unique merchants).
2. **Core analysis modules** -- spending.py, rewards.py, subscriptions.py, trends.py. These produce the outputs that modes need.
3. **Config migration** -- split profile.yml into profile-chris.yml, profile-dana.yml, household.yml. Populate from current data.
4. **Mode rewrites** -- update scan.md and optimize.md to reference the new modules. Update evaluate.md and compare.md to use parquet data.
5. **Intelligence layer** -- market.py + current-offers.yml. Seed with burn-it-all research data.
6. **Portfolio modeler** -- model.py with scenario functions. Port the math from the burn-it-all portfolio-model agent.
7. **New sequence mode** -- sequence.md + application calendar logic.
8. **Trip reconstruction + change detection** -- trips.py, trends.py with change-flags.yml.
