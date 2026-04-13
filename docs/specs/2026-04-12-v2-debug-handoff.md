# Card-Ops v2 Debug Handoff

**Date:** 2026-04-12
**Status:** Architecture complete, modules need debugging before output can be trusted
**Priority:** Fix parsers and rewards logic before any mode is used for real decisions

---

## What Was Built This Session

1. **Burn-it-all analysis** (27 agents, 260 statements) -- produced a comprehensive household optimization report at `reports/005-household-optimization-2026-04-12.md`. The findings in that report are verified against raw statement data and can be trusted.

2. **V2 three-layer architecture** -- spec at `docs/specs/2026-04-12-card-ops-v2-design.md`. Ingest (parse/normalize), Analysis (spending/subscriptions/trends/rewards/model/market), Strategy (modes). Design is approved.

3. **8 Python modules** in `lib/` -- all written, committed, structurally complete. But output cannot be trusted yet due to the bugs below.

4. **Config migration** -- `profile.yml` split into `profile-chris.yml`, `profile-dana.yml`, `household.yml`. Data is accurate.

5. **Mode rewrites** -- scan, optimize, evaluate, compare, tracker updated. New sequence mode added. These reference the lib modules correctly but will produce bad output until the modules are fixed.

6. **Market cache seeded** -- `data/market/current-offers.yml` has 11 card products with current (Apr 2026) offers. `data/market/rule-updates.yml` has 6 issuer rule changes.

---

## What Is Broken

### Bug 1: Parsers are dropping transactions (CRITICAL)

**Evidence:** The burn-it-all agents (which parsed each statement individually with custom logic) found:
- Amex BCP: 520 transactions, $39,375 over 26 months (~$1,090/mo)
- Amazon Prime Visa: 555 transactions, $30,560 over 24 months (~$1,273/mo)
- WF Active Cash: 1,049 transactions, $116,750 over 19 months (~$6,145/mo)
- CFU: 360 transactions, $21,293 over 24 months (~$852/mo)

The lib parsers report $58,636/yr total CC spend. At the known monthly rates, actual spend is ~$112K/yr. The parsers are capturing roughly half the transactions.

**Root cause (suspected):** The regex patterns in `parse_chase_pdf()` and `parse_wf_pdf()` don't handle:
- Multi-line merchant descriptions (description wraps to next line, amount is on a different line)
- Transactions where the amount column isn't at the end of the line
- Section boundaries that don't match the expected headers exactly
- Year rollover edge cases
- Statement format variations across years (older statements may have different layouts)

**How to debug:**
1. Pick one statement per card where the parser count is known (from burn-it-all agent output)
2. Compare parser output transaction count vs actual transaction count
3. Print the raw pdfplumber text and find the lines the regex is missing
4. Fix the regex or parsing logic
5. Re-parse all statements and verify totals match burn-it-all findings

**Ground truth to validate against:**
- Amex: 520 charges across 3 Excel files (this should be easiest -- Excel parsing was more reliable)
- Amazon: ~23 transactions per month average
- WF Active Cash: ~55 transactions per month average
- CFU: ~15 transactions per month average

### Bug 2: rewards.py doesn't model the BCP grocery cap (CRITICAL)

**The error:** The rewards calculator sees grocery spend on WF/CFU/Amazon cards and flags it as a "leak" suggesting it should go to the BCP at 6%. But the BCP has a $6,000/yr cap on the 6% rate -- after the cap, it drops to 1%. The household deliberately maxes the 6% tier (~$500/mo on BCP) and routes overflow to WF at 2%.

This was explicitly discussed and corrected early in the session. The user called out the first analysis for the same mistake. Building a module that repeats the error is a trust violation.

**The fix:** `calculate_rewards()` in `rewards.py` must:
1. Track YTD grocery spend on BCP against the $6,000 cap
2. For grocery spend ABOVE the cap, the "optimal" card is NOT the BCP (1% after cap) -- it's the WF Active Cash (2%)
3. Only flag grocery spend on other cards as a "leak" if there's room remaining under the BCP cap
4. The `model.py` module already has grocery cap handling (`groceries_cap` field in CardSpec) -- `rewards.py` needs to use the same logic

### Bug 3: High "Other" category resolved but not re-validated

The normalize agent reduced "Other" from 41% to 7.9%, but this was before discovering the parser bugs. After parsers are fixed and more transactions flow through, the "Other" percentage may change. Re-run the normalization coverage check after parser fixes.

### Bug 4: WF Checking parser format mismatch

The agent reported building a "Chase Total Checking" parser, but the statements are Wells Fargo checking (account ending 2961). The parser may have been built against the wrong format assumptions. The checking statements need their own format investigation.

**From the burn-it-all checking agent:** The checking format has transaction types including:
- ACH debits (NEWREZ, KMF, PA TAP 529)
- Debit card purchases
- Check payments (Check #NNN)
- Withdrawals
- Online transfers

The parser should capture debit card purchases and ACH debits to known vendors, but skip internal transfers, CC payments, and deposits.

---

## What Is Verified and Trustworthy

1. **The burn-it-all report** (`reports/005-household-optimization-2026-04-12.md`) -- all spending data was parsed individually by dedicated agents that verified their counts against the raw files. The category breakdowns, merchant lists, trip reconstructions, and subscription audits in that report are accurate.

2. **The config files** -- `profile-chris.yml`, `profile-dana.yml`, `household.yml` contain accurate data populated from the burn-it-all findings.

3. **The market cache** -- `data/market/current-offers.yml` and `rule-updates.yml` contain web-researched card data as of Apr 2026.

4. **The architecture and mode files** -- the design is sound. The modes correctly describe which modules to call and in what order. The modules just need to produce correct output.

5. **The merchant normalization map** -- 300+ patterns covering 92% of known transactions. This is solid and will only need incremental additions.

6. **The household spending summary from the burn-it-all** (verified numbers):
   - Groceries: ~$18,108/yr ($1,509/mo across all cards)
   - Dining + DoorDash: ~$12,804/yr at WA pace ($1,067/mo)
   - Amazon: ~$9,900/yr ($825/mo)
   - Travel: ~$10,066/yr (12 trips reconstructed)
   - Subscriptions: ~$8,868/yr
   - Costco: ~$7,656/yr
   - Total CC: ~$112,320/yr

---

## Recommended Debug Sequence

1. **Fix Amex parser first** -- this is the simplest (Excel, not PDF) and has known good data to compare against. If the Amex parser outputs 520 transactions / $39,375, move on. If not, the column mapping is wrong.

2. **Fix Chase PDF parser** -- compare one Amazon statement's parser output against the burn-it-all agent's transaction count for the same statement. Find the regex gap.

3. **Fix WF PDF parser** -- same approach.

4. **Fix rewards.py grocery cap logic** -- add cap-aware routing. Test against the known BCP grocery spend ($6,470 in 2025, cap hit in August).

5. **Fix WF checking parser** -- verify the format, test against burn-it-all checking agent's findings (559 transactions from 41 statements).

6. **Re-run full pipeline** -- parse all statements, build spending profile, run rewards calculator. Compare every number against the burn-it-all ground truth.

7. **Only after validation passes:** present the household effectiveness report.

---

## Session Context

The user (Chris) is a data analyst at Wizards of the Coast, moved from PA to WA in Jan 2026, married to Dana, has a toddler and a pet with chronic health issues. He explicitly does not want travel points -- cash back only. He has an MTG card selling side business. He is technically sophisticated and will catch bad data immediately. Do not present unvalidated output as findings.
