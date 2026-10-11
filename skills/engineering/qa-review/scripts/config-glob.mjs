#!/usr/bin/env node
// Glob lookups against qa-review.config.json, kept out of bash to avoid escaping.
//   config-glob.mjs <config> setup <flow.yaml>     -> prints the flowSetup command for it, or nothing
//   config-glob.mjs <config> excluded <flow.yaml>  -> exit 0 if excludeFlows matches, else 1
//   config-glob.mjs <config> suite <flowsDir>      -> prints suite flow names (not _partials, not excluded)
import fs from 'node:fs';

const [, , configPath, cmd, arg] = process.argv;
const config = JSON.parse(fs.readFileSync(configPath, 'utf8'));
const toRe = (glob) =>
  new RegExp('^' + glob.split('*').map((part) => part.replace(/[.+?^${}()|[\]\\]/g, '\\$&')).join('.*') + '$');
const excluded = (name) => (config.excludeFlows || []).some((g) => toRe(g).test(name));

if (cmd === 'setup') {
  for (const [glob, command] of Object.entries(config.flowSetup || {})) {
    if (toRe(glob).test(arg)) {
      process.stdout.write(command);
      break;
    }
  }
} else if (cmd === 'excluded') {
  process.exit(excluded(arg) ? 0 : 1);
} else if (cmd === 'suite') {
  const names = fs.readdirSync(arg).filter((f) => f.endsWith('.yaml') && !f.startsWith('_') && !excluded(f));
  process.stdout.write(names.sort().join('\n'));
} else {
  console.error('config-glob: unknown command');
  process.exit(2);
}
