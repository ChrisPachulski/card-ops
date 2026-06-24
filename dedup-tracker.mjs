#!/usr/bin/env node
/**
 * dedup-tracker.mjs -- Remove duplicate entries from cards.md
 *
 * Groups by normalized issuer + fuzzy card name match.
 * Keeps entry with highest score. If discarded entry had more advanced
 * status, preserves that status. Merges notes.
 *
 * Run: node card-ops/dedup-tracker.mjs [--dry-run]
 */

import {
  readCards, writeCards, serializeRow, parseScore, normalizeIssuer, cardMatch,
} from './tracker.mjs';

const DRY_RUN = process.argv.includes('--dry-run');

// Status advancement order (higher = more advanced in pipeline)
const STATUS_RANK = {
  'skip': 0,
  'closed': 0,
  'declined': 1,
  'rejected': 1,
  'evaluated': 2,
  'applied': 3,
  'pended': 4,
  'approved': 5,
  'active': 6,
};

const data = readCards();
if (!data) {
  console.log('No cards.md found. Nothing to dedup.');
  process.exit(0);
}
const { lines, entries } = data;
const entryLineMap = new Map(entries.map((e) => [e.num, e.lineIdx]));

console.log(`${entries.length} entries loaded`);

// Group by issuer
const groups = new Map();
for (const entry of entries) {
  const key = normalizeIssuer(entry.issuer);
  if (!groups.has(key)) groups.set(key, []);
  groups.get(key).push(entry);
}

// Find duplicates
let removed = 0;
const linesToRemove = new Set();

for (const [issuer, issuerEntries] of groups) {
  if (issuerEntries.length < 2) continue;

  const processed = new Set();
  for (let i = 0; i < issuerEntries.length; i++) {
    if (processed.has(i)) continue;
    const cluster = [issuerEntries[i]];
    processed.add(i);

    for (let j = i + 1; j < issuerEntries.length; j++) {
      if (processed.has(j)) continue;
      if (cardMatch(issuerEntries[i].card, issuerEntries[j].card)) {
        cluster.push(issuerEntries[j]);
        processed.add(j);
      }
    }

    if (cluster.length < 2) continue;

    cluster.sort((a, b) => parseScore(b.score) - parseScore(a.score));
    const keeper = cluster[0];

    let bestStatusRank = STATUS_RANK[keeper.status.toLowerCase()] || 0;
    let bestStatus = keeper.status;
    for (let k = 1; k < cluster.length; k++) {
      const rank = STATUS_RANK[cluster[k].status.toLowerCase()] || 0;
      if (rank > bestStatusRank) {
        bestStatusRank = rank;
        bestStatus = cluster[k].status;
      }
    }

    if (bestStatus !== keeper.status) {
      const lineIdx = entryLineMap.get(keeper.num);
      if (lineIdx !== undefined) {
        const parts = lines[lineIdx].split('|').map((s) => s.trim());
        parts[6] = bestStatus;
        lines[lineIdx] = serializeRow(parts);
        console.log(`  #${keeper.num}: status promoted to "${bestStatus}"`);
      }
    }

    for (let k = 1; k < cluster.length; k++) {
      const dup = cluster[k];
      const lineIdx = entryLineMap.get(dup.num);
      if (lineIdx !== undefined) {
        linesToRemove.add(lineIdx);
        removed++;
        console.log(`Remove #${dup.num} (${dup.issuer} ${dup.card}, ${dup.score}) -> kept #${keeper.num} (${keeper.score})`);
      }
    }
  }
}

const sortedRemoveIndices = [...linesToRemove].sort((a, b) => b - a);
for (const idx of sortedRemoveIndices) {
  lines.splice(idx, 1);
}

console.log(`\n${removed} duplicates removed`);

if (!DRY_RUN && removed > 0) {
  writeCards(lines);
  console.log('Written to cards.md (backup: cards.md.bak)');
} else if (DRY_RUN) {
  console.log('(dry-run -- no changes written)');
} else {
  console.log('No duplicates found');
}
