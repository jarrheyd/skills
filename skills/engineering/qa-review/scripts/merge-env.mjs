#!/usr/bin/env node
// Merge KEY=VALUE lines from stdin into a .env file: existing keys are updated in
// place, new keys appended, everything else (comments, credentials) untouched.
// Used by the runner's seed step so fresh fixture ids reach the flows. Prints
// only the key names it wrote, never values.
import fs from 'node:fs';

const file = process.argv[2];
if (!file) {
  console.error('merge-env: usage: merge-env.mjs <env-file> < KEY=VALUE lines');
  process.exit(1);
}
const incoming = new Map();
for (const line of fs.readFileSync(0, 'utf8').split('\n')) {
  const m = line.match(/^([A-Z][A-Z0-9_]*)=(.*)$/);
  if (m) incoming.set(m[1], m[2].trim());
}
const lines = fs.existsSync(file) ? fs.readFileSync(file, 'utf8').split('\n') : [];
const seen = new Set();
const out = lines.map((line) => {
  const m = line.match(/^([A-Z][A-Z0-9_]*)=/);
  if (m && incoming.has(m[1])) {
    seen.add(m[1]);
    return `${m[1]}=${incoming.get(m[1])}`;
  }
  return line;
});
while (out.length && out[out.length - 1] === '') out.pop();
for (const [k, v] of incoming) if (!seen.has(k)) out.push(`${k}=${v}`);
fs.writeFileSync(file, out.join('\n') + '\n', { mode: 0o600 });
console.log(`merge-env: wrote ${incoming.size} key(s): ${[...incoming.keys()].join(' ')}`);
