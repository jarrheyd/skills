#!/usr/bin/env python3
"""Read a Google Slides deck or Google Doc back and run the deslop checks on every line in it.

  doc_audit.py <presentation or document id or URL> [--out FILE]

Why (2026-11-02): pushes over REST were gated only on "some deslop pass in the last 45 minutes",
on any file. Lines already in the deck, and lines typed straight into a batchUpdate, were never
read. This reads the live file, so what he opens is what gets checked.

Adds checks that only make sense across a whole deck:
- the "Label: subtitle" headline formula on three or more slides
- the same sentence opener on three or more lines
Writes a stamp {"at", "file": id, "clean"} to ~/.claude/deslop-stamps.jsonl.
Exit 0 clean, 2 slop found, 1 could not read.
"""
import json
import os
import re
import subprocess
import sys
import time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "hooks"))
import copy_slop_hook as H  # noqa: E402

STAMPS = os.path.expanduser("~/.claude/deslop-stamps.jsonl")


def token():
    return subprocess.run(["gcloud", "auth", "application-default", "print-access-token"],
                          capture_output=True, text=True).stdout.strip()


def get(url, tok):
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {tok}"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read())


def runs(el):
    out = []
    for t in (el.get("shape", {}).get("text", {}) or {}).get("textElements", []):
        if "textRun" in t:
            out.append(t["textRun"]["content"])
    for c in el.get("elementGroup", {}).get("children", []):
        out.extend(runs(c))
    for row in el.get("table", {}).get("tableRows", []):
        for cell in row.get("tableCells", []):
            for t in (cell.get("text", {}) or {}).get("textElements", []):
                if "textRun" in t:
                    out.append(t["textRun"]["content"])
            out.append("\n")
    return out


def slides_text(fid, tok):
    p = get(f"https://slides.googleapis.com/v1/presentations/{fid}", tok)
    pages = []
    for i, s in enumerate(p.get("slides", []), 1):
        els = sorted(s.get("pageElements", []), key=lambda e: (e.get("transform", {}).get("translateY", 0), e.get("transform", {}).get("translateX", 0)))
        lines = []
        for e in els:
            t = "".join(runs(e)).strip()
            if t:
                lines.extend(l.strip() for l in t.split("\n") if l.strip())
        notes = s.get("slideProperties", {}).get("notesPage", {}).get("pageElements", [])
        nt = "".join("".join(runs(e)) for e in notes).strip()
        pages.append((i, lines, nt))
    return p.get("title", ""), pages


def doc_text(fid, tok):
    d = get(f"https://docs.googleapis.com/v1/documents/{fid}", tok)
    lines = []
    for b in d.get("body", {}).get("content", []):
        para = b.get("paragraph")
        if para:
            t = "".join(e.get("textRun", {}).get("content", "") for e in para.get("elements", [])).strip()
            if t:
                lines.append(t)
    return d.get("title", ""), [(1, lines, "")]


def main(argv):
    if not argv:
        print(__doc__)
        return 1
    m = re.search(r"/(presentation|document)/d/([\w-]+)", argv[0])
    kind, fid = (m.group(1), m.group(2)) if m else (None, argv[0])
    tok = token()
    try:
        if kind == "document":
            title, pages = doc_text(fid, tok)
        else:
            try:
                title, pages = slides_text(fid, tok)
            except Exception:
                title, pages = doc_text(fid, tok)
    except Exception as e:
        print(f"could not read {fid}: {e}", file=sys.stderr)
        return 1
    hits = []
    alltext = []
    for i, lines, notes in pages:
        body = "\n".join(lines)
        alltext.append(body)
        for ln, msg in H.run_send_checks(body, "prose") + H.check_interface_narration(body):
            hits.append((i, msg))
        if notes:
            for ln, msg in H.run_send_checks(notes, "prose"):
                hits.append((i, "speaker notes: " + msg))
    heads = [(i, l[0]) for i, l, _ in pages if l]
    colon = [(i, h) for i, h in heads if re.match(r"^[^:]{2,40}: \S", h)]
    if len(colon) >= 3:
        hits.append((0, f"'Label: subtitle' headline on {len(colon)} slides ({', '.join(str(i) for i, _ in colon)}): write each headline as one plain sentence"))
    openers = {}
    for i, lines, _ in pages:
        for l in lines:
            w = " ".join(l.split()[:2]).lower()
            if len(l.split()) > 3:
                openers.setdefault(w, []).append(i)
    for w, where in openers.items():
        if len(where) >= 3:
            hits.append((0, f"{len(where)} lines open with '{w}' (slides {sorted(set(where))})"))
    out = argv[argv.index("--out") + 1] if "--out" in argv else None
    if out:
        with open(out, "w") as f:
            for i, lines, notes in pages:
                f.write(f"## {i}\n" + "\n".join(lines) + ("\n[notes] " + notes if notes else "") + "\n\n")
    with open(STAMPS, "a") as f:
        f.write(json.dumps({"at": time.time(), "file": fid, "clean": not hits, "tool": "doc_audit"}) + "\n")
    print(f"{title}: {len(pages)} page(s), {len(hits)} finding(s)")
    for i, msg in hits:
        print(f"  slide {i}: {msg}" if i else f"  deck: {msg}")
    return 2 if hits else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
