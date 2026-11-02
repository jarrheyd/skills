#!/usr/bin/env python3
"""Run the deslop copy checks on files or text from the command line.

For anything the Write/Edit hook never sees: decks rendered by a script, Docs and Slides
pushed over REST, drafts saved by a script, text built in a heredoc.

  deslop_check.py FILE...            prose mode (.html is unescaped, tags stripped)
  deslop_check.py --chat FILE|-      chat mode (drafts, chat sends)
  deslop_check.py --learn "TEXT" --why "their words"
                                     add a flagged line to flagged.txt in $DESLOP_DATA
                                     (default ~/.claude/deslop-data); the regression
                                     run fails until a check blocks it

A pass writes a stamp (~/.claude/deslop-stamps.jsonl). The Bash document gate lets a
Slides, Docs or Drive push through only after a pass in the last 45 minutes.
Exit 0 clean, 2 blocked.
"""
import html
import json
import os
import re
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "hooks"))
import copy_slop_hook as H  # noqa: E402

STAMPS = os.path.expanduser("~/.claude/deslop-stamps.jsonl")
DATA = os.path.expanduser(os.environ.get("DESLOP_DATA", "~/.claude/deslop-data"))


def text_of(path):
    raw = sys.stdin.read() if path == "-" else open(path, encoding="utf-8", errors="replace").read()
    ext = os.path.splitext(path)[1].lower()
    if ext in (".html", ".htm"):
        raw = re.sub(r"(?is)<(script|style)\b.*?</\1>", " ", raw)
        raw = re.sub(r"(?i)<br\s*/?>|</(p|div|h\d|li|section)>", "\n", raw)
        raw = html.unescape(re.sub(r"<[^>]+>", " ", raw))
        raw = "\n".join(re.sub(r"[ \t]+", " ", l).strip() for l in raw.split("\n"))
        raw = re.sub(r"\n{2,}", "\n\n", raw)
    elif ext in H.SOURCE_EXTENSIONS:
        raw = H.extract_string_literals(raw, path)
    return raw


def check(text, chat):
    if chat:
        return H.run_send_checks(text, "chat")
    return H.run_send_checks(text, "prose") + H.check_interface_narration(text)


def main(argv):
    if "--learn" in argv:
        t = argv[argv.index("--learn") + 1]
        why = argv[argv.index("--why") + 1] if "--why" in argv else ""
        os.makedirs(DATA, exist_ok=True)
        with open(os.path.join(DATA, "flagged.txt"), "a") as f:
            f.write(t.replace("\n", " ") + "\n")
        with open(os.path.join(DATA, "flagged-why.jsonl"), "a") as f:
            f.write(json.dumps({"at": time.strftime("%Y-%m-%dT%H:%M:%S"), "text": t, "why": why}) + "\n")
        blocked = bool(check(t, chat=True) or check(t, chat=False))
        print("learned" + ("" if blocked else ": NOT caught yet, add a check in hooks/shape_tells.py and run scripts/regress.py"))
        return 0
    chat = "--chat" in argv
    files = [a for a in argv if not a.startswith("--")] or ["-"]
    bad = 0
    for f in files:
        hits = check(text_of(f), chat)
        if hits:
            bad += len(hits)
            print(f"{f}: {len(hits)} slop pattern(s)")
            for ln, msg in hits[:30]:
                print(f"  line ~{ln}: {msg}")
    if bad:
        print("\nFix every line, then run this again. Pushes stay blocked until it passes.")
        return 2
    # only a document pass unlocks a push; a draft or chat pass does not
    if chat:
        print("deslop: clean")
        return 0
    with open(STAMPS, "a") as s:
        s.write(json.dumps({"at": time.time(), "files": [os.path.abspath(f) for f in files if f != "-"], "chat": chat}) + "\n")
    print("deslop: clean")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
