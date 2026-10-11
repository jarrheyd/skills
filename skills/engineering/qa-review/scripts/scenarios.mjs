#!/usr/bin/env node
// Helpers for config "scenarios": multi-step suites a project already runs from
// its own script (API setup between flows, flows in a fixed order).
//   scenarios.mjs <config> flows                 -> every flow name owned by a scenario (one per line)
//   scenarios.mjs <config> list                  -> name<TAB>cmd per scenario
//   scenarios.mjs <config> owned <name>          -> flows of one scenario
//   scenarios.mjs collect <artifactDir> <runDir> <name> <rc> <flow...>
//       Files each flow's result into <runDir>/result-<flow>.xml. A script that
//       wrote per-flow JUnit (<artifactDir>/NN-<flow>/result.xml) is used as is, last
//       attempt wins, and its debug folder is copied under <runDir>/debug so the
//       report and UI review see the screenshots. A flow with no result of its own
//       gets the scenario's overall result, marked as such in the failure text.
import fs from 'node:fs';
import path from 'node:path';

const [, , a1, cmd, ...rest] = process.argv;
const esc = (s) => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/"/g, '&quot;');
const junit = (flow, failure) =>
  `<?xml version="1.0"?><testsuites><testsuite name="scenario" tests="1" failures="${failure ? 1 : 0}"><testcase id="${esc(flow)}" name="${esc(flow)}">${failure ? `<failure>${esc(failure)}</failure>` : ''}</testcase></testsuite></testsuites>\n`;

if (cmd === 'collect' || a1 === 'collect') {
  const [artifactDir, runDir, name, rc, ...flows] = a1 === 'collect' ? [cmd, ...rest] : rest;
  const perFlow = new Map();
  if (fs.existsSync(artifactDir)) {
    for (const dir of fs.readdirSync(artifactDir).sort()) {
      const m = dir.match(/^\d+-(.+)$/);
      const xml = path.join(artifactDir, dir, 'result.xml');
      if (m && fs.existsSync(xml)) perFlow.set(m[1], { xml, debug: path.join(artifactDir, dir, 'debug') });
    }
  }
  let own = 0;
  for (const flow of flows) {
    const out = path.join(runDir, `result-${flow}.xml`);
    const hit = perFlow.get(flow);
    if (hit) {
      fs.copyFileSync(hit.xml, out);
      own += 1;
      // Copied, not linked: the report and the UI review walk real folders only.
      const dest = path.join(runDir, 'debug', `scenario-${name}-${flow}`);
      if (fs.existsSync(hit.debug)) {
        fs.rmSync(dest, { recursive: true, force: true });
        fs.mkdirSync(path.dirname(dest), { recursive: true });
        fs.cpSync(hit.debug, dest, { recursive: true });
      }
    } else {
      fs.writeFileSync(
        out,
        junit(flow, rc === '0' ? '' : `Scenario "${name}" failed (exit ${rc}); this flow has no result of its own. See ${runDir}/scenario-${name}.log`),
      );
    }
  }
  console.log(`scenarios: ${name}: ${own}/${flows.length} flow result(s) from the script, rest from its exit code ${rc}`);
  process.exit(0);
}

const config = JSON.parse(fs.readFileSync(a1, 'utf8'));
const scenarios = config.scenarios || [];
if (cmd === 'flows') process.stdout.write(scenarios.flatMap((s) => s.flows || []).join('\n'));
else if (cmd === 'list') process.stdout.write(scenarios.map((s) => `${s.name}\t${s.cmd}`).join('\n'));
else if (cmd === 'owned') process.stdout.write((scenarios.find((s) => s.name === rest[0])?.flows || []).join('\n'));
else {
  console.error('scenarios: unknown command');
  process.exit(2);
}
