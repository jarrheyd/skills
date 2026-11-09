#!/usr/bin/env python3
"""Stop hook. A turn that ends on "next step" or "if you want" while its own plan still has open
steps is stopping short (rule: do not stop mid-loop). Blocks once and
says which steps are open. Never blocks twice in a row (stop_hook_active)."""
import json, re, sys
try: __import__('sys').path.insert(0, __import__('os').path.expanduser('~/.claude/hooks')); __import__('hooklog').install('open_steps')  # optional fire log, see hooklog.py
except Exception: pass

# A user message that arrives next to system notices sometimes gets answered with "No response requested."
# A turn that carries the user's words never ends on that.
NO_RESPONSE = re.compile(r"^\s*No response requested\.?\s*$", re.I)
MACHINE = re.compile(r"^(<task-notification|\[SYSTEM NOTIFICATION)")

def his_text(e):
    """The user's own words in a user line, else ''."""
    o = e.get("origin") or {}
    if o and not (o.get("kind") == "human" or (o.get("name") == "office" and o.get("asUser"))): return ""
    c = (e.get("message") or {}).get("content")
    t = c if isinstance(c, str) else " ".join(x.get("text", "") for x in (c or []) if isinstance(x, dict) and x.get("type") == "text")
    t = (t or "").strip()
    return "" if not t or MACHINE.match(t) else t

OFFER = re.compile(r"(?i)\b(next step|if you want|want me to|shall i|should i (?:go ahead|continue|proceed)|let me know if|happy to (?:also|continue))\b")

def main():
    try: d = json.load(sys.stdin)
    except Exception: return 0
    if d.get("stop_hook_active"): return 0
    path = d.get("transcript_path")
    if not path: return 0
    last_text, todos, his, his_open = "", None, "", False
    try:
        with open(path) as f:
            for line in f:
                if '"assistant"' not in line and '"user"' not in line: continue
                try: e = json.loads(line)
                except Exception: continue
                if e.get("isSidechain"): continue
                if e.get("type") == "user":
                    t = his_text(e)
                    if t: his, his_open = t, True
                    continue
                if e.get("type") != "assistant": continue
                for c in (e.get("message") or {}).get("content") or []:
                    if c.get("type") == "text" and c.get("text", "").strip():
                        last_text = c["text"]
                        if not NO_RESPONSE.match(last_text): his_open = False
                    if c.get("type") == "tool_use" and c.get("name") == "TodoWrite": todos = (c.get("input") or {}).get("todos") or []
    except Exception: return 0
    if his_open and NO_RESPONSE.match(last_text):
        print(json.dumps({"decision": "block", "reason": f"This turn carries his message: \"{his[:200]}\". The system notices around it are noise, not his words. Act on his message now (a picker answer: apply the option he picked)."}))
        return 0
    if not todos or not OFFER.search(last_text[-1200:]): return 0
    left = [t.get("content", "") for t in todos if t.get("status") in ("pending", "in_progress")]
    if not left: return 0
    print(json.dumps({"decision": "block", "reason": f"Your plan still has {len(left)} open step(s): " + "; ".join(left[:4]) + ". Do them now instead of offering them. Stop only for a call that is truly his, asked with AskUserQuestion."}))
    return 0

if __name__ == "__main__":
    sys.exit(main())
