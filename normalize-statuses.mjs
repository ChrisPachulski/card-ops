#!/usr/bin/env node
/**
 * normalize-statuses.mjs -- Clean non-canonical states in cards.md
 *
 * Maps all non-canonical statuses to canonical ones per states.yml.
 * Strips markdown bold from status and score fields.
 *
 * Run: node card-ops/normalize-statuses.mjs [--dry-run]
 */

import { readFileSync, writeFileSync, copyFileSync, existsSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const CARD_OPS = dirname(fileURLToPath(import.meta.url));
const CARDS_FILE = join(CARD_OPS, 'data/cards.md');
const DRY_RUN = process.argv.includes('--dry-run');

function normalizeStatus(raw) {
  let s = raw.replace(/\*\*/g, '').trim();
  const lower = s.toLowerCase();

  const canonical = [
    'Evaluated', 'Applied', 'Approved', 'Rejected',
    'Pended', 'Declined', 'Active', 'Closed', 'SKIP',
  ];
  for (const c of canonical) {
    if (lower === c.toLowerCase()) return { status: c };
  }

  // Common aliases
  const aliases = {
    'pending': 'Pended',
    'under review': 'Pended',
    'manual review': 'Pended',
    'denied': 'Rejected',
    'open': 'Active',
    'in wallet': 'Active',
    'cancelled': 'Closed',
    'canceled': 'Closed',
    'product changed': 'Closed',
    'downgraded': 'Closed',
    'upgraded': 'Active',
    'pass': 'SKIP',
    'no': 'SKIP',
    'not interested': 'SKIP',
  };

  if (aliases[lower]) return { status: aliases[lower] };

  if (s === '' || s === '-') return { status: 'SKIP' };

  return { status: null, unknown: true };
}

if (!existsSync(CARDS_FILE)) {
  console.log('No cards.md found. Nothing to normalize.');
  process.exit(0);
}
const content = readFileSync(CARDS_FILE, 'utf-8');
const lines = content.split('\n');

let changes = 0;
let unknowns = [];

for (let i = 0; i < lines.length; i++) {
  const line = lines[i];
  if (!line.startsWith('|')) continue;

  const parts = line.split('|').map(s => s.trim());
  if (parts.length < 10) continue;
  if (parts[1] === '#' || parts[1] === '---' || parts[1] === '') continue;

  const num = parseInt(parts[1]);
  if (isNaN(num)) continue;

  const rawStatus = parts[6];
  const result = normalizeStatus(rawStatus);

  if (result.unknown) {
    unknowns.push({ num, rawStatus, line: i + 1 });
    continue;
  }

  if (result.status === rawStatus) continue;

  parts[6] = result.status;

  // Strip bold from score field
  if (parts[5]) {
    parts[5] = parts[5].replace(/\*\*/g, '');
  }

  const newLine = '| ' + parts.slice(1, -1).join(' | ') + ' |';
  lines[i] = newLine;
  changes++;

  console.log(`#${num}: "${rawStatus}" -> "${result.status}"`);
}

if (unknowns.length > 0) {
  console.log(`\n${unknowns.length} unknown statuses:`);
  for (const u of unknowns) {
    console.log(`  #${u.num} (line ${u.line}): "${u.rawStatus}"`);
  }
}

console.log(`\n${changes} statuses normalized`);

if (!DRY_RUN && changes > 0) {
  copyFileSync(CARDS_FILE, CARDS_FILE + '.bak');
  writeFileSync(CARDS_FILE, lines.join('\n'));
  console.log('Written to cards.md (backup: cards.md.bak)');
} else if (DRY_RUN) {
  console.log('(dry-run -- no changes written)');
} else {
  console.log('No changes needed');
}
