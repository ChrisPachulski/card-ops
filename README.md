# card-ops

AI-powered credit card evaluation, portfolio optimization, and rewards tracking built on [Claude Code](https://docs.anthropic.com/en/docs/claude-code).

## What it does

- **Evaluate** a card offer: paste a URL or describe an offer, get a scored report with eligibility check, bonus strategy, value analysis, portfolio fit, and application plan
- **Compare** cards side by side with head-to-head analysis and application sequencing
- **Scan** statement PDFs to map actual spending to card earn rates
- **Optimize** your portfolio: find gaps, audit annual fees, recommend adds/downgrades
- **Track** your card pipeline: evaluations, applications, approvals, upcoming actions

## Setup

1. Clone this repo
2. Open it in Claude Code (CLI, VS Code, or JetBrains)
3. Say "evaluate this card" or paste a card offer URL
4. Claude will walk you through onboarding (credit score, income, current cards, spending, goals) on first run

Your financial profile is stored locally in `config/profile.yml` and **never leaves your machine**.

## How it works

Card-ops is a set of structured modes (prompt instructions) that Claude follows when evaluating cards. The `docs/` directory contains reference articles on issuer rules, points valuations, bonus strategies, portfolio theory, and application timing -- all sourced from Doctor of Credit, The Points Guy, NerdWallet, Frequent Miler, and One Mile at a Time.

The `/card-ops` skill routes your intent to the right mode automatically:

| You say | Mode |
|---|---|
| *paste a card offer URL* | evaluate |
| "compare CSP vs Amex Gold" | compare |
| "analyze my spending" | scan |
| "optimize my portfolio" | optimize |
| "what have I evaluated?" | tracker |

## Project structure

```
card-ops/
  .claude/skills/card-ops/   # Claude Code skill (invokable via /card-ops)
  config/
    profile.example.yml       # Template -- copy to profile.yml and fill in
  data/                       # Your card tracker and pipeline (gitignored)
  docs/                       # Reference articles (issuer rules, valuations, etc.)
  modes/                      # Mode instructions for Claude
    _shared.md                # Scoring system, card types, report structure
    evaluate.md               # Card evaluation workflow
    compare.md                # Side-by-side comparison
    scan.md                   # Statement parsing
    optimize.md               # Portfolio optimization
    tracker.md                # Pipeline overview
  reports/                    # Evaluation reports (gitignored)
  statements/                 # Your statement PDFs (gitignored)
  templates/                  # Status definitions, issuer examples
  batch/                      # Merge scripts for tracker
  *.mjs                       # Pipeline utilities (merge, dedup, normalize, verify)
```

## Privacy

The `.gitignore` is built around a strict data contract:

**Never committed** (user data):
- `config/profile.yml` -- your credit score, income, cards, spending
- `statements/` -- bank statement PDFs (blocked globally: `*.pdf`, `*.ofx`, `*.qfx`, `*.csv`, `*.xlsx`)
- `reports/` -- personalized evaluations
- `data/cards.md` -- your card portfolio
- `modes/_profile.md` -- personal preference overrides
- Images, archives, credentials, database files

**Always committed** (system layer):
- Mode instructions, reference docs, scripts, templates, config examples

## Reference docs

The `docs/` directory contains expert-level reference articles covering:

| Article | Content |
|---|---|
| `issuer-rules.md` | 7 issuers, 25+ rules (Chase 5/24, Amex pop-up jail, Citi 48-month, etc.) |
| `points-valuations.md` | 6 transferable currencies, 12 transfer partners, valuation methodology |
| `bonus-strategy.md` | MSR achievement tiers, clawback risk, referrals, retention offers, upgrade paths |
| `portfolio-strategy.md` | Ecosystem trifectas, AF stacking math, AAoA impact |
| `application-timing.md` | Bureau preferences, inquiry sensitivity rankings, spacing rules |
| `scoring-benchmarks.md` | Calibration benchmarks, statement credit programs |
| `transfer-partners.md` | 15-partner, 4-currency overlap matrix |
| `advanced-techniques.md` | Credit freeze, AU strategy, NLL offers, gardening |

All sourced from Doctor of Credit, The Points Guy, NerdWallet, Frequent Miler, OMAAT, and Upgraded Points (April 2026). Refresh quarterly.

## Ethical guardrails

- Card-ops **never submits applications** -- it evaluates, scores, and recommends, then stops
- Cards scoring below 3.5/5 get an explicit "recommend against" flag
- Approval is always framed as probability, never certainty
- No manufactured spending recommendations
