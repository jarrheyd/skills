#!/usr/bin/env python3
"""Keep deslop current: every line he flagged must block, his real sends must pass.

Data lives outside this repo (it holds his own messages): $DESLOP_DATA, default ~/.claude/deslop-data.
  flagged.txt          one flagged line per line (added by deslop_check.py --learn)
  his-sends-sample.txt his sent messages, separated by =====, must stay clean
Exit 0 when both hold, 1 otherwise, listing what to fix.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "hooks"))
import copy_slop_hook as H  # noqa: E402

T = os.path.expanduser(os.environ.get("DESLOP_DATA", "~/.claude/deslop-data"))
if not os.path.isdir(T):
    print(f"no deslop data at {T}; set DESLOP_DATA")
    sys.exit(1)
flagged = [l.strip() for l in open(os.path.join(T, "flagged.txt")) if l.strip()]
missed = [l for l in flagged if not (H.run_send_checks(l, "chat") or H.run_send_checks(l, "prose"))]
sends = [s for s in open(os.path.join(T, "his-sends-sample.txt")).read().split("\n=====\n") if s.strip()]
# typography and spelling bans (curly quotes, em dash, British) stay strict on drafts even though his own typing slips
TYPO = ("curly", "em dash", "British spelling")
false_pos = [(s, [h for h in H.run_send_checks(s, "chat") if not any(t in h[1] for t in TYPO)]) for s in sends]
false_pos = [(s, h) for s, h in false_pos if h]
print(f"flagged: {len(flagged) - len(missed)}/{len(flagged)} blocked; his sends: {len(sends) - len(false_pos)}/{len(sends)} clean")
for l in missed:
    print("  NOT BLOCKED:", l[:140])
for s, h in false_pos[:10]:
    print("  BLOCKS HIS OWN SEND:", h[0][1][:60], "|", s[:120].replace("\n", " / "))
sys.exit(1 if missed or false_pos else 0)
