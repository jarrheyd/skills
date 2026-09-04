import json
import os
import subprocess
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
DESLOP = os.path.join(ROOT, "skills", "writing", "deslop")
HOOK = os.path.join(DESLOP, "hooks", "copy_slop_hook.py")


def run(content, path="draft.md", tool="Write"):
    key = "content" if tool == "Write" else "new_string"
    payload = json.dumps({"tool_name": tool, "tool_input": {"file_path": path, key: content}})
    p = subprocess.run(["python3", HOOK], input=payload, capture_output=True, text=True)
    return p.returncode, p.stderr


BLOCKS = [
    ("fast-paced opener", "In today's fast-paced world we ship."),
    ("not-just reframe", "It's not just a tool. It's a revolution."),
    ("unlock", "Unlock the power of skills."),
    ("sycophancy", "Great question! Here is the answer."),
    ("candor opener", "Honestly, this is fine."),
    ("real talk", "Real talk. It works."),
    ("hits different", "This one hits different."),
    ("but make it", "Coffee but make it corporate."),
    ("came back", "It came back null."),
    ("operationalize", "We need to operationalize this."),
    ("question pile-up", "Top? Bottom? Both ends?"),
    ("negation ladder", "Not 95. Not 98. Fifty for fifty."),
    ("either-or", "Either it matches or it doesn't."),
    ("hyphen title", "the-thing-that-quietly-broke story"),
    ("triple adjective", "It was specific, careful, deliberate."),
    ("studies show", "Studies show this works."),
    ("moves the needle", "This moves the needle."),
    ("testament", "It stands as a testament to grit."),
    ("chatbot outro", "I hope this helps with the launch."),
    ("tool remnant", "See :contentReference[oaicite:1] for detail."),
    ("serves as", "The file serves as the entry point."),
    ("em dash", "The report is done — mostly."),
    ("curly quote", "He said “fine” and left."),
    ("middot", "Jan · Jul · Dec"),
    ("title case heading", "# The Art Of The Deal"),
    ("heading with banned phrase", "# Unlock the power of skills"),
    ("explainer heading", "# The margin gap, and why it matters"),
    ("bold-lead paragraph", "**Evidence boundary.** A timestamp confirms nothing."),
    ("restatement", "The invite button opens the native share sheet from the circle page. The invite button opens the native share sheet from the circle page."),
    ("filler transition", "Furthermore, the plan holds."),
    ("wordy", "We did this in order to ship."),
]

PASSES = [
    ("plain report", "The report lists every flow that ran. Three failed on login. Fix the selector and rerun."),
    ("parallel bullets", "- Sprint planning on Aug 20 covered the invite flow\n- Sprint review on Aug 22 covered the invite flow"),
    ("label colon line", "**Pending:** the signed SOW from the client."),
    ("comma in heading", "# Kindred invites, or how circles grow"),
    ("scope heading", "# Invites: what changed"),
    ("schedule not gloss", "# Migration, in three weeks"),
    ("one furthermore mid-sentence", "The plan holds and furthermore covers the edge."),
]


class CopyHook(unittest.TestCase):
    def test_blocks(self):
        for name, text in BLOCKS:
            with self.subTest(name):
                code, err = run(text)
                self.assertEqual(code, 2, f"{name!r} should block; stderr: {err}")

    def test_passes(self):
        for name, text in PASSES:
            with self.subTest(name):
                code, err = run(text)
                self.assertEqual(code, 0, f"{name!r} should pass; stderr: {err}")

    def test_html_entity_only_decoded_for_html(self):
        self.assertEqual(run("done &mdash; mostly", path="a.md")[0], 0)
        self.assertEqual(run("done &mdash; mostly", path="a.html")[0], 2)

    def test_non_prose_files_skip(self):
        self.assertEqual(run("In today's fast-paced world", path="data.json")[0], 0)

    def test_source_string_literals_checked(self):
        src = 'const x = "In today\'s fast-paced world we ship faster";'
        self.assertEqual(run(src, path="app.ts")[0], 2)
        self.assertEqual(run("// In today's fast-paced world", path="app.ts")[0], 0)

    def test_edit_tool_checks_new_string(self):
        self.assertEqual(run("Unlock the power of X", tool="Edit")[0], 2)

    def test_bypass_env(self):
        payload = json.dumps({"tool_name": "Write", "tool_input": {"file_path": "a.md", "content": "Great question!"}})
        env = dict(os.environ, DISABLE_ANTI_SLOP_HOOK="1")
        p = subprocess.run(["python3", HOOK], input=payload, capture_output=True, text=True, env=env)
        self.assertEqual(p.returncode, 0)

    def test_skip_paths_env(self):
        payload = json.dumps({"tool_name": "Write", "tool_input": {"file_path": "/v/_ledger/x.md", "content": "Great question!"}})
        env = dict(os.environ, DESLOP_SKIP_PATHS="_ledger/")
        p = subprocess.run(["python3", HOOK], input=payload, capture_output=True, text=True, env=env)
        self.assertEqual(p.returncode, 0)

    def test_own_docs_pass_the_gate(self):
        docs = [
            os.path.join(DESLOP, "SKILL.md"),
            os.path.join(DESLOP, "README.md"),
            os.path.join(DESLOP, "agents", "slop-detector.md"),
            os.path.join(DESLOP, "agents", "copy-humanizer.md"),
        ]
        for skill in ("qa-review", "product-review"):
            base = os.path.join(ROOT, "skills", "engineering", skill)
            for dirpath, _, files in os.walk(base):
                for f in files:
                    if f.endswith(".md"):
                        docs.append(os.path.join(dirpath, f))
        docs.append(os.path.join(ROOT, "README.md"))
        docs.append(os.path.join(ROOT, "CLAUDE.md"))
        for d in docs:
            if not os.path.exists(d):
                continue
            with self.subTest(os.path.relpath(d, ROOT)):
                # A neutral path so the skip list cannot exempt the file.
                with open(d, encoding="utf-8") as fh:
                    text = fh.read()
                code, err = run(text, path="/check/" + os.path.basename(d))
                self.assertEqual(code, 0, err)


if __name__ == "__main__":
    unittest.main()
