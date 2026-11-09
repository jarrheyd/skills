#!/usr/bin/env python3
"""Comments post from your own accounts (Google Docs, Sheets, Slides, GitHub, Bitbucket, Jira, Confluence,
Word), so they must read as you talking to the person who reads them, not as notes from a machine.

PreToolUse on Bash and MCP tools: refuse a comment or reply whose text
- starts with an AI label ("Claude:", "AI:", a robot), or
- reads as a note to you instead of a comment to the reader ("your call", "needs your yes"), or
- leaks the machinery (your notes folder, handover, job ids, "no source for this"), or
- opens with a status label ("open.", "holds.", "suggest ...", "fix:").
Put VOICE_OK=1 in a Bash command to post anyway when a hit is a false alarm."""
import json, re, sys

LABEL = re.compile(r'^\s*(?:\\u[0-9a-f]{4}|\W){0,3}(claude|ai|bot|assistant)\b\s*[:\-]', re.I)
ROBOT = '\U0001F916'

# (pattern, what to do instead). Matched against each comment text.
TELLS = [
    (r"\byour call\b|\bneeds? your (yes|ok|call|pick)\b|\byour yes\b|\bsay (keep|revert)\b",
     'it talks to you, but the reader is the doc author. Say what you changed or ask them: "i changed X to Y, ok with this?"'),
    (r'\b(the )?vault\b|\bhandover\b',
     'it names our own tools or ids, which mean nothing to the reader. Drop them'),
    (r'\bno source\b|\bnot sourced\b|\bunsourced\b|\bcan(not|\'t) be sourced\b|\bno data that\b',
     'it reads like a machine note. Say who has the info and what to do: "we don\'t have the training dates yet, can you send them before tue?"'),
    (r'\[?CONFIRM:|\bdrop the marker\b|\bthe marker\b',
     'say the placeholder plainly ("took out the blank date")'),
]
OPENERS = re.compile(r'^\s*(?:(?:open|holds|fix|note|todo|status|nb)\s*[.:]|checks out\b|mismatch\b|unclear phrase\b|recommend\b|suggest(?:ion)?\b|\d{1,2}-\d{1,2}\s*,)', re.I)

TEXT_KEYS = r'content|text|comment|body|message|raw|commentBody'
JSON_VAL = re.compile(r'"(?:%s)"\s*:\s*"((?:[^"\\]|\\.)*)"' % TEXT_KEYS)
FLAG_VAL = re.compile(r'(?:--(?:body|content|text|comment|message)|\s-[bm]|-[fF]\s+(?:body|content|text))[ =]\s*(?:"((?:[^"\\]|\\.)*)"|\'([^\']*)\')')
KW_VAL = re.compile(r'\b(?:content|body|text)=\s*(?:"((?:[^"\\]|\\.)*)"|\'([^\']*)\')')

DOCS = re.compile(r'(googleapis\.com|docs\.google|sheets|slides|drive|gdrive|gdocs|graph\.microsoft|bitbucket|atlassian)', re.I)
COMMENTY = re.compile(r'(/comments\b|/replies\b|\bcomment)', re.I)
GH = re.compile(r'\bgh\s+(pr|issue)\s+(comment|review)\b|\bgh\s+api\b[^|;]*\b(comments|reviews)\b', re.I)


def texts_from_bash(cmd):
    flat = cmd.replace('\\"', '"') if '\\"' in cmd and '"content"' not in cmd else cmd
    out = []
    for rx in (JSON_VAL, FLAG_VAL, KW_VAL):
        for m in rx.finditer(flat):
            out.append(next((g for g in m.groups() if g), ''))
    return [t for t in out if t and len(t.split()) >= 2]


def texts_from_mcp(inp):
    out = []
    def walk(v, key=''):
        if isinstance(v, dict):
            for k, x in v.items():
                walk(x, k)
        elif isinstance(v, list):
            for x in v:
                walk(x, key)
        elif isinstance(v, str) and re.fullmatch(TEXT_KEYS, key or '', re.I):
            out.append(v)
    walk(inp)
    return out


def problem(text):
    t = text.replace('\\n', '\n')
    if LABEL.search(t) or t.lstrip().startswith(ROBOT) or t.lstrip().startswith('\\ud83e\\udd16'):
        return 'it starts with an AI label. Drop "Claude:" or any label'
    for rx, fix in TELLS:
        m = re.search(rx, t, re.I)
        if m:
            return f'"{m.group(0)}": {fix}'
    m = OPENERS.match(t)
    if m:
        return (f'it opens with a status label ("{m.group(0).strip()}"). Open with the point in plain words, '
                'and make a change a question: "should we...?" or "maybe we..."')
    return None


def check(tool, inp):
    if tool == 'Bash':
        cmd = str((inp or {}).get('command', ''))
        if 'VOICE_OK=1' in cmd:
            return None
        if not ((DOCS.search(cmd) and COMMENTY.search(cmd)) or GH.search(cmd)):
            return None
        texts = texts_from_bash(cmd)
    elif tool.startswith('mcp__') and (re.search(r'comment', tool, re.I) or re.search(r'(drive|doc|sheet|slide|confluence).*repl', tool, re.I)):
        texts = texts_from_mcp(inp or {})
    else:
        return None
    for t in texts:
        why = problem(t)
        if why:
            return ('Not posted: comments go out under his account and must read as him talking to the reader, '
                    f'not as notes for him. Problem: {why}. Write it the way he would say it to that person out loud '
                    '(MISSION.md, "Comments on someone else\'s document"). VOICE_OK=1 in the command skips this for a false alarm.')
    return None


def main():
    try:
        d = json.load(sys.stdin)
    except Exception:
        return 0
    why = check(d.get('tool_name', ''), d.get('tool_input') or {})
    if why:
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny", "permissionDecisionReason": why}}))
    return 0


if __name__ == '__main__':
    sys.exit(main())
