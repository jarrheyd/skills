"""House rules: one author's own taste, layered on the general AI-tell checks.

Off by default, so a shared install only catches tells any reader would spot. On when
$DESLOP_DATA/house-rules.md exists (default ~/.claude/deslop-data) or DESLOP_HOUSE=1.
"""
import os

DATA = os.path.expanduser(os.environ.get("DESLOP_DATA", "~/.claude/deslop-data"))
HOUSE = os.environ.get("DESLOP_HOUSE") == "1" or os.path.exists(os.path.join(DATA, "house-rules.md"))
