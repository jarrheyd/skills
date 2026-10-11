import json
import os
import subprocess
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
HOOK = os.path.join(ROOT, "skills", "writing", "deslop", "hooks", "design_slop_hook.py")


def run(content, path="page.html"):
    payload = json.dumps({"tool_name": "Write", "tool_input": {"file_path": path, "content": content}})
    p = subprocess.run(["python3", HOOK], input=payload, capture_output=True, text=True)
    return p.returncode, p.stderr


BLOCKS = [
    ("ai purple", "a{color:#8b5cf6}"),
    ("chatgpt gradient", "a{background:linear-gradient(#667eea,#764ba2)}"),
    ("gradient text", "h1{-webkit-background-clip:text}"),
    ("glass", ".card{backdrop-filter:blur(10px)}"),
    ("left accent", ".card{border-left:4px solid red}"),
    ("generic shadow", ".card{box-shadow:0 1px 3px rgba(0,0,0,0.1)}"),
    ("hairline", ".card{border:1px solid rgba(0,0,0,.05)}"),
    ("blur blob", ".blob{filter:blur(40px)}"),
    ("drop shadow", ".x{filter:drop-shadow(0 0 2px #000)}"),
    ("inter", "body{font-family:Inter,sans-serif}"),
    ("lucide", '<i data-lucide="check"></i>'),
    ("heading bar", "h2{border-bottom:2px solid #000}"),
    ("hr", "<p>a</p><hr><p>b</p>"),
    ("overgradient", "a{background:linear-gradient(red,blue)} b{background:radial-gradient(red,blue)} c{background:conic-gradient(red,blue)} d{background:linear-gradient(red,blue)}"),
]

PASSES = [
    ("brand blue", "a{color:#0077FF}"),
    ("one gradient", "a{background:linear-gradient(#0077FF,#004db3)}"),
    ("real shadow", ".card{box-shadow:0 2px 0 #1a1a1a}"),
    ("hex border", ".card{border:1px solid #E7E2DA}"),
    ("separator hr", '<hr role="separator">'),
    ("heading no bar", "h2{font-weight:700;margin-top:32px}"),
    ("non design file", ".x{color:#8b5cf6}"),
]


class DesignHook(unittest.TestCase):
    def test_blocks(self):
        for name, text in BLOCKS:
            with self.subTest(name):
                code, err = run(text)
                self.assertEqual(code, 2, f"{name!r} should block; stderr: {err}")

    def test_passes(self):
        for name, text in PASSES:
            with self.subTest(name):
                path = "notes.md" if name == "non design file" else "page.html"
                code, err = run(text, path)
                self.assertEqual(code, 0, f"{name!r} should pass; stderr: {err}")

    def test_report_builders_pass(self):
        for rel in ("skills/engineering/qa-review/scripts/build-report.mjs", "skills/engineering/product-review/scripts/build-review.mjs"):
            with self.subTest(rel):
                with open(os.path.join(ROOT, rel), encoding="utf-8") as fh:
                    text = fh.read()
                code, err = run(text, path="report.html")
                self.assertEqual(code, 0, err)


if __name__ == "__main__":
    unittest.main()
