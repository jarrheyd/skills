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
    ("eyebrow class", '<p class="eyebrow">The problem</p><h2>Payroll runs late</h2>'),
    ("eyebrow class jsx", '<span className="hero-kicker">New</span>'),
    ("eyebrow css", ".eyebrow { font-size: 12px; }"),
    ("mui overline", '<Typography variant="overline">Pricing</Typography>'),
    ("all caps label over heading", "<p>THE PROBLEM</p>\n  <h2>Payroll runs late</h2>"),
    ("tailwind uppercase over heading", '<p className="text-xs uppercase tracking-widest">Command center</p>\n<h1>Today</h1>'),
    ("inline uppercase over heading", '<span style="text-transform: uppercase">Step one</span><h3>Pick a plan</h3>'),
    ("overgradient", "a{background:linear-gradient(red,blue)} b{background:radial-gradient(red,blue)} c{background:conic-gradient(red,blue)} d{background:linear-gradient(red,blue)}"),
    ("announce pill", '<span class="pill">Introducing Acme 2.0</span>'),
    ("announce pill tailwind", '<a className="rounded-full px-3 text-xs"><b>New:</b> agents</a>'),
    ("status pulse", '<span class="dot animate-pulse"></span> All systems operational'),
    ("cursor glow", "<script>el.addEventListener('mousemove',e=>{})</script><style>.g{background:radial-gradient(600px at var(--x) var(--y),#fff,transparent)}</style>"),
    ("vanity stat", '<div class="stat">10M+ <small>users</small></div>'),
    ("numbered label", "<p>01 / Features</p><h2>Built for teams</h2>"),
    ("icon tiles", '<div class="icon">a</div><h3>A</h3><div class="icon">b</div><h3>B</h3><div class="icon-box">c</div><h3>C</h3>'),
    ("nested cards", ".card .card{padding:12px}"),
    ("tw purple gradient", '<div className="bg-gradient-to-r from-purple-500 to-blue-500">x</div>'),
    ("indigo hex", "a{color:#4f46e5}"),
    ("tw inter", '<body className="font-inter">'),
    ("inter link", '<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400" rel="stylesheet">'),
    ("next font inter", "import { Inter } from 'next/font/google'"),
    ("tw gradient text", '<h1 className="bg-gradient-to-r from-sky-500 to-teal-400 bg-clip-text text-transparent">Hi</h1>'),
    ("tw glass card", '<div className="backdrop-blur-md bg-white/10 border">x</div>'),
    ("tw side stripe", '<div className="border-l-4 border-sky-500 pl-4">x</div>'),
    ("tw halo", '<div className="absolute h-96 w-96 rounded-full blur-3xl"></div>'),
    ("launch copy", "<h1>Supercharge your workflow</h1>"),
    ("tw icon tiles", '<div className="h-12 w-12 rounded-xl">a</div><h3>A</h3><div className="h-12 w-12 rounded-xl">b</div><h3>B</h3><div className="h-12 w-12 rounded-xl">c</div><h3>C</h3>'),
    ("three cards", '<div class="card"><h3>A</h3><p>x</p></div><div class="card"><h3>B</h3><p>y</p></div><div class="card"><h3>C</h3><p>z</p></div>'),
    ("tw nested cards", '<div className="rounded-2xl border p-6"><div className="rounded-xl border p-4">x</div></div>'),
    ("tw cursor glow", "<div onMouseMove={m} style={{background:`radial-gradient(600px at ${x}px ${y}px, #fff, transparent)`}}/>"),
    ("beige italic serif", "<body style=\"background:#f5efe6\"><h1 style=\"font-family:'Instrument Serif';font-style:italic\">Slow</h1>"),
]

PASSES = [
    ("brand blue", "a{color:#0077FF}"),
    ("one gradient", "a{background:linear-gradient(#0077FF,#004db3)}"),
    ("real shadow", ".card{box-shadow:0 2px 0 #1a1a1a}"),
    ("hex border", ".card{border:1px solid #E7E2DA}"),
    ("separator hr", '<hr role="separator">'),
    ("heading no bar", "h2{font-weight:700;margin-top:32px}"),
    ("label over a value", '<small class="text-muted">Nickname</small><h4>Ja</h4>'),
    ("dynamic badge over heading", '<span className="uppercase">{stage.name}</span><h2>{title}</h2>'),
    ("caps text not before heading", "<p>FAQ</p><p>Ask us anything.</p>"),
    ("sentence case date over heading", '<p class="date">Oct 21</p><h2>Release notes</h2>'),
    ("uppercase element after heading", '<h2>Plans</h2><p class="uppercase">Monthly</p>'),
    ("kicker word in copy", "<p>The kicker is the price.</p>"),
    ("non design file", ".x{color:#8b5cf6}"),
    ("skeleton loader pulse", '<div class="h-4 w-32 animate-pulse bg-stone-200"></div>'),
    ("real count in copy", "<p>We moved 12M rows last night.</p>"),
    ("plain badge", '<span class="badge">Beta</span>'),
    ("numbered list item", "<li>01 Install</li><li>02 Run</li>"),
    ("one icon over heading", '<div class="icon">a</div><h3>Settings</h3>'),
    ("mousemove without glow", "<script>el.addEventListener('mousemove',drag)</script>"),
    ("card list", ".card{padding:16px} .card h3{margin:0}"),
    ("card child class", ".pbk-card .card-sub{color:#555}"),
    ("modal overlay blur", '<div className="fixed inset-0 bg-black/50 backdrop-blur-sm"></div>'),
    ("career next level", "<p>three real cases at the next level</p>"),
    ("form sections", '<div className="space-y-2"><h3>Chief complaint</h3><p>x</p></div><div className="space-y-2"><h3>History</h3><p>y</p></div><div className="space-y-2"><h3>Plan</h3><p>z</p></div>'),
    ("helper text under heading", '<h3>Activity</h3><p className="text-xs text-neutral-500">Visible to clinic staff only.</p>'),
    ("tw left padding only", '<div className="border-l pl-4">quote</div>'),
    ("bare post number", '<span class="post-num">01</span><h3 class="post-title">think in context</h3>'),
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

    def test_functional_gradients_do_not_count_as_decoration(self):
        css = """
        .fade { mask-image: linear-gradient(#000 70%,transparent); -webkit-mask-image: linear-gradient(#000,transparent); }
        .hatch { background: repeating-linear-gradient(135deg,color-mix(in srgb,var(--c) 30%,transparent) 0 3px,transparent 3px 7px); }
        select { background: linear-gradient(45deg,transparent 50%,var(--ink) 50%),linear-gradient(135deg,var(--ink) 50%,transparent 50%); background-size:5px 5px; }
        .ring { background:conic-gradient(var(--c,var(--app)) calc(var(--p)*1%),var(--sunk) 0); }
        .progress { background:linear-gradient(90deg,var(--app) calc(var(--p) * 100%),var(--line) 0); }
        .corner { background:linear-gradient(225deg,var(--warn) 0 6px,transparent 6px); }
        .cost { height:3px; background:linear-gradient(90deg,var(--bad),var(--good)); }
        """
        code, err = run(css, 'functional.css')
        self.assertEqual(code, 0, err)

    def test_functional_gradients_do_not_hide_four_decorative_gradients(self):
        decorative = ' '.join(f'.hero{i} {{background:linear-gradient(red,blue)}}' for i in range(4))
        code, err = run('.mask{mask-image:linear-gradient(#000,transparent)}' + decorative, 'page.css')
        self.assertEqual(code, 2)
        self.assertIn('overgradient (4 gradients)', err)

    def test_soft_repeating_gradients_and_unrelated_thin_rules_still_count(self):
        css = '.line{height:3px}' + ' '.join(f'.hero{i} {{background:repeating-linear-gradient(red 0px,blue 10px)}}' for i in range(4))
        code, err = run(css, 'page.css')
        self.assertEqual(code, 2)
        self.assertIn('overgradient (4 gradients)', err)

    def test_report_builders_pass(self):
        for rel in ("skills/engineering/qa-review/scripts/build-report.mjs", "skills/engineering/product-review/scripts/build-review.mjs"):
            with self.subTest(rel):
                with open(os.path.join(ROOT, rel), encoding="utf-8") as fh:
                    text = fh.read()
                code, err = run(text, path="report.html")
                self.assertEqual(code, 0, err)


if __name__ == "__main__":
    unittest.main()
