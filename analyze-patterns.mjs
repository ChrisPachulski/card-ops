#!/usr/bin/env node
/**
 * analyze-patterns.mjs -- Approval pattern analyzer for card-ops
 *
 * Parses cards.md + all linked reports, extracts dimensions
 * (card type, issuer, annual fee, scores), classifies outcomes,
 * and outputs structured JSON with actionable patterns.
 *
 * Run: node analyze-patterns.mjs          (JSON to stdout)
 *      node analyze-patterns.mjs --summary (human-readable table)
 */

import { readFileSync, existsSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const CARD_OPS = dirname(fileURLToPath(import.meta.url));
const CARDS_FILE = join(CARD_OPS, 'data/cards.md');
const REPORTS_DIR = join(CARD_OPS, 'reports');

const args = process.argv.slice(2);
const summaryMode = args.includes('--summary');

const CANONICAL_STATUSES = [
  'evaluated', 'applied', 'approved', 'rejected',
  'pended', 'declined', 'active', 'closed', 'skip',
];

function normalizeStatus(raw) {
  return raw.replace(/\*\*/g, '').trim().toLowerCase();
}

function classifyOutcome(status) {
  const s = normalizeStatus(status);
  if (['approved', 'active'].includes(s)) return 'positive';
  if (['applied', 'pended'].includes(s)) return 'in_progress';
  if (['rejected'].includes(s)) return 'negative';
  if (['skip', 'declined', 'closed'].includes(s)) return 'self_filtered';
  return 'pending'; // evaluated
}

function parseTracker() {
  if (!existsSync(CARDS_FILE)) return [];
  const content = readFileSync(CARDS_FILE, 'utf-8');
  const entries = [];
  for (const line of content.split('\n')) {
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
  return entries;
}

function parseFee(feeStr) {
  const m = feeStr.replace(/[$,]/g, '').match(/(\d+)/);
  return m ? parseInt(m[1]) : 0;
}

function analyze() {
  const entries = parseTracker();

  if (entries.length === 0) {
    return { error: 'No cards found in tracker.' };
  }

  const enriched = entries.map(e => ({
    ...e,
    normalizedStatus: normalizeStatus(e.status),
    outcome: classifyOutcome(e.status),
    score: parseFloat(e.score) || 0,
    fee: parseFee(e.annual_fee),
  }));

  // --- Funnel ---
  const funnel = {};
  for (const e of enriched) {
    const s = e.normalizedStatus;
    funnel[s] = (funnel[s] || 0) + 1;
  }

  // --- Score comparison by outcome ---
  const scoresByOutcome = { positive: [], negative: [], in_progress: [], self_filtered: [], pending: [] };
  for (const e of enriched) {
    if (e.score > 0) scoresByOutcome[e.outcome].push(e.score);
  }

  const scoreStats = (arr) => {
    if (arr.length === 0) return { avg: 0, min: 0, max: 0, count: 0 };
    const avg = arr.reduce((a, b) => a + b, 0) / arr.length;
    return {
      avg: Math.round(avg * 100) / 100,
      min: Math.min(...arr),
      max: Math.max(...arr),
      count: arr.length,
    };
  };

  const scoreComparison = {};
  for (const [group, scores] of Object.entries(scoresByOutcome)) {
    scoreComparison[group] = scoreStats(scores);
  }

  // --- Issuer breakdown ---
  const issuerMap = new Map();
  for (const e of enriched) {
    if (!issuerMap.has(e.issuer)) issuerMap.set(e.issuer, { total: 0, positive: 0, negative: 0, in_progress: 0, self_filtered: 0, pending: 0 });
    const entry = issuerMap.get(e.issuer);
    entry.total++;
    entry[e.outcome]++;
  }
  const issuerBreakdown = [...issuerMap.entries()].map(([issuer, data]) => ({
    issuer,
    ...data,
    approvalRate: data.total > 0 ? Math.round((data.positive / data.total) * 100) : 0,
  })).sort((a, b) => b.total - a.total);

  // --- Fee analysis ---
  const feeGroups = { '$0': [], '$1-$99': [], '$100-$299': [], '$300+': [] };
  for (const e of enriched) {
    if (e.fee === 0) feeGroups['$0'].push(e);
    else if (e.fee < 100) feeGroups['$1-$99'].push(e);
    else if (e.fee < 300) feeGroups['$100-$299'].push(e);
    else feeGroups['$300+'].push(e);
  }
  const feeBreakdown = Object.entries(feeGroups).map(([range, entries]) => ({
    range,
    total: entries.length,
    positive: entries.filter(e => e.outcome === 'positive').length,
    avgScore: entries.length > 0
      ? Math.round(entries.reduce((sum, e) => sum + e.score, 0) / entries.length * 100) / 100
      : 0,
  }));

  // --- Recommendations ---
  const recommendations = [];

  // Best issuer
  const bestIssuer = issuerBreakdown.filter(i => i.total >= 2).sort((a, b) => b.approvalRate - a.approvalRate)[0];
  if (bestIssuer && bestIssuer.approvalRate > 0) {
    recommendations.push({
      action: `Focus on ${bestIssuer.issuer} cards (${bestIssuer.approvalRate}% approval rate across ${bestIssuer.total} applications)`,
      impact: 'medium',
    });
  }

  // Score threshold
  const positiveScores = scoresByOutcome.positive.filter(s => s > 0);
  const minPositiveScore = positiveScores.length > 0 ? Math.min(...positiveScores) : 0;
  if (minPositiveScore > 3.0) {
    recommendations.push({
      action: `Set minimum application threshold at ${Math.floor(minPositiveScore * 10) / 10}/5 -- no approvals below this score`,
      impact: 'high',
    });
  }

  const dates = enriched.map(e => e.date).filter(Boolean).sort();

  return {
    metadata: {
      total: enriched.length,
      dateRange: { from: dates[0], to: dates[dates.length - 1] },
      analysisDate: new Date().toISOString().split('T')[0],
      byOutcome: {
        positive: enriched.filter(e => e.outcome === 'positive').length,
        negative: enriched.filter(e => e.outcome === 'negative').length,
        in_progress: enriched.filter(e => e.outcome === 'in_progress').length,
        self_filtered: enriched.filter(e => e.outcome === 'self_filtered').length,
        pending: enriched.filter(e => e.outcome === 'pending').length,
      },
    },
    funnel,
    scoreComparison,
    issuerBreakdown,
    feeBreakdown,
    recommendations,
  };
}

function printSummary(result) {
  if (result.error) {
    console.log(`\n${result.error}\n`);
    return;
  }

  const { metadata, funnel, scoreComparison, issuerBreakdown, feeBreakdown, recommendations } = result;

  console.log(`\n${'='.repeat(60)}`);
  console.log(`  Card-Ops Pattern Analysis -- ${metadata.analysisDate}`);
  console.log(`  ${metadata.total} cards tracked (${metadata.dateRange.from} to ${metadata.dateRange.to})`);
  console.log(`${'='.repeat(60)}\n`);

  console.log('PIPELINE FUNNEL');
  console.log('-'.repeat(40));
  const funnelOrder = ['evaluated', 'applied', 'pended', 'approved', 'rejected', 'active', 'closed', 'declined', 'skip'];
  for (const status of funnelOrder) {
    if (funnel[status]) {
      const pct = Math.round((funnel[status] / metadata.total) * 100);
      console.log(`  ${status.padEnd(15)} ${String(funnel[status]).padStart(3)} (${pct}%)`);
    }
  }

  console.log('\nSCORE BY OUTCOME');
  console.log('-'.repeat(40));
  for (const [group, stats] of Object.entries(scoreComparison)) {
    if (stats.count > 0) {
      console.log(`  ${group.padEnd(15)} avg ${stats.avg}/5  (${stats.count} entries, range ${stats.min}-${stats.max})`);
    }
  }

  console.log('\nISSUER BREAKDOWN');
  console.log('-'.repeat(40));
  for (const i of issuerBreakdown) {
    console.log(`  ${i.issuer.padEnd(20)} ${String(i.total).padStart(2)} total, ${i.positive} approved (${i.approvalRate}%)`);
  }

  console.log('\nFEE BREAKDOWN');
  console.log('-'.repeat(40));
  for (const f of feeBreakdown) {
    console.log(`  ${f.range.padEnd(15)} ${String(f.total).padStart(2)} cards, avg score ${f.avgScore}/5`);
  }

  if (recommendations.length > 0) {
    console.log(`\nRECOMMENDATIONS`);
    console.log('='.repeat(60));
    for (let i = 0; i < recommendations.length; i++) {
      console.log(`  ${i + 1}. [${recommendations[i].impact.toUpperCase()}] ${recommendations[i].action}`);
    }
  }

  console.log('');
}

const result = analyze();

if (summaryMode) {
  printSummary(result);
} else {
  console.log(JSON.stringify(result, null, 2));
}

if (result.error) process.exit(1);
