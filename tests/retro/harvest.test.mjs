import test from 'node:test';
import assert from 'node:assert/strict';
import { harvestRecords, clean, slugFor } from '../../skills/engineering/retro/scripts/harvest.mjs';

const user = (content, extra = {}) => ({ type: 'user', sessionId: 's1', cwd: '/work/app', timestamp: '2026-01-01T00:00:00Z', origin: { kind: 'human' }, message: { content }, ...extra });
const said = (text) => ({ type: 'assistant', message: { content: [{ type: 'text', text }] } });
const ran = (id, name) => ({ type: 'assistant', message: { content: [{ type: 'tool_use', id, name }] } });
const result = (id, body, error = false) => user([{ type: 'tool_result', tool_use_id: id, is_error: error, content: body }], { origin: undefined });

test('the opening ask is not a moment, a reply after the agent acted is', () => {
  const m = harvestRecords([user('build the report'), said('Done, it is in report.md'), user('no, it should be a table')]);
  assert.equal(m.length, 1);
  assert.equal(m[0].kind, 'reply');
  assert.equal(m[0].hint, 'correction');
  assert.equal(m[0].before.said, 'Done, it is in report.md');
  assert.equal(m[0].project, '/work/app');
});

test('automation speaking in the user role is dropped', () => {
  const m = harvestRecords([
    user('start'), said('ok'),
    user('<scheduled-task name="x">do things</scheduled-task>', { origin: { kind: 'task-notification' } }),
    user('Another Claude session sent a message: hi', { origin: { kind: 'peer' }, isMeta: true }),
    user('<task-notification>done</task-notification>', { origin: undefined, promptSource: 'system' }),
    user('injected by a script', { origin: null, promptSource: 'sdk' }),
    user('sidechain talk', { isSidechain: true }),
  ]);
  assert.deepEqual(m, []);
});

test('system reminders are stripped and an empty remainder is dropped', () => {
  assert.equal(clean('<system-reminder>noise</system-reminder>shorter please'), 'shorter please');
  const m = harvestRecords([user('a'), said('b'), user('<system-reminder>only noise</system-reminder>')]);
  assert.deepEqual(m, []);
});

test('interrupts, retries and repeats get their own kinds', () => {
  const m = harvestRecords([
    user('do it'), said('working'),
    user('[Request interrupted by user]'),
    user('Try again'),
    user('use the blue one'), said('used green'), user('use the blue one'),
  ]);
  assert.deepEqual(m.map((x) => x.kind), ['interrupt', 'retry', 'reply', 'repeat']);
  assert.equal(m[3].times, 2);
});

test('three failures of one tool in a row is one moment, a success resets it', () => {
  const recs = [user('go')];
  for (const id of ['a', 'b', 'c', 'd']) recs.push(ran(id, 'Bash'), result(id, 'exit 1', true));
  recs.push(ran('e', 'Bash'), result('e', 'fine'), ran('f', 'Bash'), result('f', 'exit 1', true));
  const m = harvestRecords(recs);
  assert.equal(m.length, 1);
  assert.equal(m[0].kind, 'tool-fail');
  assert.equal(m[0].tool, 'Bash');
});

test('a declined tool call is a moment', () => {
  const m = harvestRecords([user('go'), ran('a', 'Write'), result('a', "The user doesn't want to proceed with this tool use.", true)]);
  assert.equal(m[0].kind, 'denied');
  assert.equal(m[0].tool, 'Write');
});

test('a mid-turn message is kept and marked', () => {
  const m = harvestRecords([user('go'), said('on it'), user('also make it shorter', { midTurn: true })]);
  assert.equal(m[0].midTurn, true);
});

test('project folders map to the transcript directory name', () => {
  assert.equal(slugFor('/Users/a/My Project'), '-Users-a-My-Project');
});
