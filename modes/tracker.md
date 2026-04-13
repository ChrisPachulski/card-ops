# Mode: Card Tracker Overview

## Trigger
User asks about card status, pipeline overview, or "what have I evaluated?"

## Execution Steps

### 1. Read Tracker
- Load `data/cards.md`
- Parse all entries
- Read application history from `config/profile-chris.yml` and `config/profile-dana.yml`

### 2. Summary Metrics
Show:
- Total cards evaluated
- Cards by status (Evaluated, Applied, Approved, Rejected, Active, etc.)
- Average score of evaluated cards
- Total annual fees across Active cards
- Estimated total annual rewards across Active cards

### 3. Pipeline Status
- Check `data/pipeline.md` for pending offers
- Check `batch/tracker-additions/` for unmerged TSVs
- If unmerged: offer to run `node merge-tracker.mjs`
- Check `data/analysis/change-flags.yml` for pending flags and display summary

### 4. Recent Activity
- Show last 5 entries by date
- Flag any Applied cards awaiting decision (suggest follow-up)
- Flag any Pended cards (suggest calling reconsideration line)

### 5. Upcoming Actions
- Annual fee renewal dates for Active cards (if tracked in notes)
- Calculate upcoming AF renewal dates from card open dates in profiles
- Cards approaching 1-year mark (downgrade decision window)
- MSR deadlines for recently approved cards
