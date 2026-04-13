---
name: card-ops
description: >-
  AI-powered credit card evaluation, portfolio optimization, and rewards tracking.
  Routes to the correct mode (evaluate, compare, scan, optimize, tracker) based on
  user intent. Loads issuer rules, points valuations, bonus strategy, portfolio theory,
  risk/timing, and scoring benchmarks from docs/ reference articles. Handles onboarding
  if no profile exists.
  TRIGGER when: user asks to evaluate a credit card offer, compare cards, parse a
  statement, optimize their card portfolio, check card tracker status, asks about
  credit card strategy, mentions a specific card name with intent to evaluate (e.g.,
  "what about the CSP?", "should I get the Amex Gold?"), or provides a card offer URL.
  Also trigger when user says "card-ops" or any variant.
  DO NOT TRIGGER when: user is working on card-ops code/modes/infrastructure (they
  are editing the tool, not using it).
---

# Card-Ops: Credit Card Optimization Pipeline

## Onboarding Check (silent, every invocation)

Before doing anything, check these three files exist:

1. `config/profile.yml` (not just profile.example.yml)
2. `modes/_profile.md`
3. `data/cards.md` (with content beyond the empty template)

**If `config/profile.yml` is missing**, enter onboarding mode:

> "I need a few details to personalize evaluations:
> - Your estimated credit score range (e.g., 740-760)
> - Approximate annual income
> - Current cards you hold (issuer + product name)
> - Your top 3 monthly spending categories and rough amounts
> - Primary reward goal: cash back, travel points, or category perks?
>
> I'll set everything up for you."

Copy `config/profile.example.yml` to `config/profile.yml` and fill from answers. Create `modes/_profile.md` (empty is fine). Create `data/cards.md` from template if missing. Then proceed to the requested mode.

**If profile exists**, proceed directly to mode routing.

## Mode Routing

Determine the mode from user intent. If ambiguous, ask.

| User signal | Mode | Primary file |
|---|---|---|
| Provides a card offer URL, screenshot, or description | **evaluate** | `modes/evaluate.md` |
| Wants to compare 2+ cards side by side | **compare** | `modes/compare.md` |
| Drops statement PDFs or asks to analyze spending | **scan** | `modes/scan.md` |
| Asks to optimize portfolio, audit cards, or find gaps | **optimize** | `modes/optimize.md` |
| Asks about card status, pipeline, or "what have I evaluated?" | **tracker** | `modes/tracker.md` |

## Execution

1. Read `modes/_shared.md` (scoring system, card types, report structure, global rules)
2. Read the mode-specific file from the table above
3. Read `config/profile.yml` (user financial profile)
4. Read `modes/_profile.md` if it exists (user overrides)
5. Follow the mode file's execution steps exactly

### Reference Docs

The mode files contain `[[wikilink]]` references to detailed articles. When you reach a step that references one, read it from `docs/`:

| Reference | File | When to load |
|---|---|---|
| `[[issuer-rules]]` | `docs/issuer-rules.md` | Block B (Eligibility Match) |
| `[[points-valuations]]` | `docs/points-valuations.md` | Block C (Bonus Strategy), Block D (Value Analysis) |
| `[[bonus-strategy]]` | `docs/bonus-strategy.md` | Block C (Bonus Strategy), lifecycle decisions |
| `[[portfolio-strategy]]` | `docs/portfolio-strategy.md` | Block E (Portfolio Optimization), optimize mode |
| `[[transfer-partners]]` | `docs/transfer-partners.md` | Block E, optimize mode, compare mode |
| `[[application-timing]]` | `docs/application-timing.md` | Block F (Application Plan) |
| `[[scoring-benchmarks]]` | `docs/scoring-benchmarks.md` | Scoring calibration, Perks Fit |
| `[[advanced-techniques]]` | `docs/advanced-techniques.md` | When relevant to the user's situation |

Load on demand (when you reach the step that needs them), not all at once.

### Output Locations

- Evaluation reports: `reports/{###}-{issuer-slug}-{YYYY-MM-DD}.md`
- Tracker additions: `batch/tracker-additions/{num}-{issuer-slug}.tsv`
- After evaluation: run `node merge-tracker.mjs` to update cards.md

## Data Contract

**User layer (NEVER auto-update, NEVER commit)**:
- `config/profile.yml`, `modes/_profile.md`
- `data/*`, `reports/*`, `statements/*`

**System layer (safe to update)**:
- `modes/_shared.md`, `modes/evaluate.md`, all other modes
- `CLAUDE.md`, `*.mjs` scripts, `templates/*`, `docs/*`

When the user asks to customize anything (spending categories, reward preferences, issuer priorities), ALWAYS write to `modes/_profile.md` or `config/profile.yml`. NEVER edit `modes/_shared.md` for user-specific content.

## Ethical Guardrails

- NEVER submit a credit card application. Evaluate, score, recommend -- then STOP.
- Strongly discourage poor-fit cards. If score < 3.5, explicitly recommend against applying.
- Never guarantee approval. Frame as probability.
- Flag time-sensitive offers prominently.
