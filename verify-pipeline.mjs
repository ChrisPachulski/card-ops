#!/usr/bin/env node
/**
 * verify-pipeline.mjs -- Health check for card-ops pipeline integrity
 *
 * Checks:
 * 1. All statuses are canonical (per states.yml)
 * 2. No duplicate issuer+card entries
 * 3. All report links point to existing files
 * 4. Scores match format X.X/5 or N/A
 * 5. All rows have proper pipe-delimited format
 * 6. No pending TSVs in tracker-additions/
 *
 * Run: node card-ops/verify-pipeline.mjs
 */

import { readFileSync, readdirSync, existsSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const CARD_OPS = dirname(fileURLToPath(import.meta.url));
const CARDS_FILE = join(CARD_OPS, 'data/cards.md');
const ADDITIONS_DIR = join(CARD_OPS, 'batch/tracker-additions');
const REPORTS_DIR = join(CARD_OPS, 'reports');

const CANONICAL_STATUSES = [
  'evaluated', 'applied', 'approved', 'rejected',
  'pended', 'declined', 'active', 'closed', 'skip',
];

let errors = 0;
let warnings = 0;

function error(msg) { console.log(`ERROR: ${msg}`); errors++; }
function warn(msg) { console.log(`WARN:  ${msg}`); warnings++; }
function ok(msg) { console.log(`OK:    ${msg}`); }

// --- Read cards.md ---
if (!existsSync(CARDS_FILE)) {
  console.log('\nNo cards.md found. This is normal for a fresh setup.');
  console.log('The file will be created when you evaluate your first offer.\n');
  process.exit(0);
}
const content = readFileSync(CARDS_FILE, 'utf-8');
const lines = content.split('\n');

const entries = [];
for (const line of lines) {
  if (!line.startsWith('|')) continue;
  const parts = line.split('|').map(s => s.trim());
  if (parts.length < 10) continue;
  const num = parseInt(parts[1]);
  if (isNaN(num)) continue;
  entries.push({
    num, date: parts[2], issuer: parts[3], card: parts[4],
    score: parts[5], status: parts[6], annual_fee: parts[7],
    report: parts[8], notes: parts[9] || '',
  });
}

console.log(`\nChecking ${entries.length} entries in cards.md\n`);

// --- Check 1: Canonical statuses ---
let badStatuses = 0;
for (const e of entries) {
  const clean = e.status.replace(/\*\*/g, '').trim().toLowerCase();
  if (!CANONICAL_STATUSES.includes(clean)) {
    error(`#${e.num}: Non-canonical status "${e.status}"`);
    badStatuses++;
  }
  if (e.status.includes('**')) {
    error(`#${e.num}: Status contains markdown bold: "${e.status}"`);
    badStatuses++;
  }
}
if (badStatuses === 0) ok('All statuses are canonical');

// --- Check 2: Duplicates ---
const issuerCardMap = new Map();
let dupes = 0;
for (const e of entries) {
  const key = e.issuer.toLowerCase().replace(/[^a-z0-9]/g, '') + '::' +
    e.card.toLowerCase().replace(/[^a-z0-9 ]/g, '');
  if (!issuerCardMap.has(key)) issuerCardMap.set(key, []);
  issuerCardMap.get(key).push(e);
}
for (const [key, group] of issuerCardMap) {
  if (group.length > 1) {
    warn(`Possible duplicates: ${group.map(e => `#${e.num}`).join(', ')} (${group[0].issuer} ${group[0].card})`);
    dupes++;
  }
}
if (dupes === 0) ok('No exact duplicates found');

// --- Check 3: Report links ---
let brokenReports = 0;
for (const e of entries) {
  const match = e.report.match(/\]\(([^)]+)\)/);
  if (!match) continue;
  const reportPath = join(CARD_OPS, match[1]);
  if (!existsSync(reportPath)) {
    error(`#${e.num}: Report not found: ${match[1]}`);
    brokenReports++;
  }
}
if (brokenReports === 0) ok('All report links valid');

// --- Check 4: Score format ---
let badScores = 0;
for (const e of entries) {
  const s = e.score.replace(/\*\*/g, '').trim();
  if (!/^\d+\.?\d*\/5$/.test(s) && s !== 'N/A') {
    error(`#${e.num}: Invalid score format: "${e.score}"`);
    badScores++;
  }
}
if (badScores === 0) ok('All scores valid');

// --- Check 5: Row format ---
let badRows = 0;
for (const line of lines) {
  if (!line.startsWith('|')) continue;
  if (line.includes('---') || line.includes('Issuer')) continue;
  const parts = line.split('|');
  if (parts.length < 10) {
    error(`Row with <10 columns: ${line.substring(0, 80)}...`);
    badRows++;
  }
}
if (badRows === 0) ok('All rows properly formatted');

// --- Check 6: Pending TSVs ---
let pendingTsvs = 0;
if (existsSync(ADDITIONS_DIR)) {
  const files = readdirSync(ADDITIONS_DIR).filter(f => f.endsWith('.tsv'));
  pendingTsvs = files.length;
  if (pendingTsvs > 0) {
    warn(`${pendingTsvs} pending TSVs in tracker-additions/ (not merged)`);
  }
}
if (pendingTsvs === 0) ok('No pending TSVs');

// --- Summary ---
console.log('\n' + '='.repeat(50));
console.log(`Pipeline Health: ${errors} errors, ${warnings} warnings`);
if (errors === 0 && warnings === 0) {
  console.log('Pipeline is clean.');
} else if (errors === 0) {
  console.log('Pipeline OK with warnings.');
} else {
  console.log('Pipeline has errors -- fix before proceeding.');
}

process.exit(errors > 0 ? 1 : 0);
