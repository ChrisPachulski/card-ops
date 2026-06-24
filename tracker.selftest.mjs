/** Self-check for tracker.mjs shared helpers. Run: node tracker.selftest.mjs */
import assert from 'assert';
import {
  parseScore, parseCardLine, serializeRow, cardMatch,
  normalizeIssuer, CANONICAL_STATES,
} from './tracker.mjs';

// parseScore strips bold and extracts the number
assert.strictEqual(parseScore('**4.2**/5'), 4.2);
assert.strictEqual(parseScore('N/A'), 0);

// parseCardLine maps the 10 columns; header/separator rows -> null
const row = '| 7 | 2026-06-24 | Chase | Freedom Unlimited | 4.0/5 | Evaluated | $0 | [7](reports/7.md) | note |';
const e = parseCardLine(row);
assert.strictEqual(e.num, 7);
assert.strictEqual(e.issuer, 'Chase');
assert.strictEqual(e.card, 'Freedom Unlimited');
assert.strictEqual(e.status, 'Evaluated');
assert.strictEqual(parseCardLine('| # | Date | Issuer |'), null);
assert.strictEqual(parseCardLine('|---|---|---|'), null);

// serializeRow round-trips a parsed row's columns
const parts = row.split('|').map((s) => s.trim());
parts[6] = 'Approved';
assert.ok(serializeRow(parts).startsWith('| 7 | 2026-06-24 | Chase |'));
assert.ok(serializeRow(parts).includes('| Approved |'));

// cardMatch: fuzzy on words >3 chars
assert.ok(cardMatch('Freedom Unlimited', 'Chase Freedom Unlimited'));
assert.ok(!cardMatch('Active Cash', 'Sapphire Reserve'));

// normalizeIssuer strips punctuation/case
assert.strictEqual(normalizeIssuer('American Express'), 'americanexpress');
assert.strictEqual(CANONICAL_STATES.length, 9);

console.log('tracker.selftest: all assertions passed');
