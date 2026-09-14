import { test } from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { spawnSync } from 'node:child_process';

const ROOT = path.resolve(path.dirname(new URL(import.meta.url).pathname), '..', '..');
const SCRIPT = path.join(ROOT, 'skills', 'engineering', 'product-review', 'scripts', 'build-review.mjs');

function build(review) {
  const d = fs.mkdtempSync(path.join(os.tmpdir(), 'product-review-test-'));
  const file = path.join(d, 'review.json');
  fs.writeFileSync(file, typeof review === 'string' ? review : JSON.stringify(review));
  const p = spawnSync('node', [SCRIPT, '--review', file, '--out', path.join(d, 'report.html')], { encoding: 'utf8' });
  const html = fs.existsSync(path.join(d, 'report.html')) ? fs.readFileSync(path.join(d, 'report.html'), 'utf8') : '';
  return { status: p.status, stderr: p.stderr, html };
}

const good = {
  feature: 'Invite from circle',
  target: 'PR #1',
  overall: 'NEEDS A CONVERSATION',
  items: [
    { n: 1, expectation: 'Invite button sits on the circle page', verdict: 'MATCHES', note: '', code: 'app/circle.tsx:40' },
    { n: 2, expectation: 'Tapping invite opens the share sheet', verdict: 'MISSING', note: 'The button exists but tapping it does nothing.', code: 'app/circle.tsx:52' },
    { n: 3, expectation: 'Empty circle shows the invite prompt', verdict: "CAN'T TELL", note: 'Needs a build or URL.' },
  ],
  extras: ['A confetti animation on join, not in any source'],
  bounds: ['code-only'],
};

test('valid review renders the overall call, agenda, extras, and bounds', () => {
  const r = build(good);
  assert.equal(r.status, 0, r.stderr);
  assert.match(r.html, /Needs a conversation/);
  assert.match(r.html, /Tapping invite opens the share sheet/);
  assert.match(r.html, /confetti/);
  assert.match(r.html, /code-only/);
  assert.match(r.html, /1 matches, 1 missing, 1 can&#039;t tell|1 matches, 1 missing, 1 can't tell/);
});

test('aligned review renders the aligned call and no agenda', () => {
  const r = build({ ...good, overall: 'ALIGNED', items: [good.items[0]], extras: [], bounds: [] });
  assert.equal(r.status, 0, r.stderr);
  assert.match(r.html, /Aligned with what you expected/);
  assert.doesNotMatch(r.html, /class="agenda"/);
});

test('report has no pills, wash boxes, middots, or footer', () => {
  const r = build(good);
  assert.doesNotMatch(r.html, /border-radius:999px/);
  assert.doesNotMatch(r.html, /<footer>/);
  assert.doesNotMatch(r.html, /·/);
});

test('rejects a bad overall, a bad verdict, a missing note, and missing evidence', () => {
  const r = build({ feature: 'x', overall: 'MAYBE', items: [{ n: 1, expectation: 'e', verdict: 'NOPE' }, { n: 2, expectation: 'f', verdict: 'DRIFTED', note: 'moved' }] });
  assert.equal(r.status, 1);
  assert.match(r.stderr, /overall must be one of/);
  assert.match(r.stderr, /verdict must be one of/);
  assert.match(r.stderr, /needs a note/);
  assert.match(r.stderr, /cites no evidence/);
  assert.equal(r.html, '');
});

test('rejects items that are not an array and invalid JSON', () => {
  assert.equal(build({ overall: 'ALIGNED', items: 'nope' }).status, 1);
  assert.equal(build('{not json').status, 1);
});

// Build a review whose shots are real files in the review dir, so b64() can read them.
function buildWithShots(makeItems) {
  const d = fs.mkdtempSync(path.join(os.tmpdir(), 'product-review-shots-'));
  const shot = (name) => {
    const p = path.join(d, name);
    // A 1x1 PNG; sips may reject it, build-review falls back to reading raw bytes.
    fs.writeFileSync(p, Buffer.from('89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4890000000a49444154789c6360000002000154a24f9f0000000049454e44ae426082', 'hex'));
    return p;
  };
  const review = { feature: 'Shots', target: 'PR #2', overall: 'ALIGNED', items: makeItems(shot), extras: [], bounds: [] };
  fs.writeFileSync(path.join(d, 'review.json'), JSON.stringify(review));
  const p = spawnSync('node', [SCRIPT, '--review', path.join(d, 'review.json'), '--out', path.join(d, 'report.html')], { encoding: 'utf8' });
  const html = fs.existsSync(path.join(d, 'report.html')) ? fs.readFileSync(path.join(d, 'report.html'), 'utf8') : '';
  return { status: p.status, stderr: p.stderr, html };
}

test('renders one screenshot per flow, and several from an actuals array', () => {
  const r = buildWithShots((shot) => [
    { n: 1, expectation: 'Home shows the card', verdict: 'MATCHES', note: '', flow: 'home', actual: shot('a.png') },
    { n: 2, expectation: 'Create walks its states', verdict: 'DRIFTED', note: 'off', flow: 'create', actuals: [shot('b.png'), shot('c.png')] },
  ]);
  assert.equal(r.status, 0, r.stderr);
  // 3 embedded images total (1 + 2), each a data URI.
  assert.equal((r.html.match(/data:image\//g) || []).length, 3);
  assert.match(r.html, /Flow: <span class="code">home<\/span>/);
  assert.match(r.html, /What was built \(1\)/);
  assert.match(r.html, /What was built \(2\)/);
});

test('a visual item with no screenshot gets a loud placeholder, not silence', () => {
  const r = buildWithShots(() => [
    { n: 1, expectation: 'Empty state', verdict: "CAN'T TELL", note: 'never reached' },
  ]);
  assert.equal(r.status, 0, r.stderr);
  assert.match(r.html, /class="noshot"/);
  assert.match(r.html, /No screenshot/);
});

test('warns when a verified item has no screenshot, and rejects a non-array actuals', () => {
  const warned = buildWithShots(() => [
    { n: 1, expectation: 'Button', verdict: 'MATCHES', note: '', code: 'x.tsx:1' },
  ]);
  assert.match(warned.stderr, /no screenshot/i);
  const bad = build({ feature: 'x', overall: 'ALIGNED', items: [{ n: 1, expectation: 'e', verdict: 'MATCHES', note: '', actuals: 'nope' }] });
  assert.equal(bad.status, 1);
  assert.match(bad.stderr, /actuals must be an array/);
});
