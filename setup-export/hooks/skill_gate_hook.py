#!/usr/bin/env python3
"""PreToolUse gate: a write that matches a route in skill_routes.json waits until the chat loaded that skill.

Nobody should have to name a skill for it to load. Routes map what is being written (path, content)
to the skill that owns it. Loaded means: the Skill tool called with that name, a typed /name, or its
SKILL.md read. Checked once per chat by scanning the transcript. Bypass: DISABLE_SKILL_GATE=1.
"""
import json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))


def routes():
    with open(os.path.join(HERE, 'skill_routes.json')) as f:
        return json.load(f)['routes']


def needed(path, content, rs):
    out = []
    for r in rs:
        if r.get('skip_path') and re.search(r['skip_path'], path):
            continue
        if r.get('path') and not re.search(r['path'], path):
            continue
        if r.get('content') and not re.search(r['content'], content or ''):
            continue
        out.append(r)
    return out


def loaded(skill, transcript):
    pats = [f'"skill":"{skill}"', f'"skill": "{skill}"', f'skills/{skill}/SKILL.md', f'<command-name>/{skill}<', f'Base directory for this skill: ', ]
    try:
        with open(transcript, errors='ignore') as f:
            text = f.read()
    except Exception:
        return True  # no transcript, never block
    if any(p in text for p in pats[:4]):
        return True
    return re.search(r'Base directory for this skill: \S*/' + re.escape(skill) + r'\b', text) is not None


def main():
    if os.environ.get('DISABLE_SKILL_GATE') == '1':
        return 0
    try:
        data = json.loads(sys.stdin.read())
    except Exception:
        return 0
    ti = data.get('tool_input') or {}
    path = ti.get('file_path') or ''
    if not path:
        return 0
    content = ti.get('content') or ti.get('new_string') or ''
    if not content and ti.get('edits'):
        content = '\n'.join(e.get('new_string', '') for e in ti['edits'])
    missing = [r for r in needed(path, content, routes()) if not loaded(r['skill'], data.get('transcript_path', ''))]
    if not missing:
        return 0
    lines = [f"- {r['skill']} ({r['why']})" for r in missing]
    sys.stderr.write("Skill gate: load these skills with the Skill tool before writing " + os.path.basename(path) + ", then write again:\n" + "\n".join(lines) + "\nRoutes live in ~/.claude/hooks/skill_routes.json.\n")
    return 2


if __name__ == '__main__':
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except Exception:
        sys.exit(0)  # a broken route never blocks a write
