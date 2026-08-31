#!/usr/bin/env node
// Keeps the newest N runs per project under ~/.scout/<project>/runs and deletes
// the rest (screenshots are the bulk of the disk use). Default keep: 2.
//
//   node prune-runs.mjs --project <name> [--keep 2]
import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';

const args = Object.fromEntries(
  process.argv.slice(2).reduce((a, v, i, arr) => (v.startsWith('--') ? [...a, [v.slice(2), arr[i + 1]]] : a), []),
);
const project = args.project || process.env.SCOUT_PROJECT;
if (!project) { console.error('prune-runs: --project <name> required'); process.exit(1); }
const keep = Math.max(1, Number(args.keep || 2));
const base = path.join(os.homedir(), '.scout', project, 'runs');
if (!fs.existsSync(base)) { console.log('prune-runs: nothing to prune'); process.exit(0); }

const runs = fs.readdirSync(base)
  .map((d) => path.join(base, d))
  .filter((d) => { try { return fs.statSync(d).isDirectory(); } catch { return false; } })
  .sort((a, b) => fs.statSync(b).mtimeMs - fs.statSync(a).mtimeMs);

const doomed = runs.slice(keep);
for (const d of doomed) fs.rmSync(d, { recursive: true, force: true });
console.log(`prune-runs: kept ${Math.min(keep, runs.length)}, deleted ${doomed.length}`);
