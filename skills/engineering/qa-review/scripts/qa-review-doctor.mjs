#!/usr/bin/env node
// qa-review doctor: is this project ready for a repeatable regression?
//   node qa-review-doctor.mjs --repo <path>
// Prints OK / WARN / FAIL per check with the fix for each. Exit 1 on any FAIL.
// Never prints credential values.
import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import { execSync } from 'node:child_process';

const args = Object.fromEntries(
  process.argv.slice(2).reduce((acc, cur, i, all) => (cur.startsWith('--') ? [...acc, [cur.slice(2), all[i + 1]]] : acc), []),
);
const repo = path.resolve(args.repo || '.');
const rows = [];
const add = (level, check, detail, fix = '') => rows.push({ level, check, detail, fix });
const has = (cmd) => {
  try {
    execSync(cmd, { stdio: 'ignore' });
    return true;
  } catch {
    return false;
  }
};

// Tools
const maestroOk = has('command -v maestro') || fs.existsSync(path.join(os.homedir(), '.maestro/bin/maestro'));
add(maestroOk ? 'OK' : 'FAIL', 'Maestro', maestroOk ? 'installed' : 'not found', 'curl -fsSL "https://get.maestro.mobile.dev" | bash');
add(has('java -version') ? 'OK' : 'FAIL', 'Java runtime', has('java -version') ? 'installed' : 'missing', 'brew install --cask temurin');

// Config
const cfgPath = path.join(repo, '.maestro/qa-review.config.json');
if (!fs.existsSync(cfgPath)) {
  add('FAIL', 'Config', `${cfgPath} missing`, 'run qa-review setup');
  report();
}
let c;
try {
  c = JSON.parse(fs.readFileSync(cfgPath, 'utf8'));
  add('OK', 'Config', 'valid JSON');
} catch (e) {
  add('FAIL', 'Config', `invalid JSON: ${e.message}`, 'fix the JSON');
  report();
}
for (const key of ['project', 'platform']) if (!c[key]) add('FAIL', `Config ${key}`, 'missing', `set "${key}"`);
if (c.platform !== 'web' && !c.appId) add('FAIL', 'Config appId', 'missing for a device platform', 'set "appId" to the dev/staging bundle id');
if (c.platform === 'mobile') {
  add(has('xcrun simctl help') ? 'OK' : 'FAIL', 'Xcode simulator tools', has('xcrun simctl help') ? 'available' : 'missing', 'install Xcode');
  const sim = c.simulator || 'iPhone 17';
  const found = has(`xcrun simctl list devices available | grep -q "${sim} ("`);
  add(found ? 'OK' : 'WARN', 'Simulator', found ? `"${sim}" available` : `"${sim}" not found`, 'set "simulator" to an installed device name');
}
if (c.platform === 'android') add(has('command -v adb') ? 'OK' : 'FAIL', 'adb', has('command -v adb') ? 'on PATH' : 'missing', 'install Android platform-tools');
add(c.buildCmd ? 'OK' : 'WARN', 'buildCmd', c.buildCmd ? 'set' : 'none: runs test whatever build is installed', 'add a buildCmd so every run tests the current code');

// Flows
const flowsDir = path.join(repo, '.maestro/flows');
const flows = fs.existsSync(flowsDir) ? fs.readdirSync(flowsDir).filter((f) => f.endsWith('.yaml') && !f.startsWith('_')) : [];
add(flows.length ? 'OK' : 'FAIL', 'Flows', `${flows.length} flow(s)`, 'run qa-review setup');
const loose = flows.filter((f) => /^(zz|tmp|scratch|test-|pr-|ss-)/.test(f) && !(c.excludeFlows || []).length);
if (loose.length) add('WARN', 'Throwaway flows', `${loose.length} look throwaway (${loose.slice(0, 3).join(', ')}...)`, 'list them in "excludeFlows" so they stay out of the suite');

// Test data
add(c.seedCmd ? 'OK' : 'WARN', 'Seed step', c.seedCmd ? 'seedCmd set: fixtures reset every run' : 'no seedCmd', 'add a seed script that recreates test data and prints KEY=VALUE ids, so a deleted fixture never breaks a run');
const scriptLike = fs.existsSync(path.join(repo, '.maestro')) ? fs.readdirSync(path.join(repo, '.maestro')).filter((f) => /^run-.*\.sh$/.test(f)) : [];
const wired = new Set((c.scenarios || []).map((s) => (s.cmd.match(/run-[\w-]+\.sh/) || [])[0]).filter(Boolean));
const unwired = scriptLike.filter((f) => !wired.has(f) && f !== 'run-smoke.sh');
if (unwired.length) add('WARN', 'Scenario scripts', `${unwired.length} run-*.sh not in "scenarios": ${unwired.slice(0, 4).join(', ')}`, 'add them to "scenarios" with the flows each one runs, or their flows will fail for missing data');
for (const s of c.scenarios || []) {
  const file = (s.cmd.match(/[\w./-]+\.sh/) || [])[0];
  if (file && !fs.existsSync(path.join(repo, file))) add('FAIL', `Scenario ${s.name}`, `${file} missing`, 'fix the cmd path');
  for (const f of s.flows || []) if (!flows.includes(`${f}.yaml`)) add('WARN', `Scenario ${s.name}`, `flow ${f} not found`, 'remove it or add the flow');
}

// Credentials
const envPath = path.join(os.homedir(), '.qa-review', c.project || '_', '.env');
const envKeys = fs.existsSync(envPath) ? new Set(fs.readFileSync(envPath, 'utf8').split('\n').map((l) => l.split('=')[0]).filter(Boolean)) : new Set();
const missing = (c.envKeys || []).filter((k) => !envKeys.has(k));
add(missing.length ? 'FAIL' : 'OK', 'Credentials', missing.length ? `missing in ${envPath}: ${missing.join(', ')}` : 'all envKeys present', `fill ${envPath}`);

// Fixture gaps: a suite flow that uses ${VAR} with nothing providing it opens
// ".../undefined" and fails for the wrong reason. Provided = the local .env, a
// flow's own setup, a scenario that runs it, or the flow's own env: block.
{
  const scenarioFlows = new Set((c.scenarios || []).flatMap((s) => s.flows || []));
  const setupGlobs = Object.keys(c.flowSetup || {}).map((g) => new RegExp('^' + g.split('*').map((x) => x.replace(/[.+?^${}()|[\]\\]/g, '\\$&')).join('.*') + '$'));
  const excludedRe = (c.excludeFlows || []).map((g) => new RegExp('^' + g.split('*').map((x) => x.replace(/[.+?^${}()|[\]\\]/g, '\\$&')).join('.*') + '$'));
  const builtins = new Set(['MAESTRO_FILENAME', 'MAESTRO_DEVICE_UDID', 'MAESTRO_SHARD_ID', 'MAESTRO_SHARD_INDEX']);
  const gaps = [];
  for (const f of flows) {
    const name = f.replace(/\.yaml$/, '');
    if (excludedRe.some((r) => r.test(f)) || scenarioFlows.has(name) || setupGlobs.some((r) => r.test(f))) continue;
    const text = fs.readFileSync(path.join(flowsDir, f), 'utf8');
    const declared = new Set([...text.matchAll(/^\s{2,}([A-Z][A-Z0-9_]*):/gm)].map((m) => m[1]));
    const used = new Set([...text.matchAll(/\$\{([A-Z][A-Z0-9_]*)\}/g)].map((m) => m[1]));
    // runFlow partials: include the variables they use too.
    for (const m of text.matchAll(/runFlow:\s*(_[\w-]+\.yaml)/g)) {
      const pth = path.join(flowsDir, m[1]);
      if (fs.existsSync(pth)) for (const u of fs.readFileSync(pth, 'utf8').matchAll(/\$\{([A-Z][A-Z0-9_]*)\}/g)) used.add(u[1]);
    }
    const missingVars = [...used].filter((v) => !envKeys.has(v) && !declared.has(v) && !builtins.has(v));
    if (missingVars.length) gaps.push(`${name} (${missingVars.join(', ')})`);
  }
  if (gaps.length) add('WARN', 'Fixture gaps', `${gaps.length} flow(s) use values nothing provides: ${gaps.slice(0, 5).join('; ')}${gaps.length > 5 ? '; ...' : ''}`, 'have seedCmd print them as KEY=VALUE, add a flowSetup or scenario, or add them to the .env');
  else add('OK', 'Fixture gaps', 'every value a flow uses is provided');
}

// Analytics
const src = ['src', 'apps', 'app', 'lib'].map((d) => path.join(repo, d)).filter((d) => fs.existsSync(d));
let analytics = false;
let guarded = false;
for (const d of src) {
  try {
    const out = execSync(`grep -rlE "posthog|mixpanel|amplitude|segment|firebase/analytics|@react-native-firebase/analytics" "${d}" --include=*.ts --include=*.tsx --include=*.js 2>/dev/null | grep -v node_modules | head -20`, { encoding: 'utf8' });
    if (out.trim()) {
      analytics = true;
      // A switch anywhere in the source counts (it usually lives in the analytics module).
      const guard = execSync(`grep -rlE "isEmulator|isSimulator|navigator\\.webdriver" "${d}" --include=*.ts --include=*.tsx --include=*.js 2>/dev/null | grep -v node_modules | grep -iv test | head -1`, { encoding: 'utf8' });
      guarded = guarded || Boolean(guard.trim());
    }
  } catch {}
}
if (analytics) add(guarded ? 'OK' : 'WARN', 'Test traffic in analytics', guarded ? 'app skips analytics on a simulator/emulator' : 'the app uses product analytics and has no simulator/emulator switch', 'make the app skip analytics on a simulator or emulator, and have the backend skip test accounts, so regression runs never reach the team dashboard');

// Flattened tappable wrappers (React Native): a Touchable/Pressable that holds
// its own buttons becomes one iOS accessibility element, hiding the inner
// buttons from VoiceOver and from every UI-test selector.
if (c.platform !== 'web') {
  const TAGS = ['TouchableOpacity', 'Pressable', 'TouchableWithoutFeedback', 'TouchableHighlight', 'PressableScale'];
  const offenders = [];
  const walkTsx = (dir) => {
    for (const e of fs.readdirSync(dir, { withFileTypes: true })) {
      const full = path.join(dir, e.name);
      if (e.isDirectory()) { if (!['node_modules', '__mocks__', 'build', 'ios', 'android', '.git'].includes(e.name)) walkTsx(full); }
      else if (e.name.endsWith('.tsx') && !e.name.includes('.test.')) {
        const src = fs.readFileSync(full, 'utf8');
        const open = new RegExp(`<(${TAGS.join('|')})\\b`, 'g');
        let m;
        while ((m = open.exec(src))) {
          let depth = 0, end = -1;
          for (let i = m.index + m[0].length; i < src.length; i++) {
            const ch = src[i];
            if (ch === '{') depth++; else if (ch === '}') depth--; else if (ch === '>' && depth === 0) { end = i; break; }
          }
          if (end < 0) continue;
          const opening = src.slice(m.index, end + 1);
          if (opening.endsWith('/>') || /\baccessible\b/.test(opening) || !/\bonPress\b/.test(opening)) continue;
          const pair = new RegExp(`<(/?)${m[1]}\\b[^>]*?(/?)>`, 'gs');
          pair.lastIndex = end + 1;
          let level = 1, p2, body = '';
          while ((p2 = pair.exec(src))) { if (p2[1] === '/') level--; else if (p2[2] !== '/') level++; if (level === 0) { body = src.slice(end + 1, p2.index); break; } }
          if (/\b(onPress|onLongPress)=/.test(body)) offenders.push(`${path.relative(repo, full)}:${src.slice(0, m.index).split('\n').length}`);
        }
      }
    }
  };
  for (const d of src) walkTsx(d);
  if (offenders.length) add('WARN', 'Flattened tap targets', `${offenders.length} tappable wrapper(s) hold their own buttons: ${offenders.slice(0, 3).join(', ')}${offenders.length > 3 ? ', ...' : ''}`, 'add accessible={false} to each wrapper so VoiceOver and UI tests can reach the inner buttons');
  else add('OK', 'Flattened tap targets', 'no tappable wrapper hides its own buttons');
}

// Design rules
add(c.uiRules?.length || c.designDoc ? 'OK' : 'WARN', 'UI rules', c.uiRules?.length ? `${c.uiRules.length} rule(s)` : c.designDoc ? 'designDoc set' : 'none', 'add "designDoc" and a few "uiRules" so the UI pass checks the app\'s own rules');

report();

function report() {
  const w = Math.max(...rows.map((r) => r.check.length));
  for (const r of rows) console.log(`${r.level.padEnd(4)}  ${r.check.padEnd(w)}  ${r.detail}${r.level !== 'OK' && r.fix ? `\n      fix: ${r.fix}` : ''}`);
  const fails = rows.filter((r) => r.level === 'FAIL').length;
  const warns = rows.filter((r) => r.level === 'WARN').length;
  console.log(`\n${fails ? 'NOT READY' : 'READY'}: ${fails} fail, ${warns} warn`);
  process.exit(fails ? 1 : 0);
}
