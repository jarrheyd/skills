import os
import subprocess
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
SCRIPT = os.path.join(ROOT, "skills", "writing", "deslop", "scripts", "flat_prose.py")


def run(text):
    p = subprocess.run(["python3", SCRIPT], input=text, capture_output=True, text=True)
    return p.returncode, p.stdout


# Six long sentences that march at one length, no semicolons, no asides: the
# shape the 2026 study calls airless. Clears the 150-word floor.
AIRLESS = (
    "The platform processes each incoming request through a series of validation "
    "layers that carefully examine the payload structure before any downstream "
    "handler is ever invoked by the router. The configuration is loaded once at "
    "startup from a central location and then cached for the entire lifetime of the "
    "running process to avoid repeated and expensive reads. Each module registers "
    "its own complete set of request handlers during the initialization phase and "
    "those handlers are resolved lazily when the first matching request arrives. "
    "The logging subsystem captures every single state transition and writes fully "
    "structured records to the configured sink for later analysis by the operations "
    "team. Failures are retried according to a backoff policy that steadily doubles "
    "the interval between successive attempts until a hard ceiling is finally "
    "reached. The scheduler then releases the reserved capacity back into the shared "
    "pool so that other pending requests can proceed without waiting any longer."
)

# Same subject, human rhythm: a short sentence after long ones, and an aside.
HUMAN = (
    "The platform checks every request before a handler runs. It broke twice today "
    "(the payload validator was reading a stale schema, and nobody had noticed) "
    "before we tracked it down. Drew caught it. The config loads once at startup and "
    "caches for the life of the process, which is fine until you change it and forget "
    "the cache never refreshes on its own. That cost us an hour. Now the scheduler "
    "releases capacity back to the pool the moment a request finishes, so nothing "
    "sits waiting behind a slot that is already free."
)

LIST = "\n".join(f"- item number {i} that is fairly wordy but still a list entry here" for i in range(1, 25))


class FlatProse(unittest.TestCase):
    def test_airless_prose_gets_the_nudge(self):
        code, out = run(AIRLESS)
        self.assertEqual(code, 0)
        self.assertIn("reads flat", out)

    def test_human_prose_stays_silent(self):
        code, out = run(HUMAN)
        self.assertEqual(code, 0)
        self.assertEqual(out.strip(), "")

    def test_short_input_stays_silent(self):
        code, out = run("yes okay ra. ill add them sa doc.")
        self.assertEqual(code, 0)
        self.assertEqual(out.strip(), "")

    def test_long_list_stays_silent(self):
        code, out = run(LIST)
        self.assertEqual(code, 0)
        self.assertEqual(out.strip(), "")

    def test_never_blocks(self):
        for text in (AIRLESS, HUMAN, LIST, "", "short"):
            code, _ = run(text)
            self.assertEqual(code, 0, f"exit must be 0 for: {text[:30]!r}")


if __name__ == "__main__":
    unittest.main()
