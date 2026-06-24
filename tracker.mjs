/**
 * tracker.mjs -- shared helpers for the cards.md tracker scripts
 * (merge / dedup / normalize-statuses / verify-pipeline / analyze-patterns).
 *
 * cards.md is a pipe-delimited table; one data row is:
 *   | num | date | issuer | card | score | status | annual_fee | report | notes |
 *
 * Self-check: node tracker.selftest.mjs
 */

import { readFileSync, writeFileSync, copyFileSync, existsSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

export const CARD_OPS = dirname(fileURLToPath(import.meta.url));
export const CARDS_FILE = join(CARD_OPS, 'data/cards.md');
export const ADDITIONS_DIR = join(CARD_OPS, 'batch/tracker-additions');
export const REPORTS_DIR = join(CARD_OPS, 'reports');

export const CANONICAL_STATES = [
  'Evaluated', 'Applied', 'Approved', 'Rejected',
  'Pended', 'Declined', 'Active', 'Closed', 'SKIP',
];
export const CANONICAL_LOWER = CANONICAL_STATES.map((s) => s.toLowerCase());

export const stripBold = (s) => s.replace(/\*\*/g, '');

export function parseScore(s) {
  const m = stripBold(s).match(/([\d.]+)/);
  return m ? parseFloat(m[1]) : 0;
}

export const normalizeIssuer = (name) =>
  name.toLowerCase().replace(/[^a-z0-9]/g, '').trim();

export const normalizeCard = (card) =>
  card.toLowerCase().replace(/[^a-z0-9 ]/g, '').trim();

/** Fuzzy card-name match: any shared word longer than 3 chars (substring either way). */
export function cardMatch(a, b) {
  const words = (s) => normalizeCard(s).split(/\s+/).filter((w) => w.length > 3);
  const wa = words(a);
  const wb = words(b);
  return wa.some((w) => wb.some((x) => x.includes(w) || w.includes(x)));
}

/** Parse one pipe-delimited cards.md row -> entry object, or null if not a data row. */
export function parseCardLine(line) {
  const parts = line.split('|').map((s) => s.trim());
  if (parts.length < 10) return null;
  const num = parseInt(parts[1]);
  if (isNaN(num)) return null;
  return {
    num, date: parts[2], issuer: parts[3], card: parts[4],
    score: parts[5], status: parts[6], annual_fee: parts[7],
    report: parts[8], notes: parts[9] || '', raw: line,
  };
}

/** Read cards.md -> { lines, entries: [...with lineIdx] }; null if the file is missing. */
export function readCards() {
  if (!existsSync(CARDS_FILE)) return null;
  const lines = readFileSync(CARDS_FILE, 'utf-8').split('\n');
  const entries = [];
  for (let i = 0; i < lines.length; i++) {
    const entry = parseCardLine(lines[i]);
    if (entry && entry.num > 0) entries.push({ ...entry, lineIdx: i });
  }
  return { lines, entries };
}

/** Re-serialize a split('|') parts array back into a table row. */
export const serializeRow = (parts) => '| ' + parts.slice(1, -1).join(' | ') + ' |';

/** Write cards.md, backing up to cards.md.bak first unless backup:false. */
export function writeCards(lines, { backup = true } = {}) {
  if (backup) copyFileSync(CARDS_FILE, CARDS_FILE + '.bak');
  writeFileSync(CARDS_FILE, lines.join('\n'));
}
