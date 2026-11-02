#!/usr/bin/env python3
"""deslop gate for documents made through Bash (2026-10-29).

The Write/Edit hooks never see a deck rendered by a script and pushed to Google Slides over
REST, a Doc filled by batchUpdate, a Drive upload, or a heredoc that writes a .md or .html.
A deck went out that way with slop on every slide. This PreToolUse hook on Bash:

1. Blocks a push to Google Docs, Slides or Drive (REST write, upload, batchUpdate, or a
   push*.py script) unless scripts/deslop_check.py passed in the last 45 minutes.
2. Runs the copy checks on any heredoc body the command writes to a prose file.
3. (2026-11-02) Reads the text inside a Slides or Docs batchUpdate (inline -d or -d @file:
   insertText, replaceAllText) and blocks it on any hit, one item at a time.
4. (2026-11-02) An edit to an existing deck or doc also needs doc_audit.py run on that same
   file id in the last 45 minutes. Before this, a pass on any other file let every push through,
   so lines already in the deck were never read. He found slop on both master plan decks.
Exit 0 allow, 2 block.
"""
import json
import os
import re
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

PUSH = re.compile(
    r"(?:(?:slides|docs)\.googleapis\.com/v1/(?:presentations|documents)/[^\s'\"]*:batchUpdate"
    r"|googleapis\.com/upload/drive"
    r"|(?:-X|--request)\s*(?:POST|PATCH|PUT)[^\n]*googleapis\.com/(?:drive|slides|docs)"
    r"|googleapis\.com/(?:drive|slides|docs)[^\n]*(?:-X|--request)\s*(?:POST|PATCH|PUT)"
    r"|\bpython3?\s+[^\s;&|]*push[\w-]*\.py\b"
    r"|\bnode\s+[^\s;&|]*push[\w-]*\.m?js\b)"
)
HEREDOC = re.compile(r"(?:cat|tee)\s*>{1,2}\s*['\"]?([^\s'\"<]+\.(?:md|mdx|txt|html?))['\"]?\s*<<-?\s*['\"]?(\w+)['\"]?\n(.*?)\n\2\b", re.S)
FRESH = 45 * 60
CHECK = "python3 ~/.claude/skills/deslop/scripts/deslop_check.py"


def recent_pass():
    try:
        lines = open(os.path.expanduser("~/.claude/deslop-stamps.jsonl")).read().splitlines()[-50:]
    except OSError:
        return False
    now = time.time()
    for l in reversed(lines):
        try:
            if now - json.loads(l)["at"] < FRESH:
                return True
        except (ValueError, KeyError):
            continue
    return False


FILE_ID = re.compile(r"(?:slides|docs)\.googleapis\.com/v1/(?:presentations|documents)/([\w-]{20,})")


def audited(fid):
    try:
        lines = open(os.path.expanduser("~/.claude/deslop-stamps.jsonl")).read().splitlines()[-200:]
    except OSError:
        return False
    now = time.time()
    for l in reversed(lines):
        try:
            j = json.loads(l)
        except ValueError:
            continue
        if j.get("file") == fid and now - j.get("at", 0) < FRESH:
            return True
    return False


def payload_texts(cmd):
    """Text a batchUpdate would put into the file: from -d '<json>' or -d @file."""
    blobs = []
    for m in re.finditer(r"(?:-d|--data(?:-binary|-raw)?)\s+@['\"]?([^\s'\"]+)", cmd):
        try:
            blobs.append(open(os.path.expanduser(m.group(1))).read())
        except OSError:
            pass
    for m in re.finditer(r"(?:-d|--data(?:-binary|-raw)?)\s+'(\{.*?\})'", cmd, re.S):
        blobs.append(m.group(1))
    out = []
    for b in blobs:
        try:
            j = json.loads(b)
        except ValueError:
            continue
        for r in j.get("requests", []) if isinstance(j, dict) else []:
            t = (r.get("insertText") or {}).get("text") or (r.get("replaceAllText") or {}).get("replaceText")
            if t and len(t.split()) >= 3:
                out.append(t)
    return out


def main():
    if os.environ.get("DISABLE_ANTI_SLOP_HOOK", "0") == "1":
        return 0
    try:
        data = json.loads(sys.stdin.read())
    except ValueError:
        return 0
    if data.get("tool_name") != "Bash":
        return 0
    cmd = (data.get("tool_input") or {}).get("command", "")

    for m in HEREDOC.finditer(cmd):
        import copy_slop_hook as H
        path, body = m.group(1), m.group(3)
        if any(s in path for s in H.SKIP_PATTERNS):
            continue
        hits = H.run_send_checks(body, "prose")
        if hits:
            print(f"AI Slop BLOCKED: {len(hits)} pattern(s) in heredoc for {os.path.basename(path)}:", file=sys.stderr)
            for ln, msg in hits[:20]:
                print(f"  Line ~{ln}: {msg}", file=sys.stderr)
            print("\nFix every line, then run it again.", file=sys.stderr)
            return 2

    if PUSH.search(cmd):
        import copy_slop_hook as H
        bad = []
        for t in payload_texts(cmd):
            for ln, msg in H.run_send_checks(t, "prose"):
                bad.append(f"{t[:60]!r}: {msg}")
        if bad:
            print(f"Document push BLOCKED: {len(bad)} slop hit(s) in the text this push writes:", file=sys.stderr)
            for b in bad[:20]:
                print("  " + b, file=sys.stderr)
            print("\nRewrite those lines, then push again.", file=sys.stderr)
            return 2
        m = FILE_ID.search(cmd)
        if m and ":batchUpdate" in cmd and not audited(m.group(1)):
            print(f"Document push BLOCKED: no whole-file deslop audit of {m.group(1)} in the last 45 minutes.\n"
                  f"Run python3 ~/.claude/skills/deslop/scripts/doc_audit.py {m.group(1)} first. It reads every line\n"
                  "already in the file, so old slop gets fixed in the same push.", file=sys.stderr)
            return 2

    if PUSH.search(cmd) and not recent_pass():
        print("Document push BLOCKED: no deslop pass in the last 45 minutes.\n"
              f"Run {CHECK} <the source .html/.md/.txt or the script that holds the copy> first,\n"
              "fix what it finds, then push. Decks, Docs and Drive files all go through deslop.", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
