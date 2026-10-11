#!/usr/bin/env node
// check-flow-freshness.mjs — flow rot detector. Cross-references every id: selector
// a flow uses against the testIDs actually present in the app code. A selector with
// no match in code is rot: the flow will fail for the wrong reason (the screen is
// fine, the hook moved). Emits gaps.json {items:[{kind:"rot",flow,selector}]} so the
// regression mode repairs rot before a run counts. Zero-dep.
//
// Usage: node check-flow-freshness.mjs --repo <path> [--out gaps.json]

import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';

const args = Object.fromEntries(process.argv.slice(2).reduce((a, v, i, arr) => (v.startsWith('--') ? [...a, [v.slice(2), arr[i + 1]]] : a), []));
const REPO = path.resolve(args.repo || '.');
let project = args.project;
try { const c = JSON.parse(fs.readFileSync(path.join(REPO, '.maestro', 'qa-review.config.json'), 'utf8')); project = project || c.project; } catch {}

// --- all testIDs present in the app code (the source of truth) ---------------
const SKIP = new Set(['node_modules', '.git', 'ios', 'android', 'build', 'dist', '.next', 'Pods', 'vendor', '.expo', 'coverage', '.maestro']);
const codeIds = new Set();     // ids on a testID= attribute
const codeStrings = new Set(); // every kebab/colon string literal in code (catches
                               // testIDs centralized in a constants file + applied by reference)
const prefixSet = new Set();   // literal prefixes of template-literal testIDs
function scanCode(dir, depth = 0) {
  if (depth > 8) return;
  let ents = []; try { ents = fs.readdirSync(dir, { withFileTypes: true }); } catch { return; }
  for (const e of ents) {
    const full = path.join(dir, e.name);
    if (e.isDirectory()) { if (!SKIP.has(e.name)) scanCode(full, depth + 1); continue; }
    if (!/\.(tsx?|jsx?)$/.test(e.name)) continue;
    let s = ''; try { s = fs.readFileSync(full, 'utf8'); } catch { continue; }
    for (const m of s.matchAll(/(?:testID|data-testid)\s*=\s*[{"']\s*[`"']?([\w:-]+)/g)) codeIds.add(m[1]);
    for (const m of s.matchAll(/(?:testID|data-testid)\s*[:=]\s*[`"']([\w:-]+)/g)) codeIds.add(m[1]);
    // Template-literal testIDs (`page-${x}-cta`) => honor their literal prefix.
    for (const m of s.matchAll(/[`"']([\w:-]*)\$\{/g)) { if (m[1] && m[1].includes('-')) prefixSet.add(m[1]); }
    // Any quoted kebab/colon string literal: catches `x: 'login-phone-input'`.
    for (const m of s.matchAll(/['"`]([a-z][\w]*(?:[-:][\w]+)+)['"`]/g)) codeStrings.add(m[1]);
  }
}
scanCode(REPO);
const prefixes = [...prefixSet];
const known = (id) => codeIds.has(id) || codeStrings.has(id) || prefixes.some((p) => id.startsWith(p));

// --- every id: selector used by the flows ------------------------------------
const flowsDir = path.join(REPO, '.maestro', 'flows');
let flowFiles = [];
try { flowFiles = fs.readdirSync(flowsDir).filter((f) => f.endsWith('.yaml')); } catch {}
const items = [];
for (const f of flowFiles) {
  let s = ''; try { s = fs.readFileSync(path.join(flowsDir, f), 'utf8'); } catch { continue; }
  const ids = new Set();
  for (const m of s.matchAll(/\bid:\s*["']?([\w:-]+)["']?/g)) ids.add(m[1]);
  for (const id of ids) {
    // Skip env-substituted or regex-ish selectors; only check literal testIDs.
    if (id.includes('${') || /[|.*()]/.test(id)) continue;
    // Real testIDs are kebab/colon (or long); a bare short word is YAML/prose noise.
    if (!/[-:]/.test(id) && id.length < 8) continue;
    if (!known(id)) items.push({ kind: 'rot', flow: f.replace(/\.yaml$/, ''), selector: id });
  }
}

const outPath = args.out || (project ? path.join(os.homedir(), '.qa-review', project, 'gaps.json') : path.join(REPO, 'gaps.json'));
fs.mkdirSync(path.dirname(outPath), { recursive: true });
// Merge with any existing gaps (audit writes happy/unhappy/edge items too).
let existing = { items: [] };
try { existing = JSON.parse(fs.readFileSync(outPath, 'utf8')); } catch {}
const kept = (existing.items || []).filter((i) => i.kind !== 'rot');
fs.writeFileSync(outPath, JSON.stringify({ items: [...kept, ...items] }, null, 2));
const flowsWithRot = new Set(items.map((i) => i.flow)).size;
console.log(JSON.stringify({ codeIds: codeIds.size, flows: flowFiles.length, rot: items.length, flowsWithRot }, null, 2));
if (items.length) { console.error(`check-flow-freshness: ${items.length} rotten selector(s) across ${flowsWithRot} flow(s) -> ${outPath}`); for (const i of items.slice(0, 30)) console.error(`  ${i.flow}: ${i.selector}`); }
else console.error('check-flow-freshness: no rot, every flow selector matches a testID in code.');
