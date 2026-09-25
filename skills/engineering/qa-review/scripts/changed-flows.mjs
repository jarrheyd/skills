#!/usr/bin/env node
// changed-flows.mjs — map a git diff to the Maestro flows it touches, for the
// Functional (change-scoped) mode. Reads the testIDs and salient copy each changed
// screen emits, then finds the flows that drive those ids/text. Zero-dep.
//
// Usage: node changed-flows.mjs --repo <path> [--base <commit|tag>] [--out <file>]
// Base resolution: --base, else ~/.qa-review/<project>/.last-proof.json commit,
// else the last git tag, else HEAD~1. Emits changed.json: { base, changedFiles,
// affected:[flows], skipped:[flows], testIds:[...] }.

import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import { execFileSync } from 'node:child_process';

const args = Object.fromEntries(process.argv.slice(2).reduce((a, v, i, arr) => (v.startsWith('--') ? [...a, [v.slice(2), arr[i + 1]]] : a), []));
const REPO = path.resolve(args.repo || '.');
const git = (a) => { try { return execFileSync('git', ['-C', REPO, ...a], { encoding: 'utf8' }).trim(); } catch { return ''; } };

// --- project + baseline -----------------------------------------------------
let project = args.project;
try { const c = JSON.parse(fs.readFileSync(path.join(REPO, '.maestro', 'qa-review.config.json'), 'utf8')); project = project || c.project; } catch {}
const home = project ? path.join(os.homedir(), '.qa-review', project) : null;

function resolveBase() {
  if (args.base) return args.base;
  try { const lp = JSON.parse(fs.readFileSync(path.join(home, '.last-proof.json'), 'utf8')); if (lp.commit) return lp.commit; } catch {}
  const tag = git(['describe', '--tags', '--abbrev=0']); if (tag) return tag;
  return 'HEAD~1';
}
const base = resolveBase();

// --- changed source files ---------------------------------------------------
const diff = git(['diff', '--name-only', `${base}...HEAD`]) || git(['diff', '--name-only', base]);
const changedFiles = diff.split('\n').filter(Boolean);
const srcChanged = changedFiles.filter((f) => /\.(tsx?|jsx?)$/.test(f) && !/\.(test|spec)\./.test(f) && /(src|app|screens|components)\//.test(f));

// --- testIDs emitted by the changed files (testIDs are the reliable anchor) --
const testIds = new Set();
for (const rel of srcChanged) {
  let s = '';
  try { s = fs.readFileSync(path.join(REPO, rel), 'utf8'); } catch { continue; }
  for (const m of s.matchAll(/(?:testID|data-testid)\s*=\s*[{"']\s*[`"']?([\w:-]+)/g)) testIds.add(m[1]);
  for (const m of s.matchAll(/(?:testID|data-testid)\s*[:=]\s*[`"']([\w:-]+)/g)) testIds.add(m[1]);
}

// --- flows, indexed by which changed testIDs they reference ------------------
const flowsDir = path.join(REPO, '.maestro', 'flows');
let flowFiles = [];
try { flowFiles = fs.readdirSync(flowsDir).filter((f) => f.endsWith('.yaml') && !f.startsWith('_')); } catch {}
const idRe = (id) => new RegExp(`(^|[^\\w])${id.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}([^\\w]|$)`);
const flowSrc = {};
for (const f of flowFiles) { try { flowSrc[f] = fs.readFileSync(path.join(flowsDir, f), 'utf8'); } catch { flowSrc[f] = ''; } }
// How many flows reference each changed testID: a low count means the id is
// distinctive to a feature; a high count means a shared component id (weak signal).
const idFlowCount = {};
for (const id of testIds) idFlowCount[id] = flowFiles.filter((f) => idRe(id).test(flowSrc[f])).length;
const DISTINCT_MAX = 12; // an id in <= this many flows is a real feature signal
// A flow is affected if it uses a distinctive changed id, or two-plus changed ids.
const affected = [];
for (const f of flowFiles) {
  const hits = [...testIds].filter((id) => idRe(id).test(flowSrc[f]));
  const distinctive = hits.some((id) => idFlowCount[id] <= DISTINCT_MAX);
  if (distinctive || hits.length >= 2) affected.push(f.replace(/\.yaml$/, ''));
}
const skipped = flowFiles.map((f) => f.replace(/\.yaml$/, '')).filter((n) => !affected.includes(n));
// A change that fans out to most flows is not really change-scoped; say so.
const broad = flowFiles.length > 0 && affected.length / flowFiles.length > 0.55;

const out = { base, changedFiles, srcChanged, testIds: [...testIds], affected, skipped, broad, at: new Date().toISOString() };
if (broad) console.error(`changed-flows: WARNING this change touches ${affected.length}/${flowFiles.length} flows (a shared/central file). Run regression, not functional.`);
const outPath = args.out || (home ? path.join(home, 'changed.json') : path.join(REPO, 'changed.json'));
fs.mkdirSync(path.dirname(outPath), { recursive: true });
fs.writeFileSync(outPath, JSON.stringify(out, null, 2));
console.log(JSON.stringify({ base, changed: srcChanged.length, testIds: testIds.size, affected: affected.length, skipped: skipped.length }, null, 2));
console.error(`changed-flows: base=${base}, ${srcChanged.length} src files, ${affected.length} affected flows -> ${outPath}`);
if (affected.length) console.error(`affected: ${affected.join(' ')}`);
