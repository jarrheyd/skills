#!/usr/bin/env node
// scout report builder. Deterministic and dependency-free: pairs the manifest
// copy with the screenshots Maestro captured per step and the JUnit pass/fail,
// and emits ONE self-contained HTML page. Zero AI tokens per build.
//
// "Last reviewed" is persisted per journey in ~/.scout/<project>/.report-state.json
// and only bumped for journeys that actually ran this time, so a partial run
// leaves the others showing their older, honest date.
//
//   node build-report.mjs \
//     --project  <name>                      (resolves ~/.scout/<name>/ paths)
//     --manifest <journeys.manifest.json>
//     --config   <scout.config.json>         (platform: mobile|web, errorCopy...)
//     --debug    <maestro debug output dir>  (default: newest run under ~/.scout/<name>/runs)
//     --junit    <result.xml[,result2.xml]>  (pass/fail per flow; authoritative)
//     --out      <report.html>               (default: <run>/report.html)
//     --state    <.report-state.json>
//     --crosscheck <crosscheck.json>         (optional verdict-matrix section)
//     --gaps       <gaps.json>               (optional coverage-gap section)
//     --product    <product-notes.json>      (optional UX-findings section)
//     --build    "pre-deploy 2026-08-31"     (footer label)
//     --shots    6                           (max screenshots per journey)
//     --previous <older report.html>         (borrow reels for flows not captured)
import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import { execFileSync } from 'node:child_process';

const args = Object.fromEntries(
  process.argv.slice(2).reduce((a, v, i, arr) => (v.startsWith('--') ? [...a, [v.slice(2), arr[i + 1]]] : a), []),
);
const die = (m) => { console.error(`build-report: ${m}`); process.exit(1); };

const project = args.project || process.env.SCOUT_PROJECT;
const home = project ? path.join(os.homedir(), '.scout', project) : null;
if (!args.manifest) die('--manifest is required');
const manifest = JSON.parse(fs.readFileSync(args.manifest, 'utf8'));
const config = args.config && fs.existsSync(args.config) ? JSON.parse(fs.readFileSync(args.config, 'utf8')) : {};
const isWeb = (config.platform || 'mobile') === 'web';

// Resolve run directories, newest first. Tolerates flaky runs: a flow that
// failed in the latest run still shows its last good screenshots from an
// earlier retained run.
function runDirsUnder(dir) {
  if (!dir || !fs.existsSync(dir)) return [];
  // Newer Maestro writes per-flow output under <debug>/.maestro/tests/<ts>/;
  // treat each of those timestamp dirs as a run alongside the classic layout.
  const nested = path.join(dir, '.maestro', 'tests');
  if (fs.existsSync(nested)) {
    return fs.readdirSync(nested)
      .map((d) => path.join(nested, d))
      .filter((d) => { try { return fs.statSync(d).isDirectory(); } catch { return false; } })
      .sort((a, b) => fs.statSync(b).mtimeMs - fs.statSync(a).mtimeMs);
  }
  const kids = fs.readdirSync(dir).map((d) => path.join(dir, d)).filter((d) => {
    try { return fs.statSync(d).isDirectory(); } catch { return false; }
  });
  const looksLikeRun = kids.some((k) => fs.existsSync(path.join(k, 'takeScreenshot')) || fs.existsSync(path.join(k, 'screenshots')));
  const runs = looksLikeRun ? [dir] : kids;
  return runs.sort((a, b) => fs.statSync(b).mtimeMs - fs.statSync(a).mtimeMs);
}
// A scout run dir holds debug/ (Maestro debug output with per-flow subdirs).
function scoutRunDirs(base) {
  if (!base || !fs.existsSync(base)) return [];
  return fs.readdirSync(base)
    .map((d) => path.join(base, d))
    .filter((d) => { try { return fs.statSync(d).isDirectory(); } catch { return false; } })
    .sort((a, b) => fs.statSync(b).mtimeMs - fs.statSync(a).mtimeMs)
    .flatMap((run) => runDirsUnder(fs.existsSync(path.join(run, 'debug')) ? path.join(run, 'debug') : run));
}
const runDirs = args.debug ? runDirsUnder(args.debug) : (home ? scoutRunDirs(path.join(home, 'runs')) : []);
if (!runDirs.length) console.error('build-report: warning, no run directories found');

const statePath = args.state || (home ? path.join(home, '.report-state.json') : null);
const outPath = args.out || (runDirs[0] ? path.join(path.dirname(runDirs[0]), 'report.html') : 'report.html');
const maxShots = Number(args.shots || 6);
const buildLabel = args.build || 'local run';
const reviewedAt = args.now ? new Date(args.now) : new Date();

function junitStatus() {
  const map = {};
  for (const file of (args.junit || '').split(',').map((f) => f.trim()).filter(Boolean)) {
    if (!fs.existsSync(file)) continue;
    const xml = fs.readFileSync(file, 'utf8');
    for (const m of xml.matchAll(/<testcase\b[^>]*\bname="([^"]+)"[^>]*(\/>|>([\s\S]*?)<\/testcase>)/g)) {
      map[m[1].replace(/\.yaml$/, '')] = /<failure|<error/.test(m[3] || '') ? 'failed' : 'passed';
    }
  }
  return map;
}
const status = junitStatus();

// --previous: borrow reels from an older report for flows this run did not
// capture. Borrowed reels are labeled so they never read as fresh evidence.
const previousReels = (() => {
  const out = {};
  if (!args.previous || !fs.existsSync(args.previous)) return out;
  const html = fs.readFileSync(args.previous, 'utf8');
  for (const m of html.matchAll(/<article[^>]*data-flow="([^"]+)"[\s\S]*?<\/article>/g)) {
    const reel = m[0].match(/<div class="reel">([\s\S]*?)<\/div>\s*(?:<div class="(?:meta|foot)|<\/article>)/);
    if (!reel || /reel-empty/.test(m[0])) continue;
    out[m[1]] = reel[1];
  }
  return out;
})();

function shotsFor(flow, cap = maxShots) {
  // Prefer explicit takeScreenshot/ captures (the journey's real moments, in
  // order), searching runs newest-first. Fall back to Maestro auto-captures,
  // evenly sampled to the cap.
  for (const run of runDirs) {
    const named = path.join(run, flow, 'takeScreenshot');
    if (!fs.existsSync(named)) continue;
    const pngs = fs.readdirSync(named).filter((f) => f.toLowerCase().endsWith('.png')).sort();
    if (pngs.length) return pngs.slice(0, cap).map((f) => path.join(named, f));
  }
  for (const run of runDirs) {
    for (const dir of [path.join(run, flow, 'screenshots'), path.join(run, flow)]) {
      if (!fs.existsSync(dir)) continue;
      const pngs = fs.readdirSync(dir).filter((f) => f.toLowerCase().endsWith('.png')).sort();
      if (!pngs.length) continue;
      const pick = pngs.length <= cap ? pngs : Array.from({ length: cap }, (_, i) => pngs[Math.round((i * (pngs.length - 1)) / (cap - 1))]);
      return [...new Set(pick)].map((f) => path.join(dir, f));
    }
  }
  return [];
}
const ranThisRun = (flow) => Boolean(status[flow]) || shotsFor(flow).length > 0;

// The JUnit verdict is authoritative: a flow whose assertion failed is FAILED
// even if it captured screenshots before the failing step. Screenshots only
// decide status for flows with no JUnit entry.
let state = {};
if (statePath) { try { state = JSON.parse(fs.readFileSync(statePath, 'utf8')); } catch { state = {}; } }
const iso = reviewedAt.toISOString();
for (const j of manifest.journeys) {
  if (ranThisRun(j.flow)) state[j.flow] = { lastReviewed: iso, status: status[j.flow] || 'passed' };
}

// Screenshots are downscaled + recompressed to JPEG (macOS sips) before base64
// inlining so the page stays small. Frames render narrow, so ~1000px is
// retina-crisp at a fraction of raw PNG size. Falls back to the raw file when
// sips is missing (non-macOS).
const IMG_MAX_PX = Number(args.imgpx || 1000);
const IMG_QUALITY = Number(args.imgq || 86);
const b64 = (p) => {
  let buf;
  try {
    const tmp = `${p}.report.jpg`;
    execFileSync('sips', ['-Z', String(IMG_MAX_PX), '-s', 'format', 'jpeg', '-s', 'formatOptions', String(IMG_QUALITY), p, '--out', tmp], { stdio: 'ignore' });
    buf = fs.readFileSync(tmp);
    fs.unlinkSync(tmp);
  } catch {
    buf = fs.readFileSync(p);
  }
  const mime = buf[0] === 0xff && buf[1] === 0xd8 ? 'image/jpeg' : 'image/png';
  return `data:${mime};base64,${buf.toString('base64')}`;
};
const esc = (s) => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
const slug = (s) => String(s).toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
const fmtDate = (isoStr) => {
  if (!isoStr) return null;
  const d = new Date(isoStr);
  if (isNaN(d)) return null;
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric', timeZone: 'UTC' });
};

const categories = manifest.categories || [...new Set(manifest.journeys.map((j) => j.category || 'Journeys'))];
const frameClass = isWeb ? 'browser' : 'phone';
const figure = (src, alt) => isWeb
  ? `<figure class="browser"><span class="chrome"><i></i><i></i><i></i></span><span class="screen"><img loading="lazy" src="${src}" alt="${alt}" /></span></figure>`
  : `<figure class="phone"><span class="screen"><img loading="lazy" src="${src}" alt="${alt}" /></span></figure>`;

function journeyCard(j) {
  const planned = !!j.planned;
  const st = planned ? 'planned' : (state[j.flow]?.status || (status[j.flow] || (shotsFor(j.flow).length ? 'passed' : 'pending')));
  const reviewed = fmtDate(state[j.flow]?.lastReviewed);
  const shots = planned ? [] : shotsFor(j.flow, j.shots || maxShots);
  const borrowed = !planned && !shots.length && previousReels[j.flow];
  const film = shots.length
    ? `<div class="reel">${shots.map((s) => figure(b64(s), esc(j.q))).join('')}</div>`
    : borrowed
      ? `<div class="reel-note">Not captured in this run. Showing the previous run.</div><div class="reel">${borrowed}</div>`
      : `<div class="reel-empty">${planned ? 'Planned. The flow for this is not built yet.' : 'Not captured in this run.'}</div>`;
  const chip = planned
    ? `<span class="stamp planned"><span class="dot"></span>Planned</span>`
    : (reviewed
        ? `<span class="stamp ${st === 'failed' ? 'warn' : 'ok'}"><span class="dot"></span>${st === 'failed' ? 'Needs a look' : 'Verified'} ${esc(reviewed)}</span>`
        : `<span class="stamp pending"><span class="dot"></span>Not run yet</span>`);
  return `<article class="qa${st === 'failed' ? ' off' : ''}${planned ? ' planned' : ''}" data-flow="${esc(j.flow)}">
      <h3>${esc(j.q)}</h3>
      <p>${esc(j.a)}</p>
      ${film}
      <div class="foot">${chip}</div>
    </article>`;
}

// Optional sidecar sections written by the modes as plain JSON.
const readJson = (p) => (p && fs.existsSync(p) ? JSON.parse(fs.readFileSync(p, 'utf8')) : null);
const crosscheck = readJson(args.crosscheck);
const gaps = readJson(args.gaps);
const product = readJson(args.product);

const VERDICT = {
  PASS: 'v-pass', FAIL: 'v-fail', 'SCRIPT WRONG': 'v-script', 'NOT WIRED': 'v-wire', BLOCKED: 'v-block',
};
function crosscheckSection() {
  if (!crosscheck || !crosscheck.cases?.length) return '';
  const rows = crosscheck.cases.map((c) => `<tr class="${VERDICT[c.verdict] || ''}">
      <td>${esc(c.id)}</td><td>${esc(c.title || '')}</td>
      <td><span class="verdict ${VERDICT[c.verdict] || ''}">${esc(c.verdict)}</span></td>
      <td>${esc(c.note || '')}</td></tr>`).join('');
  const counts = {};
  for (const c of crosscheck.cases) counts[c.verdict] = (counts[c.verdict] || 0) + 1;
  const tally = Object.entries(counts).map(([v, n]) => `${n} ${v.toLowerCase()}`).join(' · ');
  return `<section class="extra"><h2>Test-script crosscheck</h2>
    <p class="sub">${esc(crosscheck.source || '')} · ${tally}</p>
    <div class="tablewrap"><table><thead><tr><th>Case</th><th>Title</th><th>Verdict</th><th>Note</th></tr></thead>
    <tbody>${rows}</tbody></table></div>
    ${crosscheck.scriptReview ? `<h3>Script review</h3><ul>${crosscheck.scriptReview.map((f) => `<li>${esc(f)}</li>`).join('')}</ul>` : ''}
  </section>`;
}
function gapsSection() {
  if (!gaps || !gaps.items?.length) return '';
  return `<section class="extra"><h2>Coverage gaps</h2>
    <p class="sub">Screens or branches in the code with no flow yet. Approve any of these to grow the manifest.</p>
    <ul>${gaps.items.map((g) => `<li><b>${esc(g.area)}</b> (${esc(g.kind || 'happy')}): ${esc(g.note)}</li>`).join('')}</ul>
  </section>`;
}
function productSection() {
  if (!product || !product.findings?.length) return '';
  return `<section class="extra"><h2>Product notes</h2>
    <p class="sub">UX findings from the product pass, one screenshot per screen.</p>
    ${product.findings.map((f) => `<article class="qa"><h3>${esc(f.screen)}</h3><p>${esc(f.finding)}${f.fix ? ` Suggested fix: ${esc(f.fix)}` : ''}</p>${f.shot && fs.existsSync(f.shot) ? `<div class="reel">${figure(b64(f.shot), esc(f.screen))}</div>` : ''}</article>`).join('')}
  </section>`;
}

const tabs = [{ id: 'all', label: 'All' }, ...categories.map((c) => ({ id: slug(c), label: c }))];
const tabInputs = tabs.map((t, i) => `<input type="radio" name="tab" id="tab-${t.id}" class="tabctl"${i === 0 ? ' checked' : ''}>`).join('');
const tabNav = `<nav class="tabs" role="tablist">${tabs.map((t) => `<label for="tab-${t.id}" class="tab" data-tab="${t.id}">${esc(t.label)}</label>`).join('')}</nav>`;
const tabCss = tabs
  .filter((t) => t.id !== 'all')
  .map((t) => `#tab-${t.id}:checked~main .cat{display:none}#tab-${t.id}:checked~main .cat[data-cat="${t.id}"]{display:block}`)
  .join('') + tabs.map((t) => `#tab-${t.id}:checked~.tabs label[for="tab-${t.id}"]{color:var(--ink);border-color:var(--accent)}`).join('');

const sections = categories.map((c) => {
  const items = manifest.journeys.filter((j) => (j.category || 'Journeys') === c);
  if (!items.length) return '';
  return `<section class="cat" data-cat="${slug(c)}">
      <h2 class="cat-title">${esc(c)}</h2>
      ${items.map(journeyCard).join('\n')}
    </section>`;
}).join('\n');

const builtJourneys = manifest.journeys.filter((j) => !j.planned);
const plannedCount = manifest.journeys.length - builtJourneys.length;
const reviewedFlows = builtJourneys.filter((j) => ranThisRun(j.flow));
const failedCount = reviewedFlows.filter((j) => (state[j.flow]?.status) === 'failed').length;
const verifiedCount = reviewedFlows.length - failedCount;
const greenlight = failedCount === 0 && reviewedFlows.length === builtJourneys.length;

const title = manifest.title || `${config.project || project || 'App'} flows`;
const html = `<!doctype html>
<html lang="en"><head>
<meta charset="utf-8" /><meta name="viewport" content="width=device-width, initial-scale=1" />
<title>${esc(title)}</title>
<style>
  :root{
    --ground:#FCFCFB; --raise:#F6F5F2; --ink:#2E2B27; --soft:#6E675F; --faint:#A79E94;
    --accent:#1E6B4F; --wash:#EAF2EE; --line:#E7E2DA; --ok:#1E6B4F; --bad:#A4452C;
  }
  *{box-sizing:border-box}
  html{-webkit-text-size-adjust:100%}
  body{margin:0;background:var(--ground);color:var(--ink);
    font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;
    line-height:1.55;font-size:17px;-webkit-font-smoothing:antialiased}
  .page{max-width:720px;margin:0 auto;padding:56px 24px 96px}
  header h1{font-size:32px;font-weight:700;letter-spacing:-0.02em;margin:0 0 10px}
  .intro{color:var(--soft);font-size:17px;margin:0;max-width:48ch}
  .meta{margin-top:18px;font-size:14px;color:var(--soft)}
  .meta b{color:${greenlight ? 'var(--ok)' : 'var(--bad)'}}
  .search{position:relative;margin-top:26px}
  #q{width:100%;font-family:inherit;font-size:16px;color:var(--ink);background:var(--raise);
    border:1px solid var(--line);border-radius:12px;padding:12px 16px;outline:none}
  #q:focus{border-color:var(--accent)}
  .tabctl{position:absolute;opacity:0;pointer-events:none}
  .tabs{display:flex;flex-wrap:wrap;gap:8px;margin:16px 0 4px}
  body.searching .tabs{display:none}
  body.searching .cat{display:block!important}
  body.searching .cat-title{display:none}
  .qa[hidden]{display:none!important}
  .cat[data-empty]{display:none!important}
  .nomatch{color:var(--soft);font-size:16px;font-style:italic;margin:40px 0;text-align:center}
  .tab{font-size:14px;font-weight:600;color:var(--soft);cursor:pointer;user-select:none;
    padding:7px 14px;border-radius:999px;border:1px solid var(--line);background:var(--raise)}
  .tab:hover{color:var(--ink)}
  ${tabCss}
  .cat{display:block}
  .cat-title{font-size:15px;font-weight:700;color:var(--faint);margin:38px 0 0}
  .qa{padding:30px 0;border-top:1px solid var(--line)}
  .cat-title + .qa{border-top:0}
  .qa h3{font-size:21px;font-weight:700;letter-spacing:-0.01em;margin:0}
  .qa p{margin:8px 0 18px;color:var(--soft);font-size:16px;max-width:60ch}
  .qa.off h3{color:var(--bad)}
  .reel{display:flex;gap:16px;overflow-x:auto;padding:2px 2px 8px;scroll-snap-type:x proximity;
    -webkit-overflow-scrolling:touch;scrollbar-width:thin;scrollbar-color:var(--line) transparent}
  .phone{flex:none;margin:0;width:190px;padding:7px;scroll-snap-align:start;
    border-radius:32px;background:#211d19;border:1px solid #3a342e}
  .phone .screen{display:block;overflow:hidden;border-radius:25px;background:#fff;aspect-ratio:393/760}
  .phone img{width:100%;height:100%;display:block;object-fit:cover;object-position:center 54%}
  .browser{flex:none;margin:0;width:420px;scroll-snap-align:start;border:1px solid var(--line);
    border-radius:10px;overflow:hidden;background:var(--raise)}
  .browser .chrome{display:flex;gap:5px;padding:8px 10px;border-bottom:1px solid var(--line)}
  .browser .chrome i{width:9px;height:9px;border-radius:50%;background:var(--line)}
  .browser .screen{display:block;background:#fff;aspect-ratio:16/10}
  .browser img{width:100%;height:100%;display:block;object-fit:cover;object-position:top}
  .reel-note{color:var(--faint);font-size:13px;font-style:italic;padding:10px 0 0}
  .reel-empty{color:var(--faint);font-size:15px;font-style:italic;padding:20px;
    border:1px dashed var(--line);border-radius:14px;background:var(--raise)}
  .foot{margin-top:14px}
  .stamp{display:inline-flex;align-items:center;gap:7px;font-size:13px;color:var(--faint)}
  .stamp .dot{width:7px;height:7px;border-radius:50%;flex:none}
  .stamp.ok .dot{background:var(--ok)}
  .stamp.warn{color:var(--bad)}
  .stamp.warn .dot{background:var(--bad)}
  .stamp.planned,.stamp.pending{color:var(--faint)}
  .stamp.planned .dot,.stamp.pending .dot{background:var(--line)}
  .qa.planned{opacity:0.72}
  .qa.planned h3{color:var(--faint)}
  .extra{margin-top:48px;padding-top:8px;border-top:1px solid var(--line)}
  .extra h2{font-size:24px;letter-spacing:-0.01em;margin:24px 0 4px}
  .extra .sub{color:var(--soft);margin:0 0 16px}
  .tablewrap{overflow-x:auto}
  table{border-collapse:collapse;width:100%;font-size:15px}
  th,td{text-align:left;padding:9px 12px;border-bottom:1px solid var(--line);vertical-align:top}
  th{color:var(--faint);font-weight:600}
  .verdict{font-weight:700;font-size:13px;padding:2px 9px;border-radius:999px;white-space:nowrap}
  .v-pass .verdict,.verdict.v-pass{color:var(--ok);background:var(--wash)}
  .verdict.v-fail{color:#fff;background:var(--bad)}
  .verdict.v-script{color:#7A5A12;background:#F5ECD6}
  .verdict.v-wire{color:#4A4A6A;background:#E9E9F2}
  .verdict.v-block{color:var(--soft);background:var(--raise)}
  footer{margin-top:56px;padding-top:24px;border-top:1px solid var(--line);color:var(--faint);font-size:13.5px}
  @media (max-width:520px){.page{padding:44px 18px 72px}header h1{font-size:26px}.phone{width:150px}.browser{width:300px}}
</style></head><body>
<div class="page">
  <header>
    <h1>${esc(title)}</h1>
    ${manifest.intro ? `<p class="intro">${esc(manifest.intro)}</p>` : ''}
    <div class="meta">${esc(buildLabel)} · <b>${greenlight ? 'all journeys green' : `${failedCount} need${failedCount === 1 ? 's' : ''} a look`}</b> · ${verifiedCount} verified${plannedCount ? ` · ${plannedCount} planned` : ''}</div>
  </header>
  <div class="search">
    <input id="q" type="search" placeholder="Search flows" aria-label="Search flows" autocomplete="off" />
  </div>
  ${tabInputs}
  ${tabNav}
  <main>
    ${sections}
    <p class="nomatch" hidden>No flows match that.</p>
    ${crosscheckSection()}
    ${gapsSection()}
    ${productSection()}
  </main>
  <footer>Built by scout. Each "last reviewed" date is the real day that journey last ran; screenshots are captured by the flows themselves.</footer>
</div>
<script>
(function () {
  var q = document.getElementById('q');
  var body = document.body;
  var cards = Array.prototype.slice.call(document.querySelectorAll('.qa'));
  var cats = Array.prototype.slice.call(document.querySelectorAll('.cat'));
  var nomatch = document.querySelector('.nomatch');
  cards.forEach(function (c) { c._t = (c.textContent || '').toLowerCase(); });
  function apply() {
    var term = (q.value || '').trim().toLowerCase();
    if (!term) {
      body.classList.remove('searching');
      cards.forEach(function (c) { c.hidden = false; });
      cats.forEach(function (c) { c.removeAttribute('data-empty'); });
      if (nomatch) nomatch.hidden = true;
      return;
    }
    body.classList.add('searching');
    var shown = 0;
    cards.forEach(function (c) {
      var hit = c._t.indexOf(term) !== -1;
      c.hidden = !hit;
      if (hit) shown++;
    });
    cats.forEach(function (c) {
      var any = c.querySelector('.qa:not([hidden])');
      if (any) c.removeAttribute('data-empty'); else c.setAttribute('data-empty', '');
    });
    if (nomatch) nomatch.hidden = shown !== 0;
  }
  q.addEventListener('input', apply);
})();
</script>
</body></html>`;

fs.mkdirSync(path.dirname(outPath), { recursive: true });
fs.writeFileSync(outPath, html);
if (statePath) fs.writeFileSync(statePath, JSON.stringify(state, null, 2) + '\n');
console.log(`Wrote ${outPath} (${(html.length / 1024 / 1024).toFixed(1)} MB) · reviewed ${reviewedFlows.length}/${manifest.journeys.length} this run · ${failedCount} failing`);
