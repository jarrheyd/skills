#!/usr/bin/env node
// Pull "moments" out of Claude Code session transcripts: the points where the
// person reacted to what the agent did, interrupted it, repeated themselves,
// or where a tool kept failing. Output is JSONL, one moment per line.
//
//   harvest.mjs --since 7d                 every session touched in the last 7 days
//   harvest.mjs --session <id>             one session
//   harvest.mjs --latest --cwd <dir>       the newest session for a working directory
//   --out <file>   write there (default stdout)    --summary   counts only, to stderr
//   --digest       compact Markdown grouped by session instead of JSONL (for reading a whole week)
//   --projects-dir <dir>   default ~/.claude/projects    --titles-dir <dir>   session title metadata

import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import readline from 'node:readline';
import { pathToFileURL } from 'node:url';

const DROP_PREFIXES = [
  '<task-notification', '<local-command-caveat', '<command-name', '<command-message', '<command-args',
  '<local-command-stdout', '<local-command-stderr', '<bash-input', '<bash-stdout', '<bash-stderr',
  'This session is being continued', 'Base directory for this skill', 'The previous response failed',
  'Continue from where you left off', 'Caveat: The messages below', '<user-prompt-submit-hook',
  '<recommended_plugins', '<turn_aborted',
];
// valley briefs and relays that reach a chat through the office plugin (not his words)
const VALLEY_MACHINE = /^(From Jarrhey's mission control|Reply with the single word|\[from |From the EA brief|Helper chat "|You take over from|You were moved to|Jarrhey moved you to|Jarrhey says close this chat|Still late after|Due within|LATE:|\/[\w:-]+(\s|$))/;
// valley wakes, probes and relays sent with `claude --resume <id> "<text>"` carry no origin, so they
// drop by prefix whatever the origin (retro 10-24: ~100 of 402 moments were these)
const VALLEY_RESUME = /^(Reply with exactly|Ask me with AskUserQuestion, one question "Probe|keeper pass |InTown loop wake|EVENT from mission control|FYI, the valley handled|FOLLOW UP\. You are|HEARTBEAT|Routine failed, fix it now|Your first start hit|Your sign-in stopped|Delivery check|Continue the Codex chat|Your last turn stopped|From valley:|From handoff watch|From checker:)/;
const OS_PREFIXES = ['<scheduled-task', '[SCHEDULED TASK', '<automation', '(Re-invocation of', 'Another Claude session sent a message'];
const STRIP_BLOCKS = [
  /<system-reminder>[\s\S]*?<\/system-reminder>/g,
  /<environment_context>[\s\S]*?<\/environment_context>/g,
  /<ide_selection>[\s\S]*?<\/ide_selection>/g,
  /<ide_opened_file>[\s\S]*?<\/ide_opened_file>/g,
  /<pasted_content[^>]*>[\s\S]*?<\/pasted_content>/g,
  /<artifact-view-context[\s\S]*?<\/artifact-view-context>/g,
];
const CORRECTION = /^(no\b|nope|wrong|not\b|don'?t|stop|again|still|why did|why are|actually)|you (didn'?t|forgot|missed|broke|should)|i (said|told you|asked|meant)|not what i|try again|should(n'?t)? (be|have)|instead/i;
// The retry button and a bare "continue" mean the run died or stalled, not that the work was wrong.
const RETRY = /^(try again( now)?|continue|go on|keep going|resume)[.!]?$/i;
const DENIED = /doesn't want to proceed|user denied|permission (was )?denied|rejected by the user/i;

export function clean(text) {
  let t = String(text || '');
  for (const re of STRIP_BLOCKS) t = t.replace(re, ' ');
  return t.replace(/[ \t]+\n/g, '\n').trim();
}

function textOf(content) {
  if (typeof content === 'string') return { text: content, results: [] };
  if (!Array.isArray(content)) return { text: '', results: [] };
  const parts = [];
  const results = [];
  for (const c of content) {
    if (!c || typeof c !== 'object') continue;
    if (c.type === 'text') parts.push(c.text || '');
    if (c.type === 'tool_result') {
      const body = Array.isArray(c.content) ? c.content.map((x) => (x && x.text) || '').join('\n') : String(c.content || '');
      results.push({ id: c.tool_use_id, error: !!c.is_error, body });
    }
  }
  return { text: parts.join('\n'), results };
}

const clip = (s, n) => (s.length > n ? s.slice(0, n) + ' […]' : s);
const norm = (s) => s.toLowerCase().replace(/[^a-z0-9]+/g, ' ').trim();

/** Feed one transcript's records in order; returns the moments found. */
export function harvestRecords(records, meta = {}) {
  const moments = [];
  const st = { said: '', ran: [], tools: {}, streak: { name: '', n: 0, flagged: false }, seen: new Map(), acted: false, session: meta.session || '', project: meta.project || '' };
  const push = (kind, ts, text, extra = {}) => moments.push({
    kind, session: st.session, title: meta.title || '', project: st.project, ts,
    text: clip(text, 1500), before: { said: clip(st.said, 500), ran: st.ran.slice(-4) }, ...extra,
  });

  for (const d of records) {
    if (!d || typeof d !== 'object' || d.isSidechain) continue;
    if (d.sessionId && !st.session) st.session = d.sessionId;
    if (d.cwd) st.project = d.cwd;

    if (d.type === 'assistant' && d.message) {
      for (const c of Array.isArray(d.message.content) ? d.message.content : []) {
        if (c && c.type === 'text' && (c.text || '').trim()) { st.said = c.text.trim(); st.acted = true; }
        if (c && c.type === 'tool_use') { st.tools[c.id] = c.name || ''; st.ran.push(c.name || ''); st.acted = true; if (st.ran.length > 12) st.ran.shift(); }
      }
      continue;
    }
    if (d.type !== 'user' || d.isMeta || d.isCompactSummary || d.isVisibleInTranscriptOnly) continue;

    const { text: raw, results } = textOf(d.message && d.message.content);
    if (results.length) {
      for (const r of results) {
        const name = st.tools[r.id] || '';
        delete st.tools[r.id];
        if (DENIED.test(r.body.slice(0, 600))) push('denied', d.timestamp, r.body.slice(0, 300), { tool: name });
        if (r.error && !DENIED.test(r.body.slice(0, 600))) {
          if (st.streak.name === name) st.streak.n += 1; else st.streak = { name, n: 1, flagged: false };
          if (st.streak.n >= 3 && !st.streak.flagged) { st.streak.flagged = true; push('tool-fail', d.timestamp, r.body.slice(0, 300), { tool: name }); }
        } else if (!r.error) st.streak = { name: '', n: 0, flagged: false };
      }
      if (!raw.trim()) continue;
    }

    const head = raw.trimStart();
    if (head.startsWith('[Request interrupted')) { if (st.acted) push('interrupt', d.timestamp, head.slice(0, 80)); continue; }
    if (DROP_PREFIXES.some((p) => head.startsWith(p))) continue;
    if (OS_PREFIXES.some((p) => head.startsWith(p))) continue;
    if (VALLEY_MACHINE.test(head) || VALLEY_RESUME.test(head)) continue;
    // Newer transcripts say who spoke; trust that over prefixes when it is there.
    const origin = d.origin && d.origin.kind;
    // His replies typed in the valley messenger arrive through the office plugin as his own
    // turn (asUser); the valley's machine briefs take the same road, so they drop by prefix.
    const fromValley = origin === 'plugin' && d.origin.name === 'office' && d.origin.asUser && !VALLEY_MACHINE.test(head);
    if (origin && origin !== 'human' && !fromValley) continue;
    if (!origin && (d.promptSource === 'system' || d.promptSource === 'sdk') && 'origin' in d) continue;

    const text = clean(raw);
    if (!text) continue;
    const key = norm(text);
    const repeats = st.seen.get(key) || 0;
    st.seen.set(key, repeats + 1);
    if (!st.acted) continue; // the opening ask is not a reaction to anything
    if (RETRY.test(text)) push('retry', d.timestamp, text);
    else if (repeats > 0 && key.length > 0) push('repeat', d.timestamp, text, { times: repeats + 1 });
    else push('reply', d.timestamp, text, { ...(CORRECTION.test(text) ? { hint: 'correction' } : {}), ...(d.midTurn ? { midTurn: true } : {}) });
  }
  return moments;
}

async function readTranscript(file) {
  const out = [];
  const rl = readline.createInterface({ input: fs.createReadStream(file), crlfDelay: Infinity });
  for await (const line of rl) {
    if (!line || line.length < 20) continue;
    // Skip the bulky records nobody reads here before paying for JSON.parse.
    if (!line.includes('"type":"user"') && !line.includes('"type":"assistant"') && !line.includes('"queued_command"')) continue;
    try { out.push(slim(JSON.parse(line))); } catch { /* a torn last line while the session is still writing */ }
  }
  return out;
}

// Keep only what harvestRecords reads, so a 100MB transcript does not sit in memory whole.
function slim(d) {
  // A message typed while the agent was mid-turn is stored as an attachment, not a user record.
  const q = d.type === 'attachment' && d.attachment && d.attachment.type === 'queued_command' ? d.attachment : null;
  if (q) {
    return { type: 'user', isSidechain: d.isSidechain, sessionId: d.sessionId, cwd: d.cwd, timestamp: d.timestamp, origin: q.origin, midTurn: true, message: { content: typeof q.prompt === 'string' ? q.prompt : (Array.isArray(q.prompt) ? q.prompt.filter((c) => c && c.type === 'text') : '') } };
  }
  const m = d.message;
  let content = m && m.content;
  if (Array.isArray(content)) {
    content = content.map((c) => {
      if (!c || typeof c !== 'object') return c;
      if (c.type === 'tool_use') return { type: 'tool_use', id: c.id, name: c.name };
      if (c.type === 'tool_result') {
        const body = Array.isArray(c.content) ? c.content.map((x) => (x && x.text) || '').join('\n') : String(c.content || '');
        return { type: 'tool_result', tool_use_id: c.tool_use_id, is_error: c.is_error, content: body.slice(0, 600) };
      }
      if (c.type === 'text') return { type: 'text', text: c.text };
      return null;
    }).filter(Boolean);
  }
  return {
    type: d.type, isSidechain: d.isSidechain, isMeta: d.isMeta, isCompactSummary: d.isCompactSummary,
    isVisibleInTranscriptOnly: d.isVisibleInTranscriptOnly, sessionId: d.sessionId, cwd: d.cwd, timestamp: d.timestamp,
    origin: d.origin, promptSource: d.promptSource, ...('origin' in d ? {} : { noOrigin: true }),
    message: m ? { content } : undefined,
  };
}

function parseSince(v) {
  const m = /^(\d+)([dh])$/.exec(v || '');
  if (m) return Date.now() - Number(m[1]) * (m[2] === 'd' ? 86400e3 : 3600e3);
  const t = Date.parse(v);
  if (Number.isNaN(t)) throw new Error(`--since wants 7d, 12h or an ISO date, got "${v}"`);
  return t;
}

export function slugFor(cwd) { return cwd.replace(/[^a-zA-Z0-9]/g, '-'); }

function listTranscripts(projectsDir, { since, session, latestCwd }) {
  const files = [];
  if (!fs.existsSync(projectsDir)) return files;
  const dirs = latestCwd ? [slugFor(latestCwd)] : fs.readdirSync(projectsDir);
  for (const dir of dirs) {
    const full = path.join(projectsDir, dir);
    let names;
    try { names = fs.readdirSync(full); } catch { continue; }
    for (const n of names) {
      if (!n.endsWith('.jsonl')) continue;
      if (session && n !== `${session}.jsonl`) continue;
      const f = path.join(full, n);
      const st = fs.statSync(f);
      if (!st.isFile() || (since && st.mtimeMs < since)) continue;
      files.push({ file: f, mtime: st.mtimeMs, session: n.slice(0, -6) });
    }
  }
  files.sort((a, b) => b.mtime - a.mtime);
  return latestCwd ? files.slice(0, 1) : files;
}

function loadTitles(dir) {
  const titles = new Map();
  const walk = (d, depth) => {
    let ents;
    try { ents = fs.readdirSync(d, { withFileTypes: true }); } catch { return; }
    for (const e of ents) {
      const p = path.join(d, e.name);
      if (e.isDirectory() && depth < 3) walk(p, depth + 1);
      else if (e.isFile() && e.name.startsWith('local_') && e.name.endsWith('.json')) {
        try {
          const j = JSON.parse(fs.readFileSync(p, 'utf8'));
          if (j.cliSessionId) titles.set(j.cliSessionId, { title: j.title || '', scheduled: j.scheduledTaskId || '' });
        } catch { /* unreadable metadata is not worth stopping for */ }
      }
    }
  };
  walk(dir, 0);
  return titles;
}

async function main(argv) {
  const a = { projectsDir: path.join(os.homedir(), '.claude', 'projects'), titlesDir: path.join(os.homedir(), 'Library', 'Application Support', 'Claude', 'claude-code-sessions') };
  for (let i = 0; i < argv.length; i++) {
    const k = argv[i];
    if (k === '--since') a.since = parseSince(argv[++i]);
    else if (k === '--session') a.session = argv[++i];
    else if (k === '--latest') a.latest = true;
    else if (k === '--cwd') a.cwd = argv[++i];
    else if (k === '--out') a.out = argv[++i];
    else if (k === '--summary') a.summary = true;
    else if (k === '--digest') a.digest = true;
    else if (k === '--projects-dir') a.projectsDir = argv[++i];
    else if (k === '--titles-dir') a.titlesDir = argv[++i];
    else throw new Error(`unknown argument ${k}`);
  }
  if (!a.since && !a.session && !a.latest) throw new Error('give --since, --session or --latest');
  const files = listTranscripts(a.projectsDir, { since: a.since, session: a.session, latestCwd: a.latest ? (a.cwd || process.cwd()) : null });
  const titles = loadTitles(a.titlesDir);
  const out = a.out ? fs.createWriteStream(a.out) : process.stdout;
  const counts = {};
  let total = 0;
  let lastSession = '';
  for (const f of files) {
    const t = titles.get(f.session) || {};
    const moments = harvestRecords(await readTranscript(f.file), { session: f.session, title: t.title, project: '' });
    for (const m of moments) {
      if (a.since && Date.parse(m.ts) < a.since) continue;
      if (t.scheduled) m.scheduled = t.scheduled;
      if (a.digest && !a.summary) {
        if (m.session !== lastSession) { out.write(`\n## ${m.title || '(untitled)'} · ${path.basename(m.project || '?')} · ${m.session}${t.scheduled ? ' · scheduled ' + t.scheduled : ''}\n`); lastSession = m.session; }
        const one = (x, n) => clip(String(x || '').replace(/\s+/g, ' '), n);
        const tag = [m.kind, m.midTurn ? 'mid-turn' : '', m.hint || '', m.tool || '', m.times ? `x${m.times}` : ''].filter(Boolean).join(' ');
        out.write(`- ${m.ts.slice(0, 16)} [${tag}] ${one(m.text, 500)}\n    after: ${m.before.ran.slice(-3).join(', ') || 'no tool'} · "${one(m.before.said, 180)}"\n`);
      } else if (!a.summary) out.write(JSON.stringify(m) + '\n');
      const key = `${path.basename(m.project || '?')} · ${m.kind}`;
      counts[key] = (counts[key] || 0) + 1;
      total += 1;
    }
  }
  if (a.out) await new Promise((r) => out.end(r));
  console.error(`${files.length} sessions, ${total} moments`);
  for (const [k, v] of Object.entries(counts).sort((x, y) => y[1] - x[1])) console.error(`  ${String(v).padStart(4)}  ${k}`);
}

// ~/.claude/skills/retro is a symlink, so compare real paths or main never runs and the harvest is silently empty.
const entry = (() => { try { return fs.realpathSync(process.argv[1] || ''); } catch { return process.argv[1] || ''; } })();
if (import.meta.url === pathToFileURL(entry).href) {
  main(process.argv.slice(2)).catch((e) => { console.error(e.message); process.exit(1); });
}
