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
import { join } from 'path';
import { execFileSync } from 'child_process';
import {
  readCards, parseScore, normalizeIssuer, cardMatch, CANONICAL_STATES,
  CARD_OPS, CARDS_FILE, ADDITIONS_DIR,
} from './tracker.mjs';

const MERGED_DIR = join(ADDITIONS_DIR, 'merged');
const DRY_RUN = process.argv.includes('--dry-run');
const VERIFY = process.argv.includes('--verify');

function validateStatus(status) {
  const lower = status.replace(/\*\*/g, '').trim().toLowerCase();
  for (const valid of CANONICAL_STATES) {
    if (valid.toLowerCase() === lower) return valid;
  }
  console.warn(`  Non-canonical status "${status}" -> defaulting to "Evaluated"`);
  return 'Evaluated';
}

function extractReportNum(reportStr) {
  const m = reportStr.match(/\[(\d+)\]/);
  return m ? parseInt(m[1]) : null;
}

function parseTsvContent(content, filename) {
  content = content.trim();
  if (!content) return null;

  let parts;

  if (content.startsWith('|')) {
    parts = content.split('|').map((s) => s.trim()).filter(Boolean);
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

const data = readCards();
if (!data) {
  console.log('No cards.md found. Nothing to merge into.');
  process.exit(0);
}
const { lines: cardLines, entries: existingCards } = data;
let maxNum = existingCards.reduce((m, c) => Math.max(m, c.num), 0);

console.log(`Existing: ${existingCards.length} entries, max #${maxNum}`);

if (!existsSync(ADDITIONS_DIR)) {
  console.log('No tracker-additions directory found.');
  process.exit(0);
}

const tsvFiles = readdirSync(ADDITIONS_DIR).filter((f) => f.endsWith('.tsv'));
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
    duplicate = existingCards.find((c) => extractReportNum(c.report) === reportNum);
  }

  if (!duplicate) {
    duplicate = existingCards.find((c) => c.num === addition.num);
  }

  if (!duplicate) {
    const normIssuer = normalizeIssuer(addition.issuer);
    duplicate = existingCards.find((c) =>
      normalizeIssuer(c.issuer) === normIssuer && cardMatch(addition.card, c.card));
  }

  if (duplicate) {
    const newScore = parseScore(addition.score);
    const oldScore = parseScore(duplicate.score);

    if (newScore > oldScore) {
      console.log(`Update: #${duplicate.num} ${addition.issuer} ${addition.card} (${oldScore}->${newScore})`);
      if (duplicate.lineIdx >= 0) {
        cardLines[duplicate.lineIdx] = `| ${duplicate.num} | ${addition.date} | ${addition.issuer} | ${addition.card} | ${addition.score} | ${duplicate.status} | ${addition.annual_fee} | ${addition.report} | Re-eval ${addition.date} (${oldScore}->${newScore}). ${addition.notes} |`;
        updated++;
      }
    } else {
      console.log(`Skip: ${addition.issuer} ${addition.card} (existing #${duplicate.num} ${oldScore} >= new ${newScore})`);
      skipped++;
    }
  } else {
    const entryNum = addition.num > maxNum ? addition.num : ++maxNum;
    if (addition.num > maxNum) maxNum = addition.num;

    newLines.push(`| ${entryNum} | ${addition.date} | ${addition.issuer} | ${addition.card} | ${addition.score} | ${addition.status} | ${addition.annual_fee} | ${addition.report} | ${addition.notes} |`);
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
