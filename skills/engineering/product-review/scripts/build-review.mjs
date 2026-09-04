#!/usr/bin/env node
// product-review report builder. Renders review.json into one self-contained
// HTML page: the overall call, then each expectation with its verdict and its
// expected/actual pictures side by side. Deterministic, dependency-free, zero
// AI tokens per build.
//
//   node build-review.mjs --review <dir>/review.json [--out <dir>/report.html]
import fs from 'node:fs';
import path from 'node:path';
import { execFileSync } from 'node:child_process';

const args = Object.fromEntries(
  process.argv.slice(2).reduce((a, v, i, arr) => (v.startsWith('--') ? [...a, [v.slice(2), arr[i + 1]]] : a), []),
);
if (!args.review || !fs.existsSync(args.review)) { console.error('build-review: --review <review.json> required'); process.exit(1); }
let review;
try { review = JSON.parse(fs.readFileSync(args.review, 'utf8')); } catch (e) { console.error(`build-review: ${args.review} is not valid JSON (${e.message})`); process.exit(1); }

// Validate the shape phases/verdict.md promises. A wrong file must fail loudly,
// never render as a quiet "aligned" or "needs a conversation".
const VERDICTS = ['MATCHES', 'DRIFTED', 'MISSING', 'EXTRA', "CAN'T TELL"];
const OVERALLS = ['ALIGNED', 'NEEDS A CONVERSATION'];
const problems = [];
if (!OVERALLS.includes(review.overall)) problems.push(`overall must be one of ${OVERALLS.join(' | ')}, got ${JSON.stringify(review.overall)}`);
if (!Array.isArray(review.items)) problems.push('items must be an array');
else review.items.forEach((it, i) => {
  if (!it || typeof it !== 'object') { problems.push(`items[${i}] is not an object`); return; }
  if (!it.expectation) problems.push(`items[${i}] has no expectation`);
  if (!VERDICTS.includes(it.verdict)) problems.push(`items[${i}] verdict must be one of ${VERDICTS.join(' | ')}, got ${JSON.stringify(it.verdict)}`);
  if (it.verdict !== 'MATCHES' && it.verdict !== 'EXTRA' && !it.note) problems.push(`items[${i}] (${it.verdict}) needs a note`);
  if (['MATCHES', 'DRIFTED', 'MISSING'].includes(it.verdict) && !it.actual && !it.code) problems.push(`items[${i}] (${it.verdict}) cites no evidence: set actual (screenshot) or code (file:line)`);
});
for (const k of ['extras', 'bounds']) if (review[k] != null && !Array.isArray(review[k])) problems.push(`${k} must be an array of strings`);
if (problems.length) { console.error(`build-review: ${args.review} is not a valid review:\n  - ${problems.join('\n  - ')}`); process.exit(1); }
const baseDir = path.dirname(path.resolve(args.review));
const outPath = args.out || path.join(baseDir, 'report.html');

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
const esc = (s) => String(s ?? '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
const resolveShot = (p) => {
  if (!p) return null;
  const abs = path.isAbsolute(p) ? p : path.join(baseDir, p);
  return fs.existsSync(abs) ? abs : null;
};

const V = {
  'MATCHES': 'v-match', 'DRIFTED': 'v-drift', 'MISSING': 'v-miss', 'EXTRA': 'v-extra', "CAN'T TELL": 'v-cant',
};
const counts = {};
for (const it of review.items || []) counts[it.verdict] = (counts[it.verdict] || 0) + 1;
const tally = Object.entries(counts).map(([v, n]) => `${n} ${v.toLowerCase()}`).join(', ');
const aligned = review.overall === 'ALIGNED';

function pair(it) {
  const exp = resolveShot(it.expected);
  const act = resolveShot(it.actual);
  if (!exp && !act) return '';
  const fig = (src, label) => src
    ? `<figure class="shot"><figcaption>${label}</figcaption><img loading="lazy" src="${b64(src)}" alt="${esc(it.expectation)} (${label})" /></figure>`
    : '';
  return `<div class="pair">${fig(exp, 'Expected')}${fig(act, 'What was built')}</div>`;
}

function itemCard(it) {
  return `<article class="item ${V[it.verdict] || ''}">
    <div class="head"><span class="n">${esc(it.n)}</span>
      <h3>${esc(it.expectation)}</h3>
      <span class="verdict ${V[it.verdict] || ''}">${esc(it.verdict)}</span></div>
    ${it.note ? `<p>${esc(it.note)}${it.code ? ` <span class="code">(${esc(it.code)})</span>` : ''}</p>` : (it.code ? `<p><span class="code">(${esc(it.code)})</span></p>` : '')}
    ${pair(it)}
  </article>`;
}

const agenda = (review.items || []).filter((i) => ['DRIFTED', 'MISSING'].includes(i.verdict));
const html = `<!doctype html>
<html lang="en"><head>
<meta charset="utf-8" /><meta name="viewport" content="width=device-width, initial-scale=1" />
<title>${esc(review.feature || 'Product review')}</title>
<style>
  :root{--ground:#FCFCFB;--raise:#F6F5F2;--ink:#2E2B27;--soft:#6E675F;--faint:#A79E94;
    --line:#E7E2DA;--ok:#1E6B4F;--okwash:#EAF2EE;--bad:#A4452C;--badwash:#F6E9E4;
    --amber:#7A5A12;--amberwash:#F5ECD6;--gray:#4A4A6A;--graywash:#E9E9F2}
  *{box-sizing:border-box}
  body{margin:0;background:var(--ground);color:var(--ink);
    font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;
    line-height:1.55;font-size:17px;-webkit-font-smoothing:antialiased}
  .page{max-width:760px;margin:0 auto;padding:56px 24px 96px}
  h1{font-size:30px;font-weight:700;letter-spacing:-0.02em;margin:0 0 6px}
  .target{color:var(--soft);font-size:15px;margin:0}
  .call{margin:22px 0 8px;font-weight:700;font-size:20px;color:${aligned ? 'var(--ok)' : 'var(--bad)'}}
  .tally{color:var(--soft);font-size:14px;margin:0 0 8px}
  .agenda{margin:10px 0 0;padding:0 0 0 22px;color:var(--ink)}
  .agenda li{margin:4px 0}
  .item{padding:26px 0;border-top:1px solid var(--line)}
  .item .head{display:flex;align-items:baseline;gap:12px}
  .item .n{color:var(--faint);font-weight:700;flex:none}
  .item h3{font-size:19px;font-weight:700;letter-spacing:-0.01em;margin:0;flex:1}
  .item p{margin:8px 0 14px;color:var(--soft);font-size:16px;max-width:64ch}
  .code{color:var(--faint);font-size:13px}
  .verdict{flex:none;font-weight:700;font-size:13px;white-space:nowrap}
  .verdict.v-match{color:var(--ok)}
  .verdict.v-drift{color:var(--amber)}
  .verdict.v-miss{color:var(--bad)}
  .verdict.v-extra{color:var(--gray)}
  .verdict.v-cant{color:var(--soft)}
  .pair{display:flex;gap:16px;overflow-x:auto;padding:2px 2px 8px}
  .shot{flex:none;margin:0;max-width:46%}
  .shot figcaption{font-size:12.5px;color:var(--faint);margin:0 0 6px}
  .shot img{max-width:100%;display:block;border:1px solid var(--line);border-radius:10px;background:#fff}
  .section{margin-top:44px;padding-top:12px;border-top:1px solid var(--line)}
  .section h2{font-size:22px;letter-spacing:-0.01em;margin:16px 0 8px}
  .section ul{margin:0;padding-left:22px;color:var(--soft)}
  @media (max-width:520px){.page{padding:44px 18px 72px}h1{font-size:25px}.shot{max-width:100%}}
</style></head><body>
<div class="page">
  <header>
    <h1>${esc(review.feature || 'Product review')}</h1>
    <p class="target">${esc(review.target || '')}</p>
    <div class="call">${aligned ? 'Aligned with what you expected' : 'Needs a conversation'}</div>
    <p class="tally">${tally}</p>
    ${!aligned && agenda.length ? `<ul class="agenda">${agenda.slice(0, 5).map((i) => `<li>${esc(i.expectation)}: ${esc(i.note || i.verdict.toLowerCase())}</li>`).join('')}</ul>` : ''}
  </header>
  <main>
    ${(review.items || []).map(itemCard).join('\n')}
    ${review.extras?.length ? `<section class="section"><h2>Also noticed (outside what we agreed to check)</h2><ul>${review.extras.map((e) => `<li>${esc(e)}</li>`).join('')}</ul></section>` : ''}
    ${review.bounds?.length ? `<section class="section"><h2>What this review could not see</h2><ul>${review.bounds.map((b) => `<li>${esc(b)}</li>`).join('')}</ul></section>` : ''}
  </main>
</div>
</body></html>`;

fs.mkdirSync(path.dirname(outPath), { recursive: true });
fs.writeFileSync(outPath, html);
console.log(`Wrote ${outPath} (${(html.length / 1024 / 1024).toFixed(1)} MB), ${review.items.length} expectations, ${review.overall}`);
