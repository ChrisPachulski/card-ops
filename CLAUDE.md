# Card-Ops -- AI Credit Card Optimization Pipeline

## Origin

Scaffolded from [santifer/career-ops](https://github.com/santifer/career-ops), an AI-powered job search pipeline. This project adapts the same architecture -- structured evaluation, scoring, pipeline tracking, batch processing -- for credit card offers, rewards optimization, and statement analysis.

## Data Contract (CRITICAL)

There are two layers.

**User Layer (NEVER auto-updated, personalization goes HERE):**
- `config/profile.yml`, `modes/_profile.md`
- `data/*`, `reports/*`, `statements/*`

**System Layer (auto-updatable, DON'T put user data here):**
- `modes/_shared.md`, `modes/evaluate.md`, all other modes
- `CLAUDE.md`, `*.mjs` scripts, `templates/*`, `batch/*`

**THE RULE: When the user asks to customize anything (spending categories, reward preferences, issuer priorities), ALWAYS write to `modes/_profile.md` or `config/profile.yml`. NEVER edit `modes/_shared.md` for user-specific content.**

## What is card-ops

AI-powered credit card optimization built on Claude Code: statement parsing, offer evaluation, portfolio optimization, rewards tracking, batch processing.

### Main Files

| File | Function |
|------|----------|
| `data/cards.md` | Card tracker (all evaluated + held cards) |
| `data/pipeline.md` | Inbox of pending offers to evaluate |
| `statements/` | User-provided statement PDFs |
| `reports/` | Evaluation reports (format: `{###}-{issuer-slug}-{YYYY-MM-DD}.md`) |
| `config/profile.yml` | Financial profile + spending patterns + reward goals |
| `modes/` | Skill modes for each workflow |
| `templates/states.yml` | Canonical status lifecycle |
| `templates/issuers.example.yml` | Pre-configured card issuers |
| `merge-tracker.mjs` | Merge batch additions into cards.md |
| `verify-pipeline.mjs` | Pipeline integrity checker |
| `dedup-tracker.mjs` | Duplicate entry removal |
| `normalize-statuses.mjs` | Status canonicalization |
| `analyze-patterns.mjs` | Approval pattern analysis |

### Skill Modes

| If the user... | Mode |
|----------------|------|
| Provides a card offer URL or details | `evaluate` |
| Wants to compare multiple cards | `compare` |
| Drops statement PDFs | `scan` (statement parser) |
| Asks about card status | `tracker` |
| Wants spending optimization | `optimize` |
| Batch processes offers | `batch` |
| Asks about approval patterns | `patterns` |

### First Run -- Onboarding

**Before doing ANYTHING else, check if the system is set up.** Run these checks silently:

1. Does `config/profile.yml` exist (not just profile.example.yml)?
2. Does `modes/_profile.md` exist?
3. Does `data/cards.md` exist?

**If ANY is missing, enter onboarding mode:**

#### Step 1: Financial Profile (required)
> "I need a few details to personalize evaluations:
> - Your estimated credit score range (e.g., 740-760)
> - Approximate annual income
> - Current cards you hold (issuer + product name)
> - Your top 3 monthly spending categories and rough amounts
> - Primary reward goal: cash back, travel points, or category perks?
>
> I'll set everything up for you."

Fill `config/profile.yml` from their answers.

#### Step 2: Statement Upload (recommended)
> "For the most accurate analysis, drop your recent statement PDFs into the `statements/` folder. I'll parse your actual spending to calibrate recommendations. No data leaves your machine."

#### Step 3: Tracker
If `data/cards.md` doesn't exist, create it with the empty template.

#### Step 4: Ready
> "You're all set! You can now:
> - Paste a card offer URL or promo details to evaluate it
> - Drop statement PDFs into `statements/` for spending analysis
> - Run `/card-ops compare` to compare cards side by side
> - Run `/card-ops optimize` for portfolio-wide spending optimization"

### Financial Profile Source of Truth

- `config/profile.yml` is the canonical financial profile
- Statement-derived spending data supplements but never replaces the profile
- **NEVER hardcode spending amounts** -- read them from profile or parsed statements at evaluation time

## Ethical Use -- CRITICAL

- **NEVER submit a credit card application without the user reviewing it first.** Evaluate, score, recommend -- but always STOP before applying. The user makes the final call.
- **Strongly discourage poor-fit cards.** If a score is below 3.5/5, explicitly recommend against applying. Hard inquiries impact credit scores.
- **Quality over quantity.** A well-chosen card portfolio of 3-5 cards beats 10 mediocre ones. Guide toward fewer, better cards.
- **Respect the user's credit health.** Never recommend churning patterns that could damage creditworthiness. Flag risks explicitly.

## Stack and Conventions

- Node.js (mjs modules), YAML (config), Markdown (data)
- Scripts in `.mjs`, configuration in YAML
- Reports in `reports/`
- Batch in `batch/` (gitignored except scripts and prompt)
- Report numbering: sequential 3-digit zero-padded, max existing + 1

### TSV Format for Tracker Additions

Write one TSV file per evaluation to `batch/tracker-additions/{num}-{issuer-slug}.tsv`. Single line, 9 tab-separated columns:

```
{num}\t{date}\t{issuer}\t{card}\t{status}\t{score}/5\t{annual_fee}\t[{num}](reports/{num}-{slug}-{date}.md)\t{note}
```

**Column order:**
1. `num` -- sequential number (integer)
2. `date` -- YYYY-MM-DD
3. `issuer` -- card issuer (Chase, Amex, etc.)
4. `card` -- product name
5. `status` -- canonical status (e.g., Evaluated)
6. `score` -- format `X.X/5` (e.g., `4.2/5`)
7. `annual_fee` -- e.g., `$0`, `$95`, `$550`
8. `report` -- markdown link `[num](reports/...)`
9. `notes` -- one-line summary

### Pipeline Integrity

1. **NEVER edit cards.md to ADD new entries** -- Write TSV in `batch/tracker-additions/` and `merge-tracker.mjs` handles the merge.
2. **YES you can edit cards.md to UPDATE status/notes of existing entries.**
3. All statuses MUST be canonical (see `templates/states.yml`).
4. Health check: `node verify-pipeline.mjs`
5. Normalize statuses: `node normalize-statuses.mjs`
6. Dedup: `node dedup-tracker.mjs`

### Canonical States (cards.md)

**Source of truth:** `templates/states.yml`

| State | When to use |
|-------|-------------|
| `Evaluated` | Report completed, pending decision |
| `Applied` | Application submitted |
| `Approved` | Card approved |
| `Rejected` | Application denied |
| `Pended` | Application under review |
| `Declined` | User declined approved card |
| `Active` | Card in wallet, actively used |
| `Closed` | Account closed |
| `SKIP` | Does not fit, do not apply |

**RULES:**
- No markdown bold (`**`) in status field
- No dates in status field (use the date column)
- No extra text (use the notes column)
