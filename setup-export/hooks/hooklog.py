"""One line per hook fire, so the experiments can weigh what each gate costs against what it catches
(10-26: deslop, os_guard, status_append, open_steps, picker_not_list, unwrap_links and
client_doc_template never recorded a block). A hook calls install("<name>") right after its imports;
on exit this appends {at, hook, verdict, code, ms, session} to ~/.local/state/claude-hooks/hook-log.jsonl.

verdict: block (exit 2, or a block/deny decision printed), ask, note (other output), pass.
Never raises: a logging failure must not change what the hook does.
"""
import atexit, json, os, sys, time

LOG = os.path.expanduser("~/.local/state/claude-hooks/hook-log.jsonl")


def verdict(code, out):
    if code == 2 or '"block"' in out or '"deny"' in out:
        return "block"
    if '"ask"' in out:
        return "ask"
    return "note" if out.strip() else "pass"


def install(name):
    try:
        t0 = time.time()
        st = {"code": 0, "out": ""}
        real_exit = sys.exit

        def _exit(code=0):
            st["code"] = code if isinstance(code, int) else (1 if code else 0)
            real_exit(code)

        sys.exit = _exit
        real_out = sys.stdout

        class Tee:
            def write(self, s):
                if len(st["out"]) < 4000:
                    st["out"] += s
                return real_out.write(s)

            def flush(self):
                return real_out.flush()

            def __getattr__(self, k):
                return getattr(real_out, k)

        sys.stdout = Tee()

        def _log():
            try:
                os.makedirs(os.path.dirname(LOG), exist_ok=True)
                row = {"at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "hook": name, "verdict": verdict(st["code"], st["out"]), "code": st["code"], "ms": int((time.time() - t0) * 1000), "session": os.environ.get("CLAUDE_SESSION_ID") or os.environ.get("CLAUDE_CODE_SESSION_ID")}
                with open(LOG, "a") as f:
                    f.write(json.dumps(row) + "\n")
            except Exception:
                pass

        atexit.register(_log)
    except Exception:
        pass
