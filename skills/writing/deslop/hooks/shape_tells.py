"""Shape tells: sentence-pair rhythms that phrase lists miss (2026-10-29).

A reviewer flagged a draft and its deck: "this not that. that not this. phrase 1, phrase 2.
one person, several results." None of the four shapes below tripped the hook. They block in
files, in drafts and in chat sends. Each check is tuned against the writer's own sent
messages (his-sends-sample.txt must stay clean, flagged.txt must all block, both in
$DESLOP_DATA): run scripts/regress.py after any change.
"""

import re

from house import HOUSE

NEG = re.compile(r"(?i)\b(?:doesn'?t|don'?t|isn'?t|aren'?t|wasn'?t|won'?t|can'?t|not|never|no longer)\b")
PRONOUN_START = re.compile(r"(?i)^(?:it|they|this|that|he|she|we|it'?s|they'?re|what)\b")
STOP = {"that", "this", "with", "from", "they", "them", "their", "there", "what", "when", "have",
        "been", "were", "will", "would", "could", "should", "about", "into", "than", "then",
        "just", "only", "more", "also", "because", "each", "every", "some"}


def _sentences(text):
    out = []
    for line_no, line in enumerate(text.split("\n"), 1):
        for s in re.split(r"(?<=[.!?])\s+", line.strip()):
            s = s.strip()
            if s:
                out.append((line_no, s))
    return out


def _stems(s):
    out = set()
    for w in re.findall(r"[a-z]{3,}", s.lower()):
        if w in STOP or w in {"the", "and", "but", "for", "are", "was", "its", "not", "don", "doesn", "isn"}:
            continue
        out.add(re.sub(r"(?:ing|ed|es|s)$", "", w) if len(w) > 4 else w.rstrip("s"))
    return out


def check_negation_flip(text):
    """'The tool doesn't win on price. It wins because...' - deny one thing, then flip to the
    real claim with a pronoun and the same verb. Say the real claim once."""
    v = []
    sents = _sentences(text)
    for (ln, a), (_, b) in zip(sents, sents[1:]):
        if NEG.search(a) and PRONOUN_START.search(b) and len(a.split()) <= 16 and len(b.split()) <= 18:
            # the flip repeats the denied verb right after the pronoun: 'doesn't win ... It wins'
            m = NEG.search(a)
            denied = _stems(" ".join(a[m.end():].split()[:3]))
            verb = _stems(" ".join(b.split()[1:2]))
            if re.match(r"(?i)^(?:it|they|this|that|what)\b", b) and denied & verb:
                v.append((ln, "[BLOCK] negation flip ('X doesn't win on A. It wins because B') - drop the denial, state B"))
    return v


LABEL_PAIR = re.compile(r"(?i)(?:^|[.!?]\s+|\n)\s*(today|yesterday|before|old)\s*:\s*[^.\n]{2,70}\.\s*(next|tomorrow|after|new|soon)\s*:")


def check_mirrored_pair(text):
    """'Today: one team, one product. Next: one team, many products.' - a two-beat
    antithesis built from mirrored halves. Write the one claim plainly."""
    v = []
    for m in LABEL_PAIR.finditer(text):
        v.append((text[:m.start()].count("\n") + 1, "[BLOCK] label-colon antithesis ('Today: X. Next: Y.') - state the change in one plain sentence"))
    # the same two-word head repeated in short clauses: 'one team, one product ... one team, many products'
    for ln, line in enumerate(text.split("\n"), 1):
        if len(line.split()) > 24 or re.search(r"[`|\u201c\"=>]|https?:|\d", line):
            continue
        clauses = [c.strip().lower() for c in re.split(r"[.;:]", line) if c.strip()]
        heads = {}
        for c in clauses:
            words = re.findall(r"[a-z0-9₱$%']+", c)
            if 3 <= len(words) <= 5:
                heads.setdefault(" ".join(words[:2]), []).append(" ".join(words[2:]))
        if any(len(set(cs)) >= 2 for cs in heads.values()):
            v.append((ln, "[BLOCK] mirrored clauses (same two-word head, short halves) - a slogan beat; say it once in plain words"))
    return v


def check_fragment_run(text):
    """'5 people, 2 months, $40k in, $12k kept' - a run of verbless number fragments
    in place of a sentence. A noun list joined by 'and' passes."""
    v = []
    NUMWORD = re.compile(r"^[₱$]?\d[\d.,]*[kKmMbB%x]?\s+[a-z]{2,}")
    for ln, line in enumerate(text.split("\n"), 1):
        # data inventories in docs ('38 total, 26 fixed, 8 in progress') are bullets or long lines
        if re.match(r"\s*[|`_>*-]", line) or "`" in line or len(line.split()) > 30:
            continue
        for sent in re.split(r"(?<=[.!?:])\s+|\n", line):
            chunks = [c.strip() for c in re.split(r",", sent)]
            run = 0
            nums = 0
            for c in chunks:
                words = c.split()
                if 1 <= len(words) <= 3 and not re.search(r"(?i)\b(and|or)\b", c):
                    run += 1
                    nums += bool(NUMWORD.match(c))
                    if run >= 3 and nums >= 3:
                        v.append((ln, "[BLOCK] phrase list ('5 people, 2 months, $40k in') - write a sentence with a verb"))
                        break
                else:
                    run = nums = 0
            else:
                continue
            break
        # two-beat number headline: '5 people, 2 months: ...'
        if re.search(r"(?:^|[.!?]\s+)\d[\w.₱$%]*\s+\w+,\s+\d[\w.₱$%]*\s+\w+\s*:", line):
            v.append((ln, "[BLOCK] two-beat number label ('5 people, 2 months:') - put the numbers in a sentence"))
    return v


CONCEDE = re.compile(r"(?i)\b(?:the same|about the same|similar|close|equal|even)\b[^.\n]{0,70}?,\s*(?:they|it|we|he|she|this|[A-Za-z]+)\s+(?:just|simply|only|really)\s+\w+")


def check_concede_reveal(text):
    """'the margin is about the same, they just sell more' - concede, then reveal with
    'just'. Lead with the real point."""
    return [(text[:m.start()].count("\n") + 1, "[BLOCK] concede-then-reveal ('about the same, they just ...') - lead with the real point")
            for m in CONCEDE.finditer(text)]


SELF_GRADING = re.compile(r"\b(the number that matters|the most honest)\b", re.I)


def check_self_grading(text):
    """'the most honest review', 'the number that matters': grading your own honesty or
    importance reads as cheesy (author note 11-02). Say the fact and stop."""
    return [(text[:m.start()].count("\n") + 1, f"[BLOCK] self-grading ('{m.group(0)}') - state the fact and stop")
            for m in SELF_GRADING.finditer(text)]


# mid-sentence "prod settings not checked yet" stays allowed: only the line label is the tell
PAPERWORK = re.compile(r"(?im)^\s*not checked yet\s*:|\bprinted in the valley\b")


def check_paperwork(text):
    """A 'Not checked yet:' label in a document and a made-up colophon line: 'such an AI slop'
    (author notes 11-02). Leave the provenance out and let the page end on its content. House rule."""
    if not HOUSE:
        return []
    return [(text[:m.start()].count("\n") + 1, f"[BLOCK] paperwork line ('{m.group(0).strip()}') - cut it")
            for m in PAPERWORK.finditer(text)]


# "a team in Cebu", "built in Manila": where the maker sits is not the brand (author note 11-04).
# A branding opinion, not an AI tell, so house rule only.
# 11-09: "a software studio in Cebu" passed, since one adjective broke the match; "shipped from Cebu"
# and "Cebu-based" passed too. "a very weird AI tell is overemphasis on location and geography".
LOCATION_PITCH = re.compile(r"\b(?:(?:a|an|our|the|small)\s+(?:[\w-]+\s+){0,3}?(?:team|company|studio|startup|crew|agency|firm|consultancy|business|brand)\s+(?:based\s+)?(?:in|from|out of)|(?:proudly\s+)?(?:made|built|crafted|shipped|designed)\s+(?:with\s+love\s+)?(?:in|from|out of))\s+(?:the\s+)?(?!Slack|Notion|Figma|Agos|Claude|Codex|Go\b|Rust\b|React|Next|Production|Staging|Dev\b|Prod\b)[A-Z][a-z]+|\b(?!Web|Cloud|Browser|Server|Team|Agent|Text|Model)[A-Z][a-z]+-based\s+(?:team|company|studio|startup|agency|firm|brand)\b")


def check_location_pitch(text):
    """Selling the maker's city ("a team in Cebu"): 'why does a team in cebu matter - lol that is
    not part of our branding' (author note 11-04). Say what the team does, not where it sits."""
    if not HOUSE:
        return []
    return [(text[:m.start()].count("\n") + 1, f"[BLOCK] location pitch ('{m.group(0)}') - cut the place, say what the team does")
            for m in LOCATION_PITCH.finditer(text)]


# A "Still to decide" section at the end of a doc, deck or page: open calls parked for the reader
# instead of asked. His note 11-09: "i dont like always that we just put to be decided items at the
# end of the document etc - fix that systematically". His calls go to him as grill cards the turn the
# material is made; his answer goes into the section it belongs to; what waits on others sits in the
# timeline with an owner and a date. House rule.
PARKED_OPEN = re.compile(r"(?im)^[ \t#*>-]*(?:still to decide|still to be decided|to be decided|open (?:questions|items|calls|decisions)|pending decisions|decisions pending|tbd|questions for (?:you|him|jarrhey))\b[^\n]{0,40}$")


def check_parked_open_items(text):
    """A heading line that parks open calls ('Still to decide', 'Open questions', 'TBD')."""
    if not HOUSE:
        return []
    return [(text[:m.start()].count("\n") + 1, f"[BLOCK] parked open items ('{m.group(0).strip()}') - grill him on each call now (decisions.mjs open), write his answer where the topic lives, put waits in the timeline")
            for m in PARKED_OPEN.finditer(text)]


def check_shape_tells(text):
    return (check_negation_flip(text) + check_mirrored_pair(text)
            + check_fragment_run(text) + check_concede_reveal(text) + check_self_grading(text)
            + check_paperwork(text) + check_location_pitch(text) + check_parked_open_items(text))
