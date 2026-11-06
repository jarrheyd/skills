#!/usr/bin/env python3
"""Read a Google Slides deck or Google Doc back and run the deslop checks on every line in it.

  doc_audit.py <presentation or document id or URL> [--out FILE] [--template-font]

Why (2026-11-02): pushes over REST were gated only on "some deslop pass in the last 45 minutes",
on any file. Lines already in the deck, and lines typed straight into a batchUpdate, were never
read. This reads the live file, so what the reader opens is what gets checked.

Adds checks that only make sense across a whole deck:
- the "Label: subtitle" headline formula on three or more slides
- the same sentence opener on three or more lines
- house rule only: Arial anywhere, the font a file gets when nobody chose one (author note 11-02).
  --template-font skips this for a template we fill in that really is set in Arial.
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
    return p.get("title", ""), pages, slide_fonts(p), set()


def slide_fonts(p):
    """Characters per font on the slides. The API reports the inherited font on each run."""
    fonts = {}

    def walk(el):
        boxes = [el.get("shape", {}).get("text") or {}]
        boxes += [c.get("text") or {} for row in el.get("table", {}).get("tableRows", []) for c in row.get("tableCells", [])]
        for box in boxes:
            for t in box.get("textElements", []):
                run = t.get("textRun")
                if run and run["content"].strip():
                    f = run.get("style", {}).get("fontFamily", "")
                    fonts[f] = fonts.get(f, 0) + len(run["content"].strip())
        for c in el.get("elementGroup", {}).get("children", []):
            walk(c)

    for s in p.get("slides", []):
        for e in s.get("pageElements", []):
            walk(e)
    return fonts


def doc_paragraphs(content, in_table=False):
    """Every paragraph in a doc body, table cells included, each with whether it sits in a table."""
    for b in content:
        if "paragraph" in b:
            yield b["paragraph"], in_table
        for row in b.get("table", {}).get("tableRows", []):
            for cell in row.get("tableCells", []):
                yield from doc_paragraphs(cell.get("content", []), True)


def doc_read(d):
    """Lines, characters per font, and the lines in tables. A run with no font of its own takes its paragraph style's."""
    named = {n.get("namedStyleType"): n.get("textStyle", {}).get("weightedFontFamily", {}).get("fontFamily", "")
             for n in d.get("namedStyles", {}).get("styles", [])}
    lines, fonts, cells = [], {}, set()
    for para, in_table in doc_paragraphs(d.get("body", {}).get("content", [])):
        base = named.get(para.get("paragraphStyle", {}).get("namedStyleType")) or named.get("NORMAL_TEXT", "")
        t = ""
        for e in para.get("elements", []):
            run = e.get("textRun")
            if not run:
                continue
            t += run.get("content", "")
            if run.get("content", "").strip():
                f = run.get("textStyle", {}).get("weightedFontFamily", {}).get("fontFamily") or base or "Arial"  # Docs' default
                fonts[f] = fonts.get(f, 0) + len(run["content"].strip())
        if t.strip():
            lines.append(t.strip())
            if in_table:
                cells.add(t.strip())
    return lines, fonts, cells


def rendered_arial(fid, tok):
    """True when the file's PDF export embeds Arial. Unknown (no pdffonts, export failed) counts as no."""
    import tempfile
    try:
        req = urllib.request.Request(f"https://www.googleapis.com/drive/v3/files/{fid}/export?mimeType=application/pdf",
                                     headers={"Authorization": f"Bearer {tok}"})
        with urllib.request.urlopen(req, timeout=90) as r, tempfile.NamedTemporaryFile(suffix=".pdf") as t:
            t.write(r.read())
            t.flush()
            return "arial" in subprocess.run(["pdffonts", t.name], capture_output=True, text=True).stdout.lower()
    except Exception:
        return False


def has_dots(d):
    """True when a list draws a symbol, not a number. A Drive HTML import shows its dots as
    GLYPH_TYPE_UNSPECIFIED with no glyphSymbol and no counter in glyphFormat (BnK 2SV guide, 11-03)."""
    for li in d.get("lists", {}).values():
        for n in li.get("listProperties", {}).get("nestingLevels", [])[:1]:
            if n.get("glyphSymbol") or "%" not in n.get("glyphFormat", ""):
                return True
    return False


def doc_text(fid, tok):
    d = get(f"https://docs.googleapis.com/v1/documents/{fid}", tok)
    lines, fonts, cells = doc_read(d)
    # List numbers keep their own font after a Drive HTML import, and the API does not show which one renders.
    # The PDF export does: count an embedded Arial as one finding character.
    # A bullet dot has no Google Sans glyph and always falls back to Arial, so a doc with bullets cannot be read this way.
    dots = has_dots(d)
    if not dots and not any(f.lower() == "arial" for f in fonts) and rendered_arial(fid, tok):
        fonts["Arial"] = 1
    return d.get("title", ""), [(1, lines, "")], fonts, cells


def font_hits(fonts):
    if not H.HOUSE:
        return []
    arial = sum(n for f, n in fonts.items() if f.lower() == "arial")
    if not arial:
        return []
    return [(0, f"{arial} of {sum(fonts.values())} characters in Arial: set Google Sans, or the client's font on a client file")]


def main(argv):
    if not argv:
        print(__doc__)
        return 1
    m = re.search(r"/(presentation|document)/d/([\w-]+)", argv[0])
    kind, fid = (m.group(1), m.group(2)) if m else (None, argv[0])
    tok = token()
    try:
        if kind == "document":
            title, pages, fonts, cells = doc_text(fid, tok)
        else:
            try:
                title, pages, fonts, cells = slides_text(fid, tok)
            except Exception:
                title, pages, fonts, cells = doc_text(fid, tok)
    except Exception as e:
        print(f"could not read {fid}: {e}", file=sys.stderr)
        return 1
    hits = [] if "--template-font" in argv else font_hits(fonts)
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
            if len(l.split()) > 3 and l not in cells:  # rows in a table repeat their opener on purpose
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
