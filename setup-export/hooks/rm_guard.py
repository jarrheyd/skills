#!/usr/bin/env python3
"""PreToolUse Bash hook: stop deletes that Claude Code's own delete guard would hold for a click
(chats kept stalling on an allow click nobody saw). That guard fires even
in bypass mode, on rm with a variable or glob path ("rm -f $S/*.png", "rm -f shots/*") and on
"git worktree remove $W".

Denying here costs nothing: the chat gets the reason at once and rewrites the command with a
literal path or find -delete, instead of sitting on a prompt nobody sees.
Off switch: RM_GUARD_OFF=1. Test: python3 rm_guard.py --test
"""
import json, os, re, sys

HEREDOC = re.compile(r"<<-?\s*(['\"]?)(\w+)\1.*?\n.*?\n\s*\2\s*(\n|$)", re.S)
SEGMENT = re.compile(r"\|\||&&|[;|&\n(){}]|\bthen\b|\bdo\b|\belse\b")
WRAPPERS = re.compile(r"^(sudo|command|builtin|xargs|nohup|time)\s+(-\S+\s+)*")
RISKY_ARG = re.compile(r"[$`*?]|^~/?$|^/$|^\.{1,2}/?$")

WHY = ("Stopped before Claude Code's delete guard could hold this chat for a permission click. "
       "Rewrite it with literal paths: rm -f /abs/dir/a.png /abs/dir/b.png, or for a pattern "
       "find /abs/dir -maxdepth 1 -name '*.png' -delete, or git worktree remove --force /abs/path. "
       "Spell the directory out instead of using a variable or a bare glob.")


def risky(cmd):
    cmd = HEREDOC.sub("\n", cmd)
    for seg in SEGMENT.split(cmd):
        seg = WRAPPERS.sub("", seg.strip())
        m = re.match(r"(rm|rmdir)\s+(.*)", seg) or re.match(r"git\s+worktree\s+remove\s+(.*)", seg)
        if not m:
            continue
        args = [a for a in re.split(r"\s+", m.group(m.lastindex)) if a and not a.startswith("-") and not a.startswith("2>")]
        if any(RISKY_ARG.search(a.strip("'\"")) for a in args):
            return seg[:120]
    return None


# A find over / or the home folder can run for 10+ minutes and starve everything else of disk.
# A search starts at a folder, never at / or the home root.
SEARCH = re.compile(r"^(find|bfs|fd|rg|grep|ugrep|mdfind)\b")
WIDE = re.compile(r"^(/|~|~/|/Users|/Users/[^/\s]+|/Users/[^/\s]+/|\$HOME|\$HOME/|/System|/Volumes|/private)$")
SCAN_WHY = ("Stopped a search over the whole disk or home folder: it ties up the disk for minutes."
            " Search the folder it lives in, e.g. find ~/Documents/code -maxdepth 4 -name 'x*', "
            "or use the Glob tool on that folder.")


def wide_scan(cmd):
    cmd = HEREDOC.sub("\n", cmd)
    cmd = re.sub(r"'[^']*'|\"[^\"]*\"", "q", cmd)  # words in quotes are text, not a command
    for seg in SEGMENT.split(cmd):
        seg = WRAPPERS.sub("", seg.strip())
        if not SEARCH.match(seg):
            continue
        words = re.split(r"\s+", seg)
        args = [a.strip("'\"") for a in words[1:]]
        if words[0] in ("grep", "rg", "ugrep"):  # the first plain word is the pattern, not a folder
            plain = [i for i, a in enumerate(args) if not a.startswith("-")]
            if plain: args = args[:plain[0]] + args[plain[0] + 1:]
        if any(WIDE.match(a) for a in args):
            return seg[:120]
    return None


def main():
    if os.environ.get("RM_GUARD_OFF") == "1":
        return
    try:
        ev = json.load(sys.stdin)
    except Exception:
        return
    if ev.get("tool_name") != "Bash":
        return
    cmd = str((ev.get("tool_input") or {}).get("command", ""))
    scan = wide_scan(cmd)
    if scan:
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
                                                 "permissionDecisionReason": f"{SCAN_WHY} (matched: {scan})"}}))
        return
    hit = risky(cmd)
    if hit:
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
                                                 "permissionDecisionReason": f"{WHY} (matched: {hit})"}}))


def test():
    bad = ["rm -f $S/*.png", 'rm -rf "$S/iso" "$S"/viz.ts', "rm -f shots4/*", "cd x && rm -f p_*",
           "rm -rf * ", "git worktree remove --force $W", "for f in a; do rm $D/$f; done", "sudo rm -rf ~",
           "ls; rm -f `pwd`/x", "rm -rf out/fails/*"]
    good = ["rm -f /Users/x/a.png", "rm -rf /Users/x/tmp/build", "git rm --cached a.txt", "echo rm -f $S/*",
            "find /Users/x/shots -maxdepth 1 -name '*.png' -delete", "npm run clean",
            "python3 - <<'EOF'\nimport os\nos.system('rm -f $X/*')\nEOF\necho ok", "grep -rn 'rm -rf' .",
            "git worktree remove --force /Users/x/wt"]
    fails = [c for c in bad if not risky(c)] + [c for c in good if risky(c)]
    wide = ["find / -xdev -type d -name 'qa-gate*'", "find ~ -name x", "cd a && find /Users/someone -name y", "rg foo /", "mdfind -onlyin / x", "find $HOME -name z"]
    narrow = ["find /Users/x/code -maxdepth 3 -name q", "find . -name '*.js'", "rg foo ~/Documents/code", "grep -rn / file.txt", "echo find /", "echo '- blocks (find / etc.)' >> log.md"]
    fails += [c for c in wide if not wide_scan(c)] + [c for c in narrow if wide_scan(c)]
    print("FAIL", fails) if fails else print(f"ok {len(bad)} blocked, {len(good)} passed")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(test()) if sys.argv[1:] == ["--test"] else main()
