#!/usr/bin/env python3
"""PreToolUse hook: stop agent-built cloud setups that keep billing while idle (idle Cloud Run revisions
kept billing until someone found them by hand).

What it blocks, and why:
- `gcloud run deploy` with no explicit `--min-instances=0`. A deploy copies the minimum from the
  last revision, so one warm instance spread to every new revision. One site had min 1 on
  179 revisions and 43 tagged ones warm at once, about USD 175 in one week.
- `--min-instances` above 0 on a revision. Production that truly needs a warm instance uses one
  service-level minimum (`gcloud run services update <svc> --min=1`), which never multiplies.
- A deploy file (cloudbuild*.yaml, GitHub workflow, deploy script) that tags revisions and never
  removes the tag, or that runs browser tests before lint and type checks (one pipeline: 27 of
  83 builds failed, one spent 34 of 40 minutes in browser tests).

Escape hatch for a real need: put `COST_OK=<reason>` in the command, or a `# cost-ok: <reason>`
line in the file. Off switch: COST_GUARD_OFF=1. Test: python3 cloud_cost_hook.py --test
"""
import json, os, re, sys

DEPLOY_FILE = re.compile(r"(cloudbuild[^/]*\.ya?ml|\.github/workflows/[^/]+\.ya?ml|deploy[^/]*\.(sh|ya?ml|mjs|js|ts))$")
RUN_DEPLOY = re.compile(r"gcloud\s+(?:beta\s+|alpha\s+)?run\s+deploy\b")
RUN_UPDATE = re.compile(r"gcloud\s+(?:beta\s+|alpha\s+)?run\s+services\s+update(?!-traffic)\b")
MIN_FLAG = re.compile(r"--min-instances(?:=|\s+)['\"]?(\d+)")
BROWSER = re.compile(r"\b(playwright\s+test|cypress\s+run|maestro\s+test|test:e2e|e2e\b|test:browser)", re.I)
CHEAP = re.compile(r"\b(lint|typecheck|type-check|tsc\b|tsc\s+--noEmit)", re.I)


def joined(text):
    """One logical line per shell command: fold backslash continuations."""
    return re.sub(r"\\\s*\n\s*", " ", text)


def command_problems(cmd):
    if "COST_OK=" in cmd:
        return []
    out = []
    for line in joined(cmd).splitlines():
        for seg in re.split(r"&&|\|\||;", line):
            deploy, update = RUN_DEPLOY.search(seg), RUN_UPDATE.search(seg)
            if not (deploy or update):
                continue
            m = MIN_FLAG.search(seg)
            if m and int(m.group(1)) > 0:
                out.append("sets --min-instances=%s on a revision; every later deploy copies it and every tag keeps it warm. "
                           "Use --min-instances=0, and if production truly needs a warm instance, one service-level "
                           "`gcloud run services update <svc> --min=1`." % m.group(1))
            elif deploy and not m:
                out.append("`gcloud run deploy` without --min-instances=0 copies the last revision's minimum (one site "
                           "carried min 1 into 179 revisions). Add --min-instances=0.")
    return out


def file_problems(path, text):
    if not DEPLOY_FILE.search(path) or "cost-ok:" in text:
        return []
    out = command_problems(text)
    flat = joined(text)
    if RUN_DEPLOY.search(flat) and re.search(r"--tag[=\s]", flat) and not re.search(r"remove-tags|untag", flat):
        out.append("tags each deployed revision but never removes the tag; a tagged revision stays addressable and keeps "
                   "its minimum running. Remove the build's tag after promotion and after a failed smoke test.")
    b = BROWSER.search(text)
    if b:
        c = CHEAP.search(text)
        if not c or c.start() > b.start():
            out.append("runs browser tests before lint and type checks. Put lint, typecheck and targeted tests first and stop "
                       "on failure before the browser suite (one pipeline: 27 of 83 builds failed, one spent 34 of 40 "
                       "minutes in browser tests).")
    return out


def after_edit(path, old, new, replace_all):
    try:
        cur = open(path).read()
    except OSError:
        return new
    return cur.replace(old, new) if replace_all else cur.replace(old, new, 1)


def check(event):
    tool, inp = event.get("tool_name", ""), event.get("tool_input") or {}
    if tool == "Bash":
        return command_problems(inp.get("command", ""))
    path = inp.get("file_path", "")
    if tool == "Write":
        return file_problems(path, inp.get("content", ""))
    if tool == "Edit":
        return file_problems(path, after_edit(path, inp.get("old_string", ""), inp.get("new_string", ""), inp.get("replace_all")))
    if tool == "MultiEdit":
        text = open(path).read() if os.path.exists(path) else ""
        for e in inp.get("edits", []):
            old, new = e.get("old_string", ""), e.get("new_string", "")
            text = text.replace(old, new) if e.get("replace_all") else text.replace(old, new, 1)
        return file_problems(path, text)
    return []


def main():
    if os.environ.get("COST_GUARD_OFF") == "1":
        return 0
    try:
        event = json.load(sys.stdin)
    except Exception:
        return 0
    problems = check(event)
    if not problems:
        return 0
    sys.stderr.write("Cloud cost guard: this setup keeps billing while idle.\n- " + "\n- ".join(problems) +
                     "\nFix it, or for a real need add COST_OK=<reason> to the command or '# cost-ok: <reason>' to the file.\n")
    return 2


def test():
    bad = [
        {"tool_name": "Bash", "tool_input": {"command": "gcloud run deploy web --image=x --region=asia-southeast1"}},
        {"tool_name": "Bash", "tool_input": {"command": "gcloud run deploy web \\\n  --image=x \\\n  --min-instances=1"}},
        {"tool_name": "Bash", "tool_input": {"command": "gcloud run services update web --min-instances 2"}},
        {"tool_name": "Write", "tool_input": {"file_path": "/r/cloudbuild.yaml", "content": "gcloud run deploy web --min-instances=0 --no-traffic --tag=sha-$SHORT_SHA"}},
        {"tool_name": "Write", "tool_input": {"file_path": "/r/cloudbuild.yaml", "content": "steps:\n- run: npx playwright test\n- run: pnpm lint\n"}},
        {"tool_name": "Write", "tool_input": {"file_path": "/r/.github/workflows/ci.yml", "content": "- run: pnpm test:e2e\n"}},
    ]
    good = [
        {"tool_name": "Bash", "tool_input": {"command": "gcloud run deploy web --image=x --min-instances=0"}},
        {"tool_name": "Bash", "tool_input": {"command": "gcloud run services update web --min=1"}},
        {"tool_name": "Bash", "tool_input": {"command": "gcloud run services update-traffic web --remove-tags=a,b"}},
        {"tool_name": "Bash", "tool_input": {"command": "COST_OK=latency-sla gcloud run deploy web --min-instances=1"}},
        {"tool_name": "Write", "tool_input": {"file_path": "/r/cloudbuild.yaml", "content": "gcloud run deploy web \\\n --min-instances=0 --tag=sha-1\nbash scripts/untag-release.sh sha-1 p"}},
        {"tool_name": "Write", "tool_input": {"file_path": "/r/cloudbuild.yaml", "content": "- run: pnpm lint && pnpm typecheck\n- run: npx playwright test\n"}},
        {"tool_name": "Write", "tool_input": {"file_path": "/r/notes.md", "content": "gcloud run deploy web"}},
    ]
    fails = [e for e in bad if not check(e)] + [e for e in good if check(e)]
    for e in fails:
        print("WRONG:", json.dumps(e)[:160])
    print("ok" if not fails else "%d wrong" % len(fails))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(test() if "--test" in sys.argv else main())
