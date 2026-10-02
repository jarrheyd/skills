import { test } from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { execFileSync, spawnSync } from 'node:child_process';

const ROOT = path.resolve(path.dirname(new URL(import.meta.url).pathname), '..', '..');
const S = path.join(ROOT, 'skills', 'engineering', 'qa-review', 'scripts');
const tmp = () => fs.mkdtempSync(path.join(os.tmpdir(), 'qa-review-pw-'));
const { default: Reporter } = await import(path.join(S, 'playwright-reporter.mjs'));

const PNG = Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==', 'base64');
const project = (name, testDir) => ({ parent: null, project: () => ({ name, testDir }) });
// A stand-in for Playwright's TestCase: file, title, expected status, owning project.
function tc(testDir, file, title, { project: p = '', expected = 'passed', annotations = [] } = {}) {
  return { title, expectedStatus: expected, annotations, location: { file: path.join(testDir, file) }, parent: project(p, testDir) };
}
const res = (status, { retry = 0, shots = [], message } = {}) => ({
  status, retry, duration: 1500,
  error: message ? { message } : undefined,
  attachments: shots.map((name) => ({ name, contentType: 'image/png', body: PNG })),
});
function run(cases) {
  const runDir = tmp();
  const r = new Reporter({ runDir });
  r.onBegin({ rootDir: '/repo' }, { allTests: () => [...new Set(cases.map(([t]) => t))] });
  for (const [t, result] of cases) r.onTestEnd(t, result);
  r.onEnd();
  return runDir;
}
const read = (d, f) => fs.readFileSync(path.join(d, f), 'utf8');

test('one result per spec, red when any check in it failed', () => {
  const a = tc('/repo/tests', 'admin/invites.spec.ts', 'opens the list');
  const b = tc('/repo/tests', 'admin/invites.spec.ts', 'invite form validates');
  const c = tc('/repo/tests', 'client/help.spec.ts', 'articles load');
  const d = run([[a, res('passed', { shots: ['01-list'] })], [b, res('failed', { message: 'expected <b> "x" > y', shots: ['screenshot'] })], [c, res('passed')]]);
  const bad = read(d, 'result-admin-invites.xml');
  assert.match(bad, /<testcase id="admin-invites" name="admin-invites"/);
  assert.match(bad, /<failure message="1 of 2 checks failed: invite form validates"/);
  assert.doesNotMatch(bad.replace(/<[^>]+>/g, ''), /<b>/);
  assert.doesNotMatch(read(d, 'result-client-help.xml'), /<failure/);
  assert.deepEqual(fs.readdirSync(path.join(d, 'debug/playwright/admin-invites/takeScreenshot')), ['001-01-list.png']);
  assert.match(fs.readdirSync(path.join(d, 'debug/playwright/admin-invites/screenshots'))[0], /FAILED-invite-form-validates/);
});

test('a spec run under several projects is one flow per project', () => {
  const hr = tc('/repo/tests', 'access.spec.ts', 'sees its pages', { project: 'Client HR' });
  const fin = tc('/repo/tests', 'access.spec.ts', 'sees its pages', { project: 'client-finance' });
  const d = run([[hr, res('passed')], [fin, res('failed', { message: 'boom' })]]);
  assert.doesNotMatch(read(d, 'result-access--client-hr.xml'), /<failure/);
  assert.match(read(d, 'result-access--client-finance.xml'), /<failure/);
});

test('a spec in one named project keeps its plain name', () => {
  const a = tc('/repo/tests', 'public/sign-in.spec.ts', 'page renders', { project: 'public' });
  const b = tc('/repo/tests', 'public/sign-in.spec.ts', 'empty form refused', { project: 'public' });
  const d = run([[a, res('passed')], [b, res('passed')]]);
  assert.equal(fs.existsSync(path.join(d, 'result-public-sign-in.xml')), true);
});

test('green on retry writes both files, so the report says passed on retry', () => {
  const t = tc('/repo/tests', 'login.spec.ts', 'signs in');
  const d = run([[t, res('failed', { message: 'slow' })], [t, res('passed', { retry: 1 })]]);
  assert.match(read(d, 'result-login.xml'), /<failure/);
  assert.doesNotMatch(read(d, 'result-retry-login.xml'), /<failure/);
});

test('all skipped means no result, never a pass', () => {
  const t = tc('/repo/tests', 'hmo.spec.ts', 'not built yet');
  const d = run([[t, res('skipped')]]);
  assert.equal(fs.existsSync(path.join(d, 'result-hmo.xml')), false);
});

test('an expected failure keeps the flow green and lands in gaps.json', () => {
  const t = tc('/repo/tests', 'leaves.spec.ts', 'shows PTO', { expected: 'failed', annotations: [{ type: 'fail', description: 'TICKET-59 PTO not shown' }] });
  const d = run([[t, res('failed', { message: 'no PTO' })]]);
  assert.doesNotMatch(read(d, 'result-leaves.xml'), /<failure/);
  const gaps = JSON.parse(read(d, 'gaps.json'));
  assert.equal(gaps.items[0].area, 'leaves');
  assert.match(gaps.items[0].note, /TICKET-59/);
});

test('a flow annotation names the flow', () => {
  const t = tc('/repo/tests', 'misc.spec.ts', 'pays', { annotations: [{ type: 'flow', description: 'Checkout' }] });
  const d = run([[t, res('passed')]]);
  assert.equal(fs.existsSync(path.join(d, 'result-checkout.xml')), true);
});

// The runner with "runner": "playwright": a fake npx stands in for the suite and
// files results through the real reporter layout.
function repo({ url = 'https://uat.example.com' } = {}) {
  const home = tmp();
  const dir = path.join(home, 'repo');
  fs.mkdirSync(dir);
  fs.writeFileSync(path.join(dir, 'qa-review.config.json'), JSON.stringify({ project: 'pwproj', platform: 'web', runner: 'playwright', url, fingerprintCmd: 'echo build-42' }));
  fs.writeFileSync(path.join(dir, 'journeys.manifest.json'), JSON.stringify({ title: 't', categories: ['A'], journeys: [
    { flow: 'login', category: 'A', q: 'Can a user sign in?', a: 'a' }, { flow: 'home', category: 'A', q: 'q2', a: 'a2' }, { flow: 'later', category: 'A', q: 'q3', a: 'a3', planned: true }] }));
  const bin = path.join(home, 'bin');
  fs.mkdirSync(bin);
  fs.writeFileSync(path.join(bin, 'npx'), `#!/usr/bin/env bash
echo "$@" > "$QA_REVIEW_RUN_DIR/npx-args.txt"
mkdir -p "$QA_REVIEW_RUN_DIR/debug/playwright/login/takeScreenshot"
printf '<testsuites><testsuite><testcase name="login"/></testsuite></testsuites>' > "$QA_REVIEW_RUN_DIR/result-login.xml"
printf '<testsuites><testsuite><testcase name="home"><failure message="boom"/></testcase></testsuite></testsuites>' > "$QA_REVIEW_RUN_DIR/result-home.xml"
exit 1
`);
  fs.chmodSync(path.join(bin, 'npx'), 0o755);
  const env = { ...process.env, HOME: home, PATH: `${bin}:${process.env.PATH}`, QA_REVIEW_NO_OPEN: '1', QA_REVIEW_ALLOW_PARALLEL: '1', QA_REVIEW_CONFIG: '' };
  return { home, dir, env };
}
const newestRun = (home) => {
  const runs = path.join(home, '.qa-review', 'pwproj', 'runs');
  return path.join(runs, fs.readdirSync(runs).sort().pop());
};

test('playwright runner: no Maestro needed, results summarised and reported', () => {
  const { home, dir, env } = repo();
  const out = spawnSync('bash', [path.join(S, 'qa-review-run.sh'), '--repo', dir, '--tag', 'smoke'], { env, encoding: 'utf8' });
  assert.equal(out.status, 0, out.stderr + out.stdout);
  const run = newestRun(home);
  assert.match(read(run, 'npx-args.txt'), /playwright test --grep @smoke/);
  const summary = JSON.parse(read(run, 'run-summary.json'));
  assert.equal(summary.passed, 1);
  assert.equal(summary.failed, 1);
  assert.equal(summary.build.hash, 'build-42');
  assert.match(read(run, 'report.html'), /Can a user sign in\?/);
});

test('playwright runner: the regression script counts manifest flows, planned ones left out', () => {
  const { dir, env } = repo();
  const out = spawnSync('bash', [path.join(S, 'qa-review-regression.sh'), '--repo', dir], { env, encoding: 'utf8' });
  assert.equal(out.status, 0, out.stderr + out.stdout);
  assert.match(out.stdout, /passed: 1 {2}failed: 1 {2}without a result: 0/);
  assert.match(out.stdout, /failed: home/);
});

test('playwright runner: production is still refused', () => {
  const { dir, env } = repo({ url: 'https://app.example.com' });
  const out = spawnSync('bash', [path.join(S, 'qa-review-run.sh'), '--repo', dir], { env, encoding: 'utf8' });
  assert.equal(out.status, 2);
});
