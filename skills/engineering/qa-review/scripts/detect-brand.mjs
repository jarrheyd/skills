#!/usr/bin/env node
// detect-brand.mjs — read a target app repo and emit a brand.json the report
// builder themes itself from: colors (+ light/dark dominance), fonts, logo, icon.
// Zero-dep, deterministic, best-effort. A miss falls back to a neutral palette so
// the proof always renders; it never throws on a repo it cannot read.
//
// Usage: node detect-brand.mjs --repo <path> [--project <name>] [--out <file>]
// Writes brand.json to --out, else ~/.qa-review/<project>/brand.json, and prints it.

import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';

const args = process.argv.slice(2);
const arg = (k) => { const i = args.indexOf(k); return i >= 0 ? args[i + 1] : undefined; };
const REPO = path.resolve(arg('--repo') || '.');
if (!fs.existsSync(REPO)) { console.error(`detect-brand: repo not found: ${REPO}`); process.exit(2); }

// ---- helpers ---------------------------------------------------------------
const read = (p) => { try { return fs.readFileSync(p, 'utf8'); } catch { return ''; } };
const exists = (p) => { try { return fs.existsSync(p); } catch { return false; } };

// Bounded recursive walk (skips heavy/vendored dirs) so detection stays fast.
const SKIP = new Set(['node_modules', '.git', 'ios', 'android', 'build', 'dist', '.next', 'Pods', 'vendor', '.expo', 'coverage']);
function walk(dir, hit, depth = 0, out = []) {
  if (depth > 6) return out;
  let ents = [];
  try { ents = fs.readdirSync(dir, { withFileTypes: true }); } catch { return out; }
  for (const e of ents) {
    const full = path.join(dir, e.name);
    if (e.isDirectory()) { if (!SKIP.has(e.name)) walk(full, hit, depth + 1, out); }
    else if (hit(e.name, full)) out.push(full);
  }
  return out;
}
const firstFile = (names) => { for (const n of names) { const p = path.join(REPO, n); if (exists(p)) return p; } return ''; };

const HEX = /#[0-9a-fA-F]{3,8}\b/;
const normHex = (h) => {
  if (!h) return h;
  h = h.trim();
  if (/^#[0-9a-fA-F]{3}$/.test(h)) return '#' + h.slice(1).split('').map((c) => c + c).join('').toUpperCase();
  return h.toUpperCase();
};
const rgb = (h) => { const m = /^#([0-9a-fA-F]{6})/.exec(h || ''); if (!m) return null; const n = parseInt(m[1], 16); return [(n >> 16) & 255, (n >> 8) & 255, n & 255]; };
// Perceived luminance 0..255 of a #RRGGBB.
const lum = (h) => { const c = rgb(h); return c ? 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2] : null; };
// Saturation-ish spread 0..255 (max channel minus min): high = a brand color, low = a neutral.
const sat = (h) => { const c = rgb(h); return c ? Math.max(...c) - Math.min(...c) : 0; };

// ---- colors ----------------------------------------------------------------
// Pull a flat name->hex map from tailwind/twrnc config or a design-tokens file.
// We do not eval JS; we scrape `key: '#hex'` and `key: { 500: '#hex' }` pairs.
function scrapeColors(src) {
  const out = {};
  if (!src) return out;
  // key: '#hex'  or  key: "#hex"
  for (const m of src.matchAll(/(['"]?[\w-]+['"]?)\s*:\s*['"](#[0-9a-fA-F]{3,8})['"]/g)) {
    const key = m[1].replace(/['"]/g, '');
    out[key.toLowerCase()] = normHex(m[2]);
  }
  return out;
}
// Nested scales: capture `family: { 500: '#..', 100: '#..' }` → family-500 etc.
function scrapeScales(src) {
  const out = {};
  if (!src) return out;
  for (const fam of src.matchAll(/['"]?([A-Za-z][\w-]*)['"]?\s*:\s*\{([^{}]*#[0-9a-fA-F]{3,8}[^{}]*)\}/g)) {
    const family = fam[1].toLowerCase();
    for (const step of fam[2].matchAll(/(['"]?\d{2,3}['"]?)\s*:\s*['"](#[0-9a-fA-F]{3,8})['"]/g)) {
      out[`${family}-${step[1].replace(/['"]/g, '')}`] = normHex(step[2]);
    }
    const def = /DEFAULT\s*:\s*['"](#[0-9a-fA-F]{3,8})['"]/.exec(fam[2]);
    if (def) out[family] = normHex(def[1]);
  }
  return out;
}

const colorSources = [
  firstFile(['apps/mobile/src/tailwind/index.ts', 'src/tailwind/index.ts']),
  firstFile(['apps/mobile/tailwind.config.js', 'tailwind.config.js', 'tailwind.config.ts']),
  firstFile(['apps/mobile/src/constants/design-tokens.ts', 'src/constants/design-tokens.ts']),
  firstFile(['apps/mobile/DESIGN.md', 'DESIGN.md', 'docs/DESIGN.md']),
].filter(Boolean);

let flat = {};
for (const f of colorSources) { const s = read(f); Object.assign(flat, scrapeScales(s), scrapeColors(s)); }

// Pick a hex for the first key whose name matches any pattern (and passes an
// optional value filter, e.g. must be saturated for a brand color).
const pick = (pats, ok = () => true) => {
  for (const p of pats) {
    for (const k of Object.keys(flat)) { if (p.test(k) && HEX.test(flat[k]) && ok(flat[k])) return flat[k]; }
  }
  return null;
};
const isBrand = (h) => sat(h) >= 40;                    // saturated enough to read as a brand hue
const isNeutral = (h) => sat(h) <= 24;                  // near-gray line/surface
const neutralByLum = (wantLight) => {
  const grays = Object.entries(flat).filter(([, v]) => /^#[0-9a-fA-F]{6}$/.test(v) && isNeutral(v));
  if (!grays.length) return null;
  grays.sort((a, b) => (lum(a[1]) - lum(b[1])) * (wantLight ? -1 : 1));
  return grays[0][1];
};
// Most-saturated color in the map, as a last resort for the primary.
const mostSaturated = () => {
  const cs = Object.values(flat).filter((v) => /^#[0-9a-fA-F]{6}$/.test(v));
  return cs.length ? cs.sort((a, b) => sat(b) - sat(a))[0] : null;
};

const FALLBACK = { bg: '#FCFCFB', surface: '#F6F5F2', ink: '#2E2B27', muted: '#6E675F', primary: '#1E6B4F', accent: '#1E6B4F', ok: '#1E6B4F', bad: '#A4452C', line: '#E7E2DA' };

const colors = {
  // Brand hues: name first, then require saturation so a light tint or border never wins.
  primary: pick([/^primary-?500$/, /^primary$/, /logogold/, /kapwaorange/, /^brand-?500?$/], isBrand)
    || pick([/gold|orange|amber|blue|indigo|green|purple|violet|pink|red/], isBrand)
    || mostSaturated() || FALLBACK.primary,
  accent: pick([/^accent-?500$/, /^teal-?500$/, /^secondary-?500$/, /link/], isBrand) || null,
  ink: pick([/^ink$/, /^text$/, /^secondary-?500$/, /^textprimary/, /^foreground/, /^secondary-?900$/, /^neutral-?9\d\d$/, /-?900$/]) || neutralByLum(false) || FALLBACK.ink,
  muted: pick([/^muted$/, /^gray-?500$/, /^grey-?500$/, /^neutral-?5\d\d$/, /^soft$/]) || FALLBACK.muted,
  bg: pick([/^bg$/, /^background$/, /^cream-?500$/, /^cream-?100$/, /^surface-?0$/], (h) => lum(h) > 150) || neutralByLum(true) || FALLBACK.bg,
  surface: pick([/^surface-?100$/, /^card$/, /^cream-?100$/, /^raise$/], (h) => lum(h) > 150) || FALLBACK.surface,
  ok: pick([/^ok$/, /^success/, /^green-?500$/], isBrand) || FALLBACK.ok,
  bad: pick([/^bad$/, /^error/, /^danger/, /^red-?500$/], isBrand) || FALLBACK.bad,
  line: pick([/^line$/, /^border/, /^divider/, /-?100$/], isNeutral) || FALLBACK.line,
};
if (!colors.accent) colors.accent = colors.primary;

// ---- light / dark dominance ------------------------------------------------
function detectMode() {
  const plist = firstFile(['apps/mobile/ios/*/Info.plist']);
  // glob the Info.plist(s) since the app dir name varies.
  const plists = walk(REPO, (n) => n === 'Info.plist').slice(0, 6);
  for (const p of plists) {
    const s = read(p);
    const m = /<key>UIUserInterfaceStyle<\/key>\s*<string>(\w+)<\/string>/.exec(s);
    if (m) return m[1].toLowerCase() === 'dark' ? 'dark' : 'light';
  }
  const appJson = read(firstFile(['apps/mobile/app.json', 'app.json', 'app.config.js']));
  const uis = /"userInterfaceStyle"\s*:\s*"(\w+)"/.exec(appJson);
  if (uis) return uis[1].toLowerCase() === 'dark' ? 'dark' : (uis[1].toLowerCase() === 'automatic' ? 'auto' : 'light');
  const design = read(firstFile(['apps/mobile/DESIGN.md', 'DESIGN.md']));
  if (/no dark (palette|mode)|light[- ]only|locked to the light/i.test(design)) return 'light';
  // Fall back to the bg luminance: a light bg means a light app.
  const bl = lum(colors.bg);
  return bl == null ? 'light' : (bl < 110 ? 'dark' : 'light');
}
const mode = detectMode();

// ---- fonts -----------------------------------------------------------------
function detectFonts() {
  const files = walk(REPO, (n) => /\.(ttf|otf|woff2?)$/i.test(n)).filter((p) => /fonts?\//i.test(p));
  // family name = file basename up to the first weight/style token.
  const fam = (p) => path.basename(p).replace(/\.(ttf|otf|woff2?)$/i, '').replace(/[-_ ]?(regular|bold|semibold|medium|light|extralight|extrabold|italic|thin|demo|black|book|text).*$/i, '').replace(/[-_ ]/g, '') || path.basename(p);
  const families = [...new Set(files.map(fam))];
  // Try tailwind fontFamily mapping for role hints (sans / heading / accent).
  const tw = ['apps/mobile/src/tailwind/index.ts', 'src/tailwind/index.ts', 'apps/mobile/tailwind.config.js', 'tailwind.config.js', 'apps/mobile/src/constants/design-tokens.ts']
    .map((f) => read(firstFile([f]))).join('\n');
  const clean = (s) => s.replace(/[-_ ]?(regular|bold|semibold|medium|light|extralight|extrabold|italic|thin|demo|black|book|text)\b.*$/i, '').replace(/[-_ ]/g, '') || s;
  // A role's value may be a bare string OR a ternary (`IS_ANDROID ? 'X' : 'Y'`),
  // so grab the first quoted font token within a short window after `role:`.
  const roleFont = (role) => {
    const re = new RegExp(`['"]?\\b${role}\\b['"]?\\s*:\\s*([^,}\\n]{0,120})`, 'i');
    const m = re.exec(tw); if (!m) return null;
    const q = /['"]([A-Za-z][\w .-]+?)['"]/.exec(m[1]);
    return q ? clean(q[1]) : null;
  };
  const sans = roleFont('sans') || roleFont('body') || (families[0] && clean(families[0])) || null;
  const heading = roleFont('degular') || roleFont('heading') || roleFont('display') || sans;
  const accent = roleFont('mansalva') || roleFont('accent') || roleFont('hand') || heading;
  return { sans, heading, accent, files: files.slice(0, 24) };
}
const fonts = detectFonts();

// ---- logo / icon -----------------------------------------------------------
const logo = (walk(REPO, (n) => /logo/i.test(n) && /\.(svg|png)$/i.test(n)).sort((a, b) => a.length - b.length)[0]) || '';
const icon = (walk(REPO, (n, f) => /AppIcon\.appiconset/.test(f) && /\.png$/i.test(n)).sort((a, b) => b.length - a.length)[0]) || '';

// ---- app name --------------------------------------------------------------
const appJson = read(firstFile(['apps/mobile/app.json', 'app.json']));
const nameM = /"(?:name|displayName)"\s*:\s*"([^"]+)"/.exec(appJson);
const appName = (arg('--project') && arg('--project')[0].toUpperCase() + arg('--project').slice(1)) || (nameM ? nameM[1] : path.basename(REPO));

// ---- emit ------------------------------------------------------------------
const project = arg('--project') || (nameM ? nameM[1].toLowerCase() : path.basename(REPO).toLowerCase());
const brand = {
  appName, project, mode, colors, fonts, logo, icon,
  detectedFrom: colorSources.map((f) => path.relative(REPO, f)),
  at: new Date().toISOString(),
};

const outPath = arg('--out') || path.join(os.homedir(), '.qa-review', project, 'brand.json');
fs.mkdirSync(path.dirname(outPath), { recursive: true });
fs.writeFileSync(outPath, JSON.stringify(brand, null, 2));
console.log(JSON.stringify(brand, null, 2));
console.error(`detect-brand: wrote ${outPath} (mode=${mode}, ${Object.keys(flat).length} colors scraped, ${fonts.files.length} font files, logo=${logo ? 'yes' : 'no'})`);
