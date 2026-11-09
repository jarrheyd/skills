#!/usr/bin/env python3
"""PostToolUse on AskUserQuestion. When the user dismisses a picker, the agent tends to carry on as
if it had an answer (handover retro 10-16). This tells it the question is still open: do not act
on a guess, keep it on the list, and ask again at the next natural stop."""
import json, sys

def main():
    try: d = json.load(sys.stdin)
    except Exception: return 0
    if d.get("tool_name") != "AskUserQuestion": return 0
    r = d.get("tool_response")
    # an answered picker carries its answers; anything else (declined, dismissed, cancelled) is open
    if isinstance(r, dict) and r.get("answers"): return 0
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext":
        "He dismissed this picker, so it is still unanswered. Do not act on your recommended option as if he picked it. "
        "Carry on only with work that does not depend on it, keep the question open, and ask it again at the next stop."}}))
    return 0

if __name__ == "__main__":
    sys.exit(main())
