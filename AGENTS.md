# Card-Ops for Codex

Read `CLAUDE.md` for all project instructions, routing, and behavioral rules. They apply equally to Codex.

Key points:
- Reuse the existing modes, scripts, templates, and tracker flow -- do not create parallel logic.
- Store user-specific customization in `config/profile-chris.yml`, `config/profile-dana.yml`, `config/household.yml`, or `modes/_profile.md` -- never in `modes/_shared.md`.
- Never submit a credit card application on the user's behalf.

## Workflow

### First run -- onboarding

Before doing anything else, check silently whether `config/profile-chris.yml` (not just `profile.example.yml`), `modes/_profile.md`, and `data/cards.md` all exist. If any is missing:

1. **Financial profile (required).** Ask for: estimated credit score range, approximate annual income, current cards held (names only), and primary reward goal (cash back / travel points / category perks).
   - Earn rates for named cards come from `lib/card_lookup.py::lookup_card(name)` if found. If not found, web-search the issuer's product page, verify rates, and call `lib/card_lookup.py::add_card(...)` to persist it for future sessions -- then use the looked-up rates.
   - Fill `config/profile-{name}.yml` from the answers plus looked-up rates.
2. **Statement upload (recommended).** Ask the user to drop recent statement PDFs into `statements/` for spending-calibrated analysis; no data leaves the machine.
3. **Tracker.** If `data/cards.md` doesn't exist, create it from the empty template.
4. **Ready.** Tell the user they can now paste a card offer to evaluate, drop statements for analysis, or run `/card-ops compare` / `/card-ops optimize`.

### Market scan

The card database must cover the full market. On first setup, or when `wiki/card-ops/cards/` has fewer than 50 articles, run a full scan: parallel agents per issuer, web-search product pages, create wiki articles, then `python lib/generate_known_cards.py`. Full procedure in SKILL.md.

### Staleness check

On every invocation, check the most recent `updated` date under `wiki/card-ops/cards/`. If it's more than 30 days old, prompt the user to re-scan.

### Tracker additions (TSV format)

Write one TSV file per evaluation to `batch/tracker-additions/{num}-{issuer-slug}.tsv` -- a single line, 9 tab-separated columns:

```
{num}\t{date}\t{issuer}\t{card}\t{status}\t{score}/5\t{annual_fee}\t[{num}](reports/{num}-{slug}-{date}.md)\t{note}
```

Column order: `num` (sequential integer), `date` (YYYY-MM-DD), `issuer`, `card`, `status` (canonical, see below), `score` (`X.X/5`), `annual_fee` (e.g. `$0`, `$95`), `report` (markdown link), `notes` (one line).

### Canonical states (`data/cards.md`)

Source of truth: `templates/states.yml`.

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


## THE COMPRESSION LIE — ABSOLUTE TABOO
Acting on a summary or recall of an instruction or artifact while presenting
the work as if the instruction itself was executed. When an instruction or
workflow establishes a source-of-record (spec, theme doc, plan, config, prompt
file), every execution step MUST mechanically read and consume that artifact —
never memory of it, never a condensed rewrite of it. You are NEVER permitted
to decide a shortcut is "good enough" against an express instruction; that
determination belongs to the user alone. If executing the artifact verbatim is
impossible or seems wrong, STOP and say so before spending anything (tokens,
credits, money, outbound sends). Named 2026-08-20; memory:
feedback-the-compression-lie.


## ASSERT-THEN-VERIFY — ABSOLUTE TABOO
Stating a result as fact ("it is synced", "it is deployed", "every machine
inherits it") BEFORE mechanically verifying it, with the check running only
after the user challenges the claim. Every claim of state ships WITH its
verification evidence, and the check runs BEFORE the sentence is written —
never after. A claim that cannot be verified right now is labeled unverified
at first utterance, not defended later. Named 2026-08-20; memory:
feedback-assert-then-verify-taboo.
