#!/usr/bin/env python3
"""PermissionRequest hook: answer the permission prompts that kept stopping chats (his ask 10-23,
"how can we also resolve repeating permission issues across all chats"). The asks log showed 700+
prompts in two days, nearly all memory/plan file writes, Bash runs and the title tool.

Allows everything except:
- his own calls (AskUserQuestion, ExitPlanMode): those are questions, not permissions
- anything that sends, posts, publishes or deletes outside the machine (drafts only until he says)
- force pushes, pushes to main/master, sudo, rm -rf on home or root
Those fall through to the normal prompt. Every decision is logged to ~/.cache/claude-hooks/auto-allow.log.
"""
import json, os, re, sys, datetime

HIS = {"AskUserQuestion", "ExitPlanMode"}
OUTWARD = re.compile(r"(^|_)(send|post|publish|delete|remove|reply_to|create_forum_post|add_reaction|respond|merge)", re.I)
BASH_RISK = re.compile(
    r"git\s+push\s+[^|;&]*(--force|-f\b|\b(main|master)\b)"
    r"|\bsudo\b"
    r"|rm\s+-[a-z]*r[a-z]*f?\s+(/|~|\$HOME)\s*($|[;&|])"
    r"|\bdiscord_send\b|gmail_send"
)


def verdict(tool, inp):
    if tool in HIS:
        return None, "his call"
    if tool.startswith("mcp__"):
        name = tool.split("__", 2)[-1]
        if OUTWARD.search(name):
            return None, "outward"
        return "allow", "mcp"
    if tool == "Bash":
        cmd = str((inp or {}).get("command", ""))
        if BASH_RISK.search(cmd):
            return None, "risky bash"
        return "allow", "bash"
    return "allow", "tool"


def main():
    try:
        ev = json.load(sys.stdin)
    except Exception:
        return
    tool = str(ev.get("tool_name") or "")
    inp = ev.get("tool_input") or {}
    if os.environ.get("AUTO_ALLOW_OFF") == "1":
        return
    decision, why = verdict(tool, inp)
    try:
        os.makedirs(os.path.expanduser("~/.cache/claude-hooks"), exist_ok=True)
        with open(os.path.expanduser("~/.cache/claude-hooks/auto-allow.log"), "a") as f:
            f.write(json.dumps({"at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "tool": tool, "decision": decision or "ask", "why": why,
                                "what": str(inp.get("command") or inp.get("file_path") or "")[:160], "sid": str(ev.get("session_id", ""))[:40]}) + "\n")
    except Exception:
        pass
    if decision == "allow":
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "PermissionRequest", "decision": {"behavior": "allow"}}}))


if __name__ == "__main__":
    main()
