#!/usr/bin/env node
// Writes run-summary.json for a scout run: per-flow status, failing step,
// failing-step screenshot path, timings. This file is the ONLY thing the AI
// reads after a run; the human reads report.html.
//
//   node summarize-run.mjs --run <runDir> [--junit result.xml,result2.xml]
//
// runDir layout (created by scout-run.sh):
//   <runDir>/debug/<timestamp>/<flow>/...   Maestro debug output
//   <runDir>/result*.xml                    JUnit files (default junit source)
import fs from 'node:fs';
import path from 'node:path';

const args = Object.fromEntries(
  process.argv.slice(2).reduce((a, v, i, arr) => (v.startsWith('--') ? [...a, [v.slice(2), arr[i + 1]]] : a), []),
);
const runDir = args.run;
if (!runDir || !fs.existsSync(runDir)) { console.error('summarize-run: --run <dir> required'); process.exit(1); }

const junitFiles = args.junit
  ? args.junit.split(',').map((f) => f.trim()).filter(Boolean)
  : fs.readdirSync(runDir).filter((f) => /^result.*\.xml$/.test(f)).map((f) => path.join(runDir, f));

const flows = {};
for (const file of junitFiles) {
  if (!fs.existsSync(file)) continue;
  const xml = fs.readFileSync(file, 'utf8');
  for (const m of xml.matchAll(/<testcase\b([^>]*)(\/>|>([\s\S]*?)<\/testcase>)/g)) {
    const attrs = m[1];
    const body = m[3] || '';
    const name = (attrs.match(/\bname="([^"]+)"/) || [])[1];
    if (!name) continue;
    const flow = name.replace(/\.yaml$/, '');
    const failed = /<failure|<error/.test(body);
    const failMsg = (body.match(/<(?:failure|error)[^>]*message="([^"]*)"/) || body.match(/<(?:failure|error)[^>]*>([\s\S]*?)<\/(?:failure|error)>/) || [])[1];
    const time = Number((attrs.match(/\btime="([^"]+)"/) || [])[1] || 0);
    // A retry result file for the same flow overrides an earlier failure.
    const isRetry = /retry/.test(path.basename(file));
    if (flows[flow] && !isRetry && flows[flow].status === 'passed') continue;
    flows[flow] = {
      status: failed ? 'failed' : 'passed',
      timeSec: time || flows[flow]?.timeSec || 0,
      ...(failed && failMsg ? { failure: failMsg.trim().slice(0, 500) } : {}),
      ...(failed && isRetry ? { retried: true } : {}),
    };
  }
}

// Attach the last screenshot of each failed flow (closest to the failing step)
// and count captures per flow.
function newestDebugDirs(base) {
  if (!fs.existsSync(base)) return [];
  return fs.readdirSync(base).map((d) => path.join(base, d))
    .filter((d) => { try { return fs.statSync(d).isDirectory(); } catch { return false; } })
    .sort((a, b) => fs.statSync(b).mtimeMs - fs.statSync(a).mtimeMs);
}
const debugBase = fs.existsSync(path.join(runDir, 'debug')) ? path.join(runDir, 'debug') : runDir;
const debugRuns = newestDebugDirs(debugBase);
for (const [flow, info] of Object.entries(flows)) {
  for (const run of debugRuns) {
    const flowDir = path.join(run, flow);
    if (!fs.existsSync(flowDir)) continue;
    const named = path.join(flowDir, 'takeScreenshot');
    const dir = fs.existsSync(named) ? named : flowDir;
    const pngs = fs.readdirSync(dir).filter((f) => f.toLowerCase().endsWith('.png')).sort();
    info.screenshots = pngs.length;
    if (info.status === 'failed' && pngs.length) info.lastScreenshot = path.join(dir, pngs[pngs.length - 1]);
    break;
  }
}

const list = Object.entries(flows).map(([flow, v]) => ({ flow, ...v }));
const failed = list.filter((f) => f.status === 'failed');
const summary = {
  runDir,
  at: new Date().toISOString(),
  total: list.length,
  passed: list.length - failed.length,
  failed: failed.length,
  greenlight: failed.length === 0 && list.length > 0,
  flows: list.sort((a, b) => (a.status === b.status ? a.flow.localeCompare(b.flow) : a.status === 'failed' ? -1 : 1)),
};
const out = path.join(runDir, 'run-summary.json');
fs.writeFileSync(out, JSON.stringify(summary, null, 2) + '\n');
console.log(`Wrote ${out} · ${summary.passed}/${summary.total} passed${failed.length ? ` · FAILED: ${failed.map((f) => f.flow).join(', ')}` : ''}`);
