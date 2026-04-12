#!/usr/bin/env node
/**
 * merge-tracker.mjs -- Merge batch tracker additions into cards.md
 *
 * Handles TSV format:
 * 9-col: num\tdate\tissuer\tcard\tstatus\tscore\tannual_fee\treport\tnotes
 *
 * Dedup: issuer normalized + card fuzzy match + report number match
 * If duplicate with higher score -> update in-place, update report link
 * Validates status against states.yml (rejects non-canonical, logs warning)
 *
 * Run: node card-ops/merge-tracker.mjs [--dry-run] [--verify]
 */

import { readFileSync, writeFileSync, readdirSync, mkdirSync, renameSync, existsSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';
import { execFileSync } from 'child_process';

const CARD_OPS = dirname(fileURLToPath(import.meta.url));
const CARDS_FILE = join(CARD_OPS, 'data/cards.md');
const ADDITIONS_DIR = join(CARD_OPS, 'batch/tracker-additions');
const MERGED_DIR = join(ADDITIONS_DIR, 'merged');
const DRY_RUN = process.argv.includes('--dry-run');
const VERIFY = process.argv.includes('--verify');

const CANONICAL_STATES = [
  'Evaluated', 'Applied', 'Approved', 'Rejected',
  'Pended', 'Declined', 'Active', 'Closed', 'SKIP',
];

function validateStatus(status) {
  const clean = status.replace(/\*\*/g, '').trim();
  const lower = clean.toLowerCase();

  for (const valid of CANONICAL_STATES) {
    if (valid.toLowerCase() === lower) return valid;
  }

  console.warn(`  Non-canonical status "${status}" -> defaulting to "Evaluated"`);
  return 'Evaluated';
}

function normalizeIssuer(name) {
  return name.toLowerCase().replace(/[^a-z0-9]/g, '');
}

function cardFuzzyMatch(a, b) {
  const wordsA = a.toLowerCase().split(/\s+/).filter(w => w.length > 3);
  const wordsB = b.toLowerCase().split(/\s+/).filter(w => w.length > 3);
  const overlap = wordsA.filter(w => wordsB.some(wb => wb.includes(w) || w.includes(wb)));
  return overlap.length >= 1;
}

function extractReportNum(reportStr) {
  const m = reportStr.match(/\[(\d+)\]/);
  return m ? parseInt(m[1]) : null;
}

function parseScore(s) {
  const m = s.replace(/\*\*/g, '').match(/([\d.]+)/);
  return m ? parseFloat(m[1]) : 0;
}

function parseCardLine(line) {
  const parts = line.split('|').map(s => s.trim());
  if (parts.length < 10) return null;
  const num = parseInt(parts[1]);
  if (isNaN(num) || num === 0) return null;
  return {
    num, date: parts[2], issuer: parts[3], card: parts[4],
    score: parts[5], status: parts[6], annual_fee: parts[7],
    report: parts[8], notes: parts[9] || '', raw: line,
  };
}

function parseTsvContent(content, filename) {
  content = content.trim();
  if (!content) return null;

  let parts;

  if (content.startsWith('|')) {
    parts = content.split('|').map(s => s.trim()).filter(Boolean);
    if (parts.length < 8) {
      console.warn(`  Skipping malformed pipe-delimited ${filename}: ${parts.length} fields`);
      return null;
    }
    return {
      num: parseInt(parts[0]), date: parts[1], issuer: parts[2],
      card: parts[3], score: parts[4], status: validateStatus(parts[5]),
      annual_fee: parts[6], report: parts[7], notes: parts[8] || '',
    };
  }

  parts = content.split('\t');
  if (parts.length < 8) {
    console.warn(`  Skipping malformed TSV ${filename}: ${parts.length} fields`);
    return null;
  }

  const addition = {
    num: parseInt(parts[0]), date: parts[1], issuer: parts[2],
    card: parts[3], status: validateStatus(parts[4]),
    score: parts[5], annual_fee: parts[6],
    report: parts[7], notes: parts[8] || '',
  };

  if (isNaN(addition.num) || addition.num === 0) {
    console.warn(`  Skipping ${filename}: invalid entry number`);
    return null;
  }

  return addition;
}

// ---- Main ----

if (!existsSync(CARDS_FILE)) {
  console.log('No cards.md found. Nothing to merge into.');
  process.exit(0);
}
const cardContent = readFileSync(CARDS_FILE, 'utf-8');
const cardLines = cardContent.split('\n');
const existingCards = [];
let maxNum = 0;

for (const line of cardLines) {
  if (line.startsWith('|') && !line.includes('---') && !line.includes('Issuer')) {
    const card = parseCardLine(line);
    if (card) {
      existingCards.push(card);
      if (card.num > maxNum) maxNum = card.num;
    }
  }
}

console.log(`Existing: ${existingCards.length} entries, max #${maxNum}`);

if (!existsSync(ADDITIONS_DIR)) {
  console.log('No tracker-additions directory found.');
  process.exit(0);
}

const tsvFiles = readdirSync(ADDITIONS_DIR).filter(f => f.endsWith('.tsv'));
if (tsvFiles.length === 0) {
  console.log('No pending additions to merge.');
  process.exit(0);
}

tsvFiles.sort((a, b) => {
  const numA = parseInt(a.replace(/\D/g, '')) || 0;
  const numB = parseInt(b.replace(/\D/g, '')) || 0;
  return numA - numB;
});

console.log(`Found ${tsvFiles.length} pending additions`);

let added = 0;
let updated = 0;
let skipped = 0;
const newLines = [];

for (const file of tsvFiles) {
  const content = readFileSync(join(ADDITIONS_DIR, file), 'utf-8').trim();
  const addition = parseTsvContent(content, file);
  if (!addition) { skipped++; continue; }

  const reportNum = extractReportNum(addition.report);
  let duplicate = null;

  if (reportNum) {
    duplicate = existingCards.find(c => {
      const existingReportNum = extractReportNum(c.report);
      return existingReportNum === reportNum;
    });
  }

  if (!duplicate) {
    duplicate = existingCards.find(c => c.num === addition.num);
  }

  if (!duplicate) {
    const normIssuer = normalizeIssuer(addition.issuer);
    duplicate = existingCards.find(c => {
      if (normalizeIssuer(c.issuer) !== normIssuer) return false;
      return cardFuzzyMatch(addition.card, c.card);
    });
  }

  if (duplicate) {
    const newScore = parseScore(addition.score);
    const oldScore = parseScore(duplicate.score);

    if (newScore > oldScore) {
      console.log(`Update: #${duplicate.num} ${addition.issuer} ${addition.card} (${oldScore}->${newScore})`);
      const lineIdx = cardLines.indexOf(duplicate.raw);
      if (lineIdx >= 0) {
        const updatedLine = `| ${duplicate.num} | ${addition.date} | ${addition.issuer} | ${addition.card} | ${addition.score} | ${duplicate.status} | ${addition.annual_fee} | ${addition.report} | Re-eval ${addition.date} (${oldScore}->${newScore}). ${addition.notes} |`;
        cardLines[lineIdx] = updatedLine;
        updated++;
      }
    } else {
      console.log(`Skip: ${addition.issuer} ${addition.card} (existing #${duplicate.num} ${oldScore} >= new ${newScore})`);
      skipped++;
    }
  } else {
    const entryNum = addition.num > maxNum ? addition.num : ++maxNum;
    if (addition.num > maxNum) maxNum = addition.num;

    const newLine = `| ${entryNum} | ${addition.date} | ${addition.issuer} | ${addition.card} | ${addition.score} | ${addition.status} | ${addition.annual_fee} | ${addition.report} | ${addition.notes} |`;
    newLines.push(newLine);
    added++;
    console.log(`Add #${entryNum}: ${addition.issuer} ${addition.card} (${addition.score})`);
  }
}

if (newLines.length > 0) {
  let insertIdx = -1;
  for (let i = 0; i < cardLines.length; i++) {
    if (cardLines[i].includes('---') && cardLines[i].startsWith('|')) {
      insertIdx = i + 1;
      break;
    }
  }
  if (insertIdx >= 0) {
    cardLines.splice(insertIdx, 0, ...newLines);
  }
}

if (!DRY_RUN) {
  writeFileSync(CARDS_FILE, cardLines.join('\n'));

  if (!existsSync(MERGED_DIR)) mkdirSync(MERGED_DIR, { recursive: true });
  for (const file of tsvFiles) {
    renameSync(join(ADDITIONS_DIR, file), join(MERGED_DIR, file));
  }
  console.log(`\nMoved ${tsvFiles.length} TSVs to merged/`);
}

console.log(`\nSummary: +${added} added, ${updated} updated, ${skipped} skipped`);
if (DRY_RUN) console.log('(dry-run -- no changes written)');

if (VERIFY && !DRY_RUN) {
  console.log('\n--- Running verification ---');
  try {
    execFileSync('node', [join(CARD_OPS, 'verify-pipeline.mjs')], { stdio: 'inherit' });
  } catch (e) {
    process.exit(1);
  }
}
