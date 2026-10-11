#!/usr/bin/env python3
"""Advisory check for airless prose: the tells AI leaves out.

The 2026 Economist study found the modern machine tell is absence, not
vocabulary. LLMs write long, evenly-punctuated sentences with almost no
semicolons or parenthetical asides. That cannot be a deslop hook: the write
hooks are zero-tolerance, and a bullet list or a commit message legitimately
lacks all of it, so a block would fire constantly. So this runs in the review
path instead, never blocks (exit 0 always), and speaks only when several
signals agree the prose is clearly flat.

Usage:
    flat_prose.py <file>      # read a file
    flat_prose.py             # read stdin

Output: one plain line when the prose reads flat, nothing otherwise.

Tuning lives in the constants below.
"""
import re
import sys

# A short passage carries no signal: a commit message or a two-line note has no
# room for a semicolon or an aside whether a human or a model wrote it. Below
# this many words of flowing prose, stay silent.
MIN_PROSE_WORDS = 150

# "Flat" is a composite. Each of these must hold at once, which is what keeps
# the nudge rare and true rather than a constant background hum.
LONG_MEAN_WORDS = 24        # sentences average at least this many words
LOW_SPREAD_RATIO = 0.45     # stdev / mean below this = sentences march in step
MIN_SENTENCES = 5           # need enough sentences for the spread to mean anything

NUDGE = ("deslop (advisory): this stretch reads flat and even. Break a long "
         "sentence with a short one, or drop in an aside. Nothing blocked.")


def strip_non_prose(text):
    """Drop everything that is terse by design, leaving flowing paragraphs.

    Fenced code, list items, table rows and headings all legitimately lack the
    connective punctuation we look for, so measuring them would misfire.
    """
    out = []
    in_fence = False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("```") or stripped.startswith("~~~"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if not stripped:
            continue
        if stripped.startswith("#"):            # heading
            continue
        if stripped.startswith("|"):            # table row
            continue
        if re.match(r"^([-*+]|\d+[.)])\s+", stripped):   # list item
            continue
        out.append(stripped)
    return " ".join(out)


def sentences(prose):
    parts = re.split(r"[.!?]+(?:\s+|$)", prose)
    return [p for p in (s.strip() for s in parts) if p]


def is_flat(text):
    prose = strip_non_prose(text)
    words = prose.split()
    if len(words) < MIN_PROSE_WORDS:
        return False

    sents = sentences(prose)
    if len(sents) < MIN_SENTENCES:
        return False

    lengths = [len(s.split()) for s in sents]
    mean = sum(lengths) / len(lengths)
    if mean < LONG_MEAN_WORDS:
        return False

    variance = sum((n - mean) ** 2 for n in lengths) / len(lengths)
    stdev = variance ** 0.5
    if mean and (stdev / mean) >= LOW_SPREAD_RATIO:
        return False

    if ";" in prose:
        return False
    if "(" in prose and ")" in prose:
        return False

    return True


def main():
    if len(sys.argv) > 1:
        try:
            with open(sys.argv[1], "r", encoding="utf-8") as fh:
                text = fh.read()
        except OSError as exc:
            print(f"flat_prose: cannot read {sys.argv[1]}: {exc}", file=sys.stderr)
            sys.exit(0)   # advisory only; never fail a caller
    else:
        text = sys.stdin.read()

    if is_flat(text):
        print(NUDGE)
    sys.exit(0)


if __name__ == "__main__":
    main()
