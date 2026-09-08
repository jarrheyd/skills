import { test } from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { execFileSync, spawnSync } from 'node:child_process';

const ROOT = path.resolve(path.dirname(new URL(import.meta.url).pathname), '..', '..');
const S = path.join(ROOT, 'skills', 'engineering', 'qa-review', 'scripts');
const tmp = () => fs.mkdtempSync(path.join(os.tmpdir(), 'qa-review-test-'));

function runDir({ base, retry }) {
  const d = tmp();
  fs.mkdirSync(path.join(d, 'debug'));
  fs.writeFileSync(path.join(d, 'result.xml'), `<testsuite>${base}</testsuite>`);
  if (retry) fs.writeFileSync(path.join(d, 'result-retry-login.xml'), `<testsuite>${retry}</testsuite>`);
  fs.writeFileSync(path.join(d, 'm.json'), JSON.stringify({ title: 't', categories: ['A'], journeys: [
    { flow: 'login', category: 'A', q: 'q', a: 'a' }, { flow: 'home', category: 'A', q: 'q2', a: 'a2' }] }));
  return d;
}
const FAIL = '<testcase name="login.yaml"><failure message="boom"/></testcase><testcase name="home.yaml"/>';
const PASS_LOGIN = '<testcase name="login.yaml"/>';

function summary(d) {
  execFileSync('node', [path.join(S, 'summarize-run.mjs'), '--run', d], { stdio: 'pipe' });
  return JSON.parse(fs.readFileSync(path.join(d, 'run-summary.json'), 'utf8'));
}
function report(d, junitOrder) {
  const out = path.join(d, 'r.html');
  execFileSync('node', [path.join(S, 'build-report.mjs'), '--manifest', path.join(d, 'm.json'), '--debug', path.join(d, 'debug'),
    '--junit', junitOrder.map((f) => path.join(d, f)).join(','), '--out', out, '--state', path.join(d, 's.json')], { stdio: 'pipe' });
  return fs.readFileSync(out, 'utf8');
}

test('retry pass: summary and report both green, flow marked retried', () => {
  const d = runDir({ base: FAIL, retry: PASS_LOGIN });
  const s = summary(d);
  assert.equal(s.greenlight, true);
  assert.equal(s.flows.find((f) => f.flow === 'login').retried, true);
  for (const order of [['result.xml', 'result-retry-login.xml'], ['result-retry-login.xml', 'result.xml']]) {
    const html = report(d, order);
    assert.match(html, /All journeys green/);
    assert.match(html, /Passed on retry/);
    assert.doesNotMatch(html, /needs? a look/);
  }
});

test('retry fail: summary and report both red, flow marked retried', () => {
  const d = runDir({ base: FAIL, retry: '<testcase name="login.yaml"><failure message="again"/></testcase>' });
  const s = summary(d);
  assert.equal(s.greenlight, false);
  assert.equal(s.flows.find((f) => f.flow === 'login').retried, true);
  const html = report(d, ['result-retry-login.xml', 'result.xml']);
  assert.match(html, /1 needs a look/);
});

test('no retry: plain pass has no retried flag', () => {
  const d = runDir({ base: '<testcase name="login.yaml"/><testcase name="home.yaml"/>' });
  const s = summary(d);
  assert.equal(s.greenlight, true);
  assert.equal(s.flows.every((f) => !f.retried), true);
});

test('report has no pills, dots, or footer', () => {
  const d = runDir({ base: FAIL, retry: PASS_LOGIN });
  const html = report(d, ['result.xml', 'result-retry-login.xml']);
  assert.doesNotMatch(html, /border-radius:999px/);
  assert.doesNotMatch(html, /class="dot"/);
  assert.doesNotMatch(html, /<footer>/);
  assert.doesNotMatch(html, /·/);
});

test('guard-env refuses substring matches and allows real markers', () => {
  const guard = path.join(S, 'guard-env.sh');
  const refuse = ['https://app.devhub.com', 'https://latest.acme.com', 'com.acme.developer', 'https://contest.acme.com', 'https://backstage.io', 'https://api.acme.com', 'com.symph.kindred'];
  const allow = ['https://staging.acme.com', 'http://localhost:3000', 'com.acme.app.dev', 'https://dev2.acme.com', 'https://staging-eu.acme.com/login', 'https://app.acme.local', 'https://pr-12.preview.acme.com', 'https://user:pw@qa.acme.com:8443/x'];
  for (const t of refuse) assert.equal(spawnSync('bash', [guard, t]).status, 2, `${t} should be refused`);
  for (const t of allow) assert.equal(spawnSync('bash', [guard, t]).status, 0, `${t} should be allowed`);
  assert.equal(spawnSync('bash', [guard, 'https://api.acme.com'], { env: { ...process.env, SCOUT_ALLOW_PROD: '1' } }).status, 0);
  assert.equal(spawnSync('bash', [guard]).status, 1);
});

// Carry-forward: a flow that did not run this time still shows its last
// evidence, and counts green only while that evidence describes this build and
// is inside the carry window.
function carryDir({ buildHash, ranFlow = 'home' }) {
  const d = tmp();
  fs.mkdirSync(path.join(d, 'debug'));
  fs.writeFileSync(path.join(d, 'result.xml'), `<testsuite><testcase name="${ranFlow}.yaml"/></testsuite>`);
  fs.writeFileSync(path.join(d, 'm.json'), JSON.stringify({ title: 't', categories: ['A'], journeys: [
    { flow: 'login', category: 'A', q: 'q', a: 'a' }, { flow: 'home', category: 'A', q: 'q2', a: 'a2' }] }));
  if (buildHash) fs.writeFileSync(path.join(d, 'build.json'), JSON.stringify({ kind: 'binary', hash: buildHash, at: new Date().toISOString() }));
  return d;
}
// A stand-in for last week's report: one card with a real reel and provenance.
function priorReport(d, { captured, build }) {
  const p = path.join(d, 'previous.html');
  fs.writeFileSync(p, `<article class="qa" data-flow="login" data-captured="${captured}" data-build="${build}">
    <h3>q</h3><p>a</p><div class="reel"><figure class="phone">OLDSHOT</figure></div>
    <div class="foot"><span class="stamp ok">Verified</span></div></article>`);
  return p;
}
function carryReport(d, previous, extra = []) {
  const out = path.join(d, 'r.html');
  execFileSync('node', [path.join(S, 'build-report.mjs'), '--manifest', path.join(d, 'm.json'),
    '--debug', path.join(d, 'debug'), '--junit', path.join(d, 'result.xml'), '--out', out,
    '--state', path.join(d, 's.json'), '--previous', previous,
    ...(fs.existsSync(path.join(d, 'build.json')) ? ['--buildinfo', path.join(d, 'build.json')] : []),
    ...extra], { stdio: 'pipe' });
  return fs.readFileSync(out, 'utf8');
}
const DAYS = (n) => new Date(Date.now() - n * 864e5).toISOString();

test('same build, inside the window: evidence carries and counts green', () => {
  const d = carryDir({ buildHash: 'abc123' });
  const html = carryReport(d, priorReport(d, { captured: DAYS(2), build: 'abc123' }));
  assert.match(html, /OLDSHOT/);
  assert.match(html, /on this same build/);
  assert.match(html, /carried/);
  assert.match(html, /All journeys green/);
  assert.doesNotMatch(html, /reel stale/);
});

test('build changed: evidence still shows, dimmed, and does not count green', () => {
  const d = carryDir({ buildHash: 'NEWBUILD' });
  const html = carryReport(d, priorReport(d, { captured: DAYS(1), build: 'abc123' }));
  assert.match(html, /OLDSHOT/);
  assert.match(html, /reel stale/);
  assert.match(html, /ran before the current build/);
  assert.match(html, /Needs a rerun/);
  assert.doesNotMatch(html, /All journeys green/);
});

test('older than the carry window: expired even on the same build', () => {
  const d = carryDir({ buildHash: 'abc123' });
  const html = carryReport(d, priorReport(d, { captured: DAYS(30), build: 'abc123' }));
  assert.match(html, /reel stale/);
  assert.match(html, /more than 7 days old/);
  assert.doesNotMatch(html, /All journeys green/);
});

test('no build fingerprint: carried evidence expires rather than counting green', () => {
  const d = carryDir({ buildHash: null });
  const html = carryReport(d, priorReport(d, { captured: DAYS(1), build: 'abc123' }));
  assert.match(html, /reel stale/);
  assert.match(html, /build it ran against is unknown/);
  assert.doesNotMatch(html, /All journeys green/);
});

test('provenance survives a chain of carries', () => {
  const first = carryDir({ buildHash: 'abc123' });
  const once = carryReport(first, priorReport(first, { captured: DAYS(1), build: 'abc123' }));
  const chained = path.join(first, 'chained.html');
  fs.writeFileSync(chained, once);
  // Carrying a carried reel keeps the ORIGINAL date and build, so age is
  // measured from the real capture and never resets on every partial run.
  const second = carryDir({ buildHash: 'abc123' });
  const html = carryReport(second, chained);
  assert.match(html, /OLDSHOT/);
  assert.match(html, /data-build="abc123"/);
  assert.match(html, /carried/);
});

test('the carry window is configurable', () => {
  const d = carryDir({ buildHash: 'abc123' });
  const html = carryReport(d, priorReport(d, { captured: DAYS(10), build: 'abc123' }), ['--carrydays', '30']);
  assert.doesNotMatch(html, /reel stale/);
});

test('header counts each state and never reads as a full pass on a partial run', () => {
  const d = carryDir({ buildHash: 'NEWBUILD' });
  const html = carryReport(d, priorReport(d, { captured: DAYS(1), build: 'abc123' }));
  assert.match(html, /1 verified this run/);
  assert.match(html, /1 needs a rerun/);
  assert.match(html, /still to run/);
});

test('open-report opens the report, and says so when it cannot', () => {
  const opener = path.join(S, 'open-report.sh');
  const d = tmp();
  const built = path.join(d, 'report.html');
  fs.writeFileSync(built, '<html></html>');
  const marker = path.join(d, 'opened.txt');
  const fake = path.join(d, 'fake-open.sh');
  fs.writeFileSync(fake, `#!/usr/bin/env bash\necho "$1" > ${marker}\n`);
  fs.chmodSync(fake, 0o755);
  const env = { ...process.env, SCOUT_OPEN_CMD: fake, CI: '' };

  const ok = spawnSync('bash', [opener, built], { env, encoding: 'utf8' });
  assert.equal(ok.status, 0);
  assert.equal(fs.readFileSync(marker, 'utf8').trim(), built);

  fs.rmSync(marker);
  const off = spawnSync('bash', [opener, built], { env: { ...env, SCOUT_NO_OPEN: '1' }, encoding: 'utf8' });
  assert.equal(off.status, 0);
  assert.equal(fs.existsSync(marker), false);
  assert.match(off.stdout, /SKIPPED/);

  const missing = spawnSync('bash', [opener, path.join(d, 'gone.html')], { env, encoding: 'utf8' });
  assert.equal(missing.status, 0);
  assert.match(missing.stderr, /no report at/);
  assert.equal(spawnSync('bash', [opener], { env }).status, 1);
});

test('scout-run opens the report it built', () => {
  const runner = fs.readFileSync(path.join(S, 'scout-run.sh'), 'utf8');
  assert.match(runner, /open-report\.sh" "\$RUN_DIR\/report\.html"/);
});

test('prune-runs keeps the newest N', () => {
  const home = tmp();
  const runs = path.join(home, '.scout', 'proj', 'runs');
  fs.mkdirSync(runs, { recursive: true });
  for (const n of ['a', 'b', 'c', 'd']) {
    fs.mkdirSync(path.join(runs, n));
    const t = new Date(2026, 0, n.charCodeAt(0) - 96);
    fs.utimesSync(path.join(runs, n), t, t);
  }
  execFileSync('node', [path.join(S, 'prune-runs.mjs'), '--project', 'proj', '--keep', '2'], { env: { ...process.env, HOME: home }, stdio: 'pipe' });
  assert.deepEqual(fs.readdirSync(runs).sort(), ['c', 'd']);
});
