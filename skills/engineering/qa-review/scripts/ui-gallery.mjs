#!/usr/bin/env node
// Collect every named screenshot a run took (takeScreenshot steps) into one
// review set for the UI and consistency pass: <run>/ui-review/NNN-<flow>--<name>.jpg,
// downscaled so an agent can look at every screen of a full regression cheaply,
// plus index.json [{ id, flow, name, file, source }]. Failure frames Maestro
// saves on its own are included too, marked kind "failure".
//
//   node ui-gallery.mjs --run <run dir> [--px 480] [--dupe 5]
//
// Near-identical screens (the same Home or login captured by many flows) are kept
// once: each screen gets a 64-bit difference hash from a 9x8 thumbnail (macOS
// sips, no extra dependencies), and a screen within --dupe bits of one already
// kept is listed as a duplicate instead of reviewed again. Failure frames are
// always kept. --dupe 0 keeps everything.
import fs from 'node:fs';
import path from 'node:path';
import { execFileSync } from 'node:child_process';

const args = Object.fromEntries(
  process.argv.slice(2).reduce((acc, cur, i, all) => (cur.startsWith('--') ? [...acc, [cur.slice(2), all[i + 1]]] : acc), []),
);
const run = args.run;
if (!run || !fs.existsSync(run)) {
  console.error('ui-gallery: --run <run dir> required');
  process.exit(1);
}
const px = String(args.px || 480);
const dupeBits = Number(args.dupe ?? 5);

// 64-bit difference hash: grayscale 9x8, compare each pixel with its right
// neighbour. Returns null when sips is unavailable (then nothing is deduped).
function dhash(file) {
  const tmp = `${file}.dhash.bmp`;
  try {
    execFileSync('sips', ['-s', 'format', 'bmp', '-z', '8', '9', file, '--out', tmp], { stdio: 'ignore' });
    const b = fs.readFileSync(tmp);
    const offset = b.readUInt32LE(10);
    const w = b.readInt32LE(18);
    const hRaw = b.readInt32LE(22);
    const bpp = b.readUInt16LE(28) / 8;
    const h = Math.abs(hRaw);
    const rowSize = Math.ceil((w * bpp) / 4) * 4;
    const gray = [];
    for (let y = 0; y < h; y++) {
      const row = hRaw < 0 ? y : h - 1 - y;
      for (let x = 0; x < w; x++) {
        const i = offset + row * rowSize + x * bpp;
        gray.push(0.299 * b[i + 2] + 0.587 * b[i + 1] + 0.114 * b[i]);
      }
    }
    let bits = '';
    for (let y = 0; y < h; y++) for (let x = 0; x < w - 1; x++) bits += gray[y * w + x] > gray[y * w + x + 1] ? '1' : '0';
    return bits;
  } catch {
    return null;
  } finally {
    fs.rmSync(tmp, { force: true });
  }
}
const hamming = (a, b) => {
  let d = 0;
  for (let i = 0; i < a.length; i++) if (a[i] !== b[i]) d++;
  return d;
};
const outDir = path.join(run, 'ui-review');
fs.rmSync(outDir, { recursive: true, force: true });
fs.mkdirSync(outDir, { recursive: true });

// Walk the debug tree for PNGs. Maestro lays them out as
// .../<flow>/takeScreenshot/<name>.png (named) and .../<flow>/screenshots/*.png (failure frames).
const found = [];
const walk = (dir) => {
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const p = path.join(dir, entry.name);
    if (entry.isDirectory()) walk(p);
    else if (entry.name.endsWith('.png') && !entry.name.endsWith('.report.jpg')) found.push(p);
  }
};
walk(run);

const seen = new Map();
for (const file of found.sort()) {
  const parts = file.split(path.sep);
  const bucket = parts[parts.length - 2];
  const kind = bucket === 'takeScreenshot' ? 'named' : bucket === 'screenshots' ? 'failure' : 'other';
  if (kind === 'other') continue;
  if (kind === 'failure' && !/assertCondition|FAILED|failed/i.test(path.basename(file))) continue;
  const flow = parts[parts.length - 3];
  const name = path.basename(file, '.png');
  // Latest attempt wins (a retried flow re-shoots the same names).
  seen.set(`${flow}::${name}`, { flow, name, kind, source: file });
}

const index = [];
const duplicates = [];
const kept = [];
let n = 0;
for (const item of seen.values()) {
  const hash = dupeBits > 0 ? dhash(item.source) : null;
  if (hash && item.kind !== 'failure') {
    const twin = kept.find((k) => k.hash && hamming(k.hash, hash) <= dupeBits);
    if (twin) {
      duplicates.push({ flow: item.flow, name: item.name, source: item.source, dupeOf: twin.id });
      continue;
    }
  }
  n += 1;
  const id = String(n).padStart(3, '0');
  const file = path.join(outDir, `${id}-${item.flow}--${item.name}.jpg`.replace(/[^\w.-]+/g, '_'));
  try {
    execFileSync('sips', ['-Z', px, '-s', 'format', 'jpeg', '-s', 'formatOptions', '70', item.source, '--out', file], { stdio: 'ignore' });
  } catch {
    fs.copyFileSync(item.source, file.replace(/\.jpg$/, '.png'));
  }
  index.push({ id, ...item, file });
  kept.push({ id, hash });
}
fs.writeFileSync(path.join(outDir, 'index.json'), JSON.stringify(index, null, 2));
fs.writeFileSync(path.join(outDir, 'duplicates.json'), JSON.stringify(duplicates, null, 2));
const flows = new Set(index.map((i) => i.flow)).size;
console.log(`ui-gallery: ${index.length} distinct screens from ${flows} flows (${duplicates.length} near-duplicates skipped) -> ${outDir}`);
