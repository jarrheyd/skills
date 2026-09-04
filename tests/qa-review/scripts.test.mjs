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
