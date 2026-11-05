#!/usr/bin/env python3
"""
Design AI-Slop Hook for Claude Code - companion to copy_slop_hook.py.

Scans HTML/CSS/JSX source on Write/Edit for AI-DEFAULT visual design tells and BLOCKS them.
Targets the signatures intentional brand design does NOT use, so on-brand work (cobalt/cyan,
hex borders, a real typeface, a single purposeful gradient) passes, while the AI defaults get
stopped: AI purple, the ChatGPT gradient, gradient text, glassmorphism, left-border accent
cards, the generic rgba(0,0,0,0.1) shadow, ultra-faint card outlines, decorative blur blobs,
Inter-as-default, overgradient, and eyebrow labels above headings.

Everything here blocks; there is no warn tier. Bypass a session with DISABLE_ANTI_SLOP_HOOK=1.

Exit codes: 0 = allow, 2 = block.
"""

import json
import os
import re
import sys
try: __import__('sys').path.insert(0, __import__('os').path.expanduser('~/.claude/hooks')); __import__('hooklog').install('design_slop')  # fire log for the experiments (10-26)
except Exception: pass

DESIGN_EXTS = {".html", ".htm", ".css", ".scss", ".tsx", ".jsx", ".vue", ".svelte"}

SKIP = [
    "node_modules", "deslop/", "dist/", "build/", ".next/",
    "design-system/references/", "brand-system/references/",
]

def relevant(fp):
    if not fp or any(s in fp for s in SKIP) or ".min." in os.path.basename(fp):
        return False
    return os.path.splitext(fp)[1].lower() in DESIGN_EXTS


# (regex, message) - each match is a BLOCK.
TELLS = [
    (r"(?i)#(?:8b5cf6|a855f7|7c3aed|6d28d9|9333ea|7e22ce|c084fc|a78bfa|818cf8|6366f1)\b",
     "AI purple palette (#8b5cf6 / #a855f7 / indigo...) - the default AI accent; choose a color with brand intent"),
    (r"(?i)#(?:667eea|764ba2)\b",
     "the ChatGPT purple-blue gradient (#667eea / #764ba2) - the single most recognizable AI gradient"),
    (r"(?i)(?:-webkit-)?background-clip\s*:\s*text",
     "gradient text (background-clip: text) - a strong AI landing-page tell"),
    (r"(?i)backdrop-filter\s*:\s*blur",
     "glassmorphism (backdrop-filter: blur) - AI-default frosted glass; use a solid surface with intent"),
    (r"(?i)border-left\s*:\s*[3-8]px\s+solid",
     "left-border accent stripe (border-left: 3-8px solid) - the generic 'accent card' move"),
    (r"(?i)box-shadow\s*:[^;{}]*rgba\(\s*0\s*,\s*0\s*,\s*0\s*,\s*0?\.1\d?\s*\)",
     "the generic AI shadow rgba(0,0,0,0.1) - use a real, brand-derived shadow or none"),
    (r"(?i)border\s*:\s*1px\s+solid\s+rgba\([^)]*,\s*0?\.0[0-8]\s*\)",
     "ultra-faint hairline card border (rgba alpha <= .08) - the invisible AI card outline"),
    (r"(?i)filter\s*:\s*blur\(\s*[2-9]\dpx",
     "decorative blur blob (filter: blur >= 20px) - AI background decoration; delete it"),
    (r"(?i)filter\s*:\s*drop-shadow",
     "drop-shadow filter - AI-default depth; use a real, brand-derived shadow or none"),
    (r"(?i)font-family\s*:[^;{}]*\b(?:Inter|Geist|Space\s+Grotesk)\b",
     "Inter / Geist / Space Grotesk - the default AI UI typefaces; choose type with intent"),
    (r"(?i)\blucide(?:-react|-icons?)?\b|data-lucide",
     "Lucide icons - the default AI icon set; pick icons that fit the brand"),
    (r'(?i)class(?:Name)?\s*=\s*["\'][^"\']*\b(?:terminal|code-window|window-dots|traffic-lights?)\b',
     "fake terminal-window mockup - an overused AI landing-page prop"),
    (r"(?is)\bh[1-6]\s*(?:,[^{}]*)?\{[^{}]*border-bottom\s*:",
     "bar line under a heading (h1-h6 with border-bottom) - the AI section-divider rule; let the heading's weight and spacing carry it, no underline bar"),
    (r"(?i)#(?:4f46e5|4338ca|5b21b6|3730a3)\b",
     "AI indigo (#4f46e5 / #4338ca) - Tailwind's default button color, the reason AI sites lean purple; choose a color with brand intent"),
    (r"(?i)\bfrom-(?:purple|violet|indigo|fuchsia)-\d{2,3}\b|\b(?:via|to)-(?:purple|violet|indigo|fuchsia)-\d{2,3}\b",
     "Tailwind purple / indigo gradient (from-purple-500 to-blue-500) - the AI hero gradient; one brand color with intent"),
    (r"(?i)\bfont-(?:inter|geist)\b|family=(?:Inter|Geist|Space\+Grotesk)\b|import\s*\{[^}]*\b(?:Inter|Geist|Space_Grotesk)\b[^}]*\}\s*from\s*[\"'](?:next/font|geist)",
     "Inter / Geist loaded as the page font (class, Google Fonts link or next/font) - the default AI typeface; choose type with intent"),
    (r"\bbg-clip-text\b",
     "gradient text (bg-clip-text) - a strong AI landing-page tell"),
    (r"(?i)class(?:Name)?\s*=\s*[\"'{`](?=[^\"'`}]*\bbackdrop-blur)(?=[^\"'`}]*\bbg-white/\d)",
     "glassmorphism (backdrop-blur on a see-through white card) - AI-default frosted glass; use a solid surface with intent"),
    (r"\bborder-l-(?:[3-8])\b",
     "left-border accent stripe (border-l-4) - the generic 'accent card' move"),
    (r"\bblur-(?:2xl|3xl|\[(?:[2-9]\d|\d{3})px\])\b",
     "decorative blur blob or halo (blur-3xl) - AI background decoration; delete it"),
    (r"(?i)\b(?:supercharge|turbocharge|unleash|revolutioni[sz]e|game[- ]chang(?:er|ing)|elevate your)\b",
     "AI launch-page copy ('supercharge your workflow') - say what it does in plain words"),
    (r"(?i)<hr\b(?![^>]*\brole\s*=\s*[\"']?separator)",
     "decorative <hr> rule - AI section-divider furniture; use whitespace and heading hierarchy instead of a bar"),
]


# Eyebrow / kicker: a short label line stuck above a heading. Matched narrowly so
# ordinary markup passes: an explicit eyebrow-style class name, or a short element directly
# before an <h1>-<h6> that is set uppercase or written in ALL CAPS. A dynamic value ({...}) and a
# plain small label over a value (Nickname over a name) pass: those carry information.
EYEBROW_CLASS = re.compile(
    r"(?i)(?:class(?:Name)?\s*=\s*[\"'{`][^>]*?\b|^\s*\.)(?:eyebrow|kicker|overline|pretitle|supertitle)\b"
    r"|\bvariant\s*=\s*[\"'{]?\s*[\"']?overline\b",
    re.M,
)
LABEL_BEFORE_HEADING = re.compile(
    r"(?is)<(p|span|div|small|label|strong|em|b)\b([^>]*)>\s*([^<]{1,40}?)\s*</\1>\s*<h[1-6]\b"
)


def eyebrow(content):
    if EYEBROW_CLASS.search(content):
        return ["eyebrow / kicker class (eyebrow, kicker, overline, pretitle) - a label line over a heading; delete it, the heading carries itself"]
    for m in LABEL_BEFORE_HEADING.finditer(content):
        attrs, text = m.group(2), m.group(3)
        if "{" in text:
            continue
        letters = re.sub(r"[^A-Za-z]", "", text)
        all_caps = len(letters) >= 3 and letters.isupper()
        styled = re.search(r"(?i)\buppercase\b|text-transform\s*:\s*uppercase|textTransform", attrs)
        if all_caps or styled:
            return [f"eyebrow above a heading ('{text.strip()[:30]}') - a small or uppercase label line over a heading; delete it, the heading carries itself"]
    return []


# Tells from Impeccable's slop catalog (impeccable.style/slop) and Ridd's portfolio reviews,
# added 11-02 after his saved reels. Each needs two signals together so ordinary markup passes:
# a skeleton loader may pulse, a stats page may say 10M, a docs page may number its steps.
ANNOUNCE_PILL = re.compile(
    r"(?is)<(span|div|a|p|button)\b[^>]*class(?:Name)?\s*=\s*[\"'{`][^>]*?\b(?:pill|badge|chip|rounded-full)\b[^>]*>"
    r"\s*(?:<[^>]+>\s*)*[^<\w]{0,4}(?:introducing|announcing|new\s*:)"
)
STATUS_COPY = re.compile(r"(?i)all\s+systems\s+(?:operational|go|normal)|systems?\s+(?:are\s+)?(?:online|operational)")
PULSE = re.compile(r"(?i)\banimate-pulse\b|animation(?:-name)?\s*:[^;{}]*\bpulse\b")
VANITY_STAT = re.compile(r"(?i)>\s*\d+(?:[.,]\d+)?\s*[KMB]\+\s*<")
NUMBERED_LABEL = re.compile(
    r"(?is)>\s*0[1-9]\s*[^\w\s<]\s*[A-Za-z][^<]{0,30}</\w+>\s*(?:<\w+\b[^>]*>[^<]{0,40}</\w+>\s*)?<h[1-6]\b"
)
ICON_TILE = re.compile(
    r"(?is)<(div|span)\b[^>]*class(?:Name)?\s*=\s*[\"'{`](?:[^\"'`}]*\bicon[\w-]*\b|(?=[^\"'`}]*\b(?:h|w|size)-(?:8|9|1[0-6])\b)(?=[^\"'`}]*\brounded-(?:md|lg|xl|2xl)\b))[^>]*>(?:(?!</\1>).){0,200}</\1>\s*<h[2-4]\b"
)
CARD_TRIPLET = re.compile(
    r"(?is)(<(div|article|li)\b[^>]*class(?:Name)?\s*=\s*([\"'])((?=[^\"']*\b(?:card|feature|tile|rounded(?:-\w+)?|border|shadow(?:-\w+)?)\b)[^\"']+)\3[^>]*>\s*(?:<[^>]+>\s*){0,3}<h[2-4]\b[^>]*>[^<]{1,60}</h[2-4]>\s*<p\b[^>]*>[^<]{1,200}</p>\s*(?:</[^>]+>\s*){0,3}</\2>\s*)"
    r"<\2\b[^>]*class(?:Name)?\s*=\s*\3\4\3[^>]*>(?:(?!</\2>).){0,400}</\2>\s*<\2\b[^>]*class(?:Name)?\s*=\s*\3\4\3"
)
NESTED_CARD_TW = re.compile(
    r"(?is)class(?:Name)?\s*=\s*[\"'](?=[^\"']*\brounded-(?:lg|xl|2xl|3xl)\b)(?=[^\"']*\bborder\b)[^\"']*[\"'][^>]*>\s*<div\b[^>]*class(?:Name)?\s*=\s*[\"'](?=[^\"']*\brounded-(?:md|lg|xl|2xl)\b)(?=[^\"']*\bborder\b)"
)
BEIGE = re.compile(r"(?i)#(?:f5efe6|f4ede[0-9a-f]|f5f0e[0-9a-f]|faf[5-8]f[0-2]|f7f3e[0-9a-f]|efe9df|f2ece[0-9a-f]|fbf8f3)\b|\bbg-(?:stone|amber)-(?:50|100)\b")
NEAR_BLACK = re.compile(r"(?i)background(?:-color)?\s*:\s*#(?:000|000000|0a0a0a|0b0b0b|0c0c0c|0d0d0d|0f0f0f|111|111111|121212)\b|\bbg-(?:black|neutral-950|zinc-950|stone-950)\b")
ITALIC_SERIF = re.compile(r"(?is)(?:Instrument\s*Serif|Playfair|Fraunces|DM\s*Serif|Cormorant|EB\s*Garamond|Newsreader)[^{}]{0,200}?(?:font-style\s*:\s*italic|\bitalic\b)|(?:font-style\s*:\s*italic|\bitalic\b)[^{}]{0,200}?(?:Instrument\s*Serif|Playfair|Fraunces|DM\s*Serif|Cormorant|EB\s*Garamond|Newsreader)|\bfont-serif\b[^\"']*\bitalic\b|\bitalic\b[^\"']*\bfont-serif\b")


def has_brand_system(fp):
    """A project that wrote down its own look (DESIGN-SYSTEM.md / BRAND-SYSTEM.md) chose its palette on purpose."""
    d = os.path.dirname(os.path.abspath(fp or "."))
    for _ in range(8):
        if any(os.path.exists(os.path.join(d, n)) for n in ("DESIGN-SYSTEM.md", "BRAND-SYSTEM.md", "DESIGN.md")):
            return True
        up = os.path.dirname(d)
        if up == d:
            break
        d = up
    return False
NESTED_CARD_CSS = re.compile(r"(?i)\.(card|panel|tile)(?![\w-])[^{},]*?\s\.\1(?![\w-])")


def catalog_tells(content, fp=""):
    hits = []
    if ANNOUNCE_PILL.search(content):
        hits.append("'Introducing' pill badge over the hero - the AI launch-page opener; say the news in the headline or cut it")
    if PULSE.search(content) and STATUS_COPY.search(content):
        hits.append("pulsing 'all systems operational' dot - AI landing-page decoration; show status only where a real status feed backs it")
    if re.search(r"(?i)\bmousemove\b|onMouseMove|pointermove|onPointerMove", content) and re.search(r"(?i)radial-gradient\([^)]*(?:var\(--|\$\{|clientX|mouse)", content):
        hits.append("glow that follows the cursor - the first hover effect AI hands out; cut it")
    if VANITY_STAT.search(content):
        hits.append("giant '10M+' stat with a tiny label - AI vanity number; use a real, sourced number in a sentence or drop it")
    if NUMBERED_LABEL.search(content):
        hits.append("'01 / 02 / 03' section label over a heading - AI section numbering; let the heading carry the section")
    if len(ICON_TILE.findall(content)) >= 3:
        hits.append("icon tile above every heading (3+ times) - the AI feature-grid pattern; drop the tiles or vary the layout")
    if NESTED_CARD_CSS.search(content) or NESTED_CARD_TW.search(content):
        hits.append("cards inside cards - AI nesting; flatten to one surface")
    if CARD_TRIPLET.search(content):
        hits.append("three identical feature cards (same class, heading plus one line each) - the AI feature grid; vary them or say it in a sentence")
    if BEIGE.search(content) and ITALIC_SERIF.search(content) and not has_brand_system(fp):
        hits.append("beige background with a fancy italic serif - the 2025 AI 'tasteful' default; pick type and color from a real brand, or write a DESIGN-SYSTEM.md that says why")
    elif NEAR_BLACK.search(content) and ITALIC_SERIF.search(content) and not has_brand_system(fp):
        hits.append("near-black background with a big italic serif - the 'Claude look' trying to seem expensive; pick type and color from a real brand, or write a DESIGN-SYSTEM.md that says why")
    return hits


def css_parts(value, separator=','):
    """Split CSS arguments or words without splitting nested functions or quoted strings."""
    out, start, depth, quote, escaped = [], 0, 0, None, False
    for i, char in enumerate(value):
        if escaped:
            escaped = False
            continue
        if char == "\\":
            escaped = True
        elif quote:
            if char == quote:
                quote = None
        elif char in "\"'":
            quote = char
        elif char == '(':
            depth += 1
        elif char == ')':
            depth -= 1
        elif depth == 0 and (char == separator if separator else char.isspace()):
            if value[start:i].strip():
                out.append(value[start:i].strip())
            start = i + 1
    if value[start:].strip():
        out.append(value[start:].strip())
    return out


def hard_stops(body):
    stops = css_parts(body)
    if stops and re.match(r"(?i)^(?:to\b|from\b|at\b|circle\b|ellipse\b|[+-]?[\d.]+(?:deg|turn|rad|grad)\b)", stops[0]):
        stops = stops[1:]
    if len(stops) < 2:
        return False
    end = None
    for stop in stops:
        positions = css_parts(stop, None)[1:]
        if not positions or (end is not None and positions[0] not in (end, '0')):
            return False
        end = positions[-1]
    return True


def overgradient(content):
    content = re.sub(r"/\*[\s\S]*?\*/", '', content)
    n = 0
    for match in re.finditer(r"(?i)(?:repeating-)?(?:linear|radial|conic)-gradient\(", content):
        start, depth, end = match.end(), 1, match.end()
        while end < len(content) and depth:
            depth += (content[end] == '(') - (content[end] == ')')
            end += 1
        declaration = content[max(content.rfind(c, 0, match.start()) for c in ';{}') + 1:match.start()]
        prop = re.match(r"\s*([-\w]+)\s*:", declaration)
        if prop and prop[1].lower() in ('mask', 'mask-image', '-webkit-mask', '-webkit-mask-image'):
            continue
        rule = content[content.rfind('{', 0, match.start()) + 1:content.find('}', end) if '}' in content[end:] else end]
        thin = any(0 < float(v) <= 4 for v in re.findall(r"(?i)(?:^|;)\s*(?:height|width)\s*:\s*((?:\d+(?:\.\d+)?|\.\d+))px\b", rule))
        if thin or (depth == 0 and hard_stops(content[start:end - 1])):
            continue
        n += 1
    if n >= 4:
        return [f"overgradient ({n} gradients) - gradients used as decoration; a brand uses one with purpose, not four"]
    return []


def extract(tool, ti):
    if tool == "Write":
        return ti.get("content", "")
    if tool == "Edit":
        return ti.get("new_string", "")
    if tool == "MultiEdit":
        return "\n".join(e.get("new_string", "") for e in ti.get("edits", []))
    return ""


def main():
    if os.environ.get("DISABLE_ANTI_SLOP_HOOK", "0") == "1":
        sys.exit(0)
    try:
        data = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, ValueError):
        sys.exit(0)
    tool = data.get("tool_name", "")
    ti = data.get("tool_input", {})
    if tool not in ("Write", "Edit", "MultiEdit"):
        sys.exit(0)
    fp = ti.get("file_path", "")
    if not relevant(fp):
        sys.exit(0)
    content = extract(tool, ti)
    if not content:
        sys.exit(0)

    hits = [msg for rx, msg in TELLS if re.search(rx, content)]
    hits += overgradient(content)
    hits += eyebrow(content)
    hits += catalog_tells(content, fp)

    if hits:
        parts = [f"Design AI-Slop BLOCKED - {len(hits)} tell(s) in {os.path.basename(fp)}:\n"]
        for m in hits[:8]:
            parts.append(f"  - {m}")
        if len(hits) > 8:
            parts.append(f"\n  ... and {len(hits) - 8} more.")
        parts.append("\nThese are AI-default visual tells. Design with brand intent. See: ~/.claude/skills/deslop/references/design-slop-patterns.md")
        print("\n".join(parts), file=sys.stderr)
        sys.exit(2)

    sys.exit(0)


if __name__ == "__main__":
    main()
