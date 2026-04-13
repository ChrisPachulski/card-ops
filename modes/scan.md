# Mode: Scan (Statement Ingestion)

## Trigger
User drops statement PDFs/Excel into `statements/` or asks to parse/analyze spending.

## Inputs
- New statement files in `statements/{issuer}/`
- Existing parquets in `data/transactions/`

## Execution Steps

### 1. Parse New Statements
Run `parse_new_statements()` from `lib/parse.py`. This detects which statement files are new (not yet in parquets), parses them, and appends to the appropriate parquet.

```python
from lib.parse import parse_new_statements
results = parse_new_statements()
```

Report: "{N} new transactions parsed for {card}" for each card with new data. If no new statements found, report that and stop.

### 2. Build Spending Profile
Run `build_spending_profile()` from `lib/spending.py` to rebuild the household spending summary.

```python
from lib.spending import build_spending_profile, print_spending_summary
profile = build_spending_profile(months=12)
print_spending_summary(profile)
```

### 3. Detect Subscriptions
Run `detect_subscriptions()` from `lib/subscriptions.py` to identify recurring charges.

```python
from lib.subscriptions import detect_subscriptions
subs = detect_subscriptions(months=6)
```

Report top subscriptions by monthly cost, flag any that seem duplicative or wasteful.

### 4. Detect Changes
Run `detect_changes()` from `lib/trends.py` to compare recent spending to baseline.

```python
from lib.trends import detect_changes
changes = detect_changes()
```

Report all flags with severity and recommendation.

### 5. Output
- Print spending summary (categories, cards, top merchants)
- Print subscription audit highlights
- Print change flags
- If `requires_full_reanalysis` is true: "Spending patterns have shifted significantly. Run optimize for a full portfolio review."

Scan is purely about ingesting data and detecting changes. No card recommendations -- that is optimize's job.
