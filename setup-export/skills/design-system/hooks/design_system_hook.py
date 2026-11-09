#!/usr/bin/env python3
"""
Design System Enforcement Hook for Claude Code

PreToolUse hook that validates Write/Edit operations against the project's
DESIGN-SYSTEM.md. Three enforcement layers:
1. Token violations (hardcoded colors, magic spacing, wrong radii)
2. AI slop patterns (generic copy, stock patterns, uncustomized components)
3. Component gatekeeper (blocks raw card/layout patterns in page files when components should exist)
4. System existence check (warns if project has no DESIGN-SYSTEM.md)

Exit codes:
  0 = allow (no violations or non-UI file)
  2 = block (violation found, show warning)
"""

import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

DEBUG_LOG_FILE = "/tmp/design-system-hook-log.txt"


def debug_log(message):
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(DEBUG_LOG_FILE, "a") as f:
            f.write(f"[{timestamp}] {message}\n")
    except Exception:
        pass


# File patterns that should be checked
UI_FILE_PATTERNS = [
    # Web
    "/components/",
    "/app/",
    "/pages/",
    "/views/",
    "/screens/",
    "page.tsx",
    "layout.tsx",
    "loading.tsx",
    # SwiftUI
    "/Sources/",
    "/Features/",
    "/Core/",
    "View.swift",
    "Screen.swift",
    "Components.swift",
]

SKIP_PATTERNS = [
    "globals.css",
    "DESIGN-SYSTEM.md",
    "tailwind.config",
    "postcss.config",
    ".env",
    "node_modules",
    "/api/",
    "/server/",
    "/lib/ai/",
    "/inngest/",
    "/lib/firebase/",
    "/lib/integrations/",
    "/lib/supabase/",
    "/trpc/",
    # iOS
    "Info.plist",
    ".entitlements",
    "GoogleService-Info",
    "/Resources/Assets",
    "AppColors.swift",   # Token definitions use raw Color() values
    "AppDesign.swift",   # Animation presets
]

# ============================================================
# 1. TOKEN VIOLATIONS
# ============================================================

HARDCODED_COLOR_PATTERNS = [
    (r'className=["\'][^"\']*(?:#[0-9a-fA-F]{3,8})', "hardcoded hex color in className"),
    (r'style=\{\{[^}]*color:\s*["\']#[0-9a-fA-F]', "hardcoded hex color in inline style"),
    (r'style=\{\{[^}]*color:\s*["\']rgb\(', "hardcoded rgb() in inline style"),
    (r'(?:bg|text|border|ring|fill|stroke)-\[#[0-9a-fA-F]+\]', "arbitrary Tailwind color — use a design token"),
    (r'(?:bg|text|border|ring|fill|stroke)-\[rgb', "arbitrary Tailwind rgb color — use a design token"),
]

MAGIC_SPACING_PATTERNS = [
    (r'(?:p|px|py|pt|pb|pl|pr|m|mx|my|mt|mb|ml|mr|gap|space-[xy])-\[(\d+)(?:px|rem)\]', "magic_spacing"),
]
VALID_SPACING_PX = {0, 1, 2, 4, 6, 8, 10, 12, 14, 16, 20, 24, 28, 32, 36, 40, 48, 56, 64, 80, 96}

TYPOGRAPHY_PATTERNS = [
    (r'text-\[(\d+)px\]', "magic_font_size"),
]
VALID_FONT_SIZES_PX = {10, 11, 12, 13, 14, 16, 18, 20, 24, 30, 36, 48}

VISUAL_LANGUAGE_PATTERNS = [
    (r'(?:bg-card|border-border)[^"\']*shadow-(?:md|lg|xl|2xl)', "heavy shadow on card — use border only, shadow-sm on hover max"),
    (r'\bdark:', "dark mode class — check if this project supports dark mode in DESIGN-SYSTEM.md"),
]

# ============================================================
# 1b. SWIFTUI TOKEN VIOLATIONS
# ============================================================

SWIFT_COLOR_PATTERNS = [
    (r'\.foregroundColor\(\s*\.white\s*\)', "hardcoded .white — use design token (.appBackground)"),
    (r'\.foregroundColor\(\s*\.black\s*\)', "hardcoded .black — use design token (.appText)"),
    (r'\.foregroundColor\(\s*\.gray\s*\)', "hardcoded .gray — use design token (.appTextSecondary)"),
    (r'\.foregroundStyle\(\s*\.white\s*\)', "hardcoded .white — use design token"),
    (r'\.foregroundStyle\(\s*\.black\s*\)', "hardcoded .black — use design token"),
    (r'\.background\(\s*Color\.white\s*\)', "hardcoded Color.white — use design token"),
    (r'\.background\(\s*Color\.black\s*\)', "hardcoded Color.black — use design token"),
    (r'Color\(\s*red:', "hardcoded Color(red:green:blue:) — define in design system"),
    (r'UIColor\.\s*(?:black|white|gray|systemGray)\b', "hardcoded UIColor — use design token"),
]

SWIFT_SPACING_PATTERNS = [
    # .padding(N) where N is a single number
    (r'\.padding\(\s*(\d+)\s*\)', "swift_spacing"),
    # .padding(.direction, N)
    (r'\.padding\(\s*\.\w+\s*,\s*(\d+)\s*\)', "swift_spacing"),
    # Spacer().frame(height: N) or .frame(width: N) used as spacing
    (r'Spacer\(\)\.frame\(\s*(?:height|width)\s*:\s*(\d+)\s*\)', "swift_spacing"),
]
# Valid SwiftUI spacing values per the app design system
VALID_SWIFT_SPACING = {0, 4, 8, 12, 16, 24, 32}

SWIFT_RADIUS_PATTERNS = [
    (r'\.cornerRadius\(\s*(\d+(?:\.\d+)?)\s*\)', "swift_radius"),
    (r'RoundedRectangle\(\s*cornerRadius\s*:\s*(\d+(?:\.\d+)?)\s*\)', "swift_radius"),
]
# Valid corner radius values per the app design system: 8 (pills), 12 (cards), 24 (input pill), 2 (status bar)
VALID_SWIFT_RADIUS = {2, 4, 8, 12, 24}

SWIFT_FONT_PATTERNS = [
    (r'\.font\(\s*\.system\(\s*size\s*:\s*(\d+)', "swift_font"),
    (r'Font\.system\(\s*size\s*:\s*(\d+)', "swift_font"),
]
# Minimum font size per design system
SWIFT_MIN_FONT_SIZE = 13

SWIFT_ICON_PATTERNS = [
    # Warn about SF Symbols in empty state contexts (but don't block — could be toolbar icons)
    (r'AppEmptyState\([^)]*icon\s*:', "SF Symbol in empty state — use illustration: parameter with brand illustration instead"),
]

SWIFT_COMPONENT_PATTERNS = [
    # Inline input bars instead of AppInputBar
    (r'TextField\(\s*"message\s+app', "inline TextField for chat — use AppInputBar component"),
    # Inline search instead of AppSearchBar
    (r'TextField\(\s*"[Ss]earch', "inline search TextField — consider AppSearchBar component"),
]

# ============================================================
# 2. AI SLOP PATTERNS
# ============================================================

SLOP_COPY_PATTERNS = [
    # Buzzword slop
    (r'(?i)elevate\s+your', "AI slop: 'elevate your...' — be specific"),
    (r'(?i)unlock\s+the\s+power', "AI slop: 'unlock the power' — what does it actually do?"),
    (r'(?i)in\s+today\'?s\s+fast[- ]paced', "AI slop: 'in today's fast-paced...' — skip throat-clearing"),
    (r'(?i)seamlessly?\s+integrat', "AI slop: 'seamlessly integrate' — describe what it does"),
    (r'(?i)supercharge\s+your', "AI slop: 'supercharge your' — be concrete"),
    (r'(?i)revolutioniz', "AI slop: 'revolutionize' — overused, show don't tell"),
    (r'(?i)game[- ]?changer', "AI slop: 'game-changer' — say what changes"),
    (r'(?i)cutting[- ]?edge', "AI slop: 'cutting-edge' — show don't tell"),
    (r'(?i)next[- ]?level', "AI slop: 'next-level' — empty phrase"),
    (r'(?i)empower\s+(?:your|users|teams)', "AI slop: 'empower your...' — what does it do?"),
    (r'(?i)harness\s+the', "AI slop: 'harness the...' — be direct"),
    (r'(?i)leverage\s+(?:the|your|our)', "AI slop: 'leverage' — just say 'use'"),
    (r'(?i)streamline\s+your', "AI slop: 'streamline your' — how specifically?"),
    (r'(?i)take\s+(?:your|it)\s+to\s+the\s+next', "AI slop: 'take it to the next level'"),
    # Structural slop
    (r'(?i)(?:it\'?s|this\s+is)\s+not\s+just\s+\w+[^.]*\.\s*(?:it\'?s|this\s+is)\s+', "AI slop structure: 'It's not just X. It's Y.' — the #1 AI tell"),
    (r'(?i)not\s+\w+[^.]*[,]\s*but\s+\w+', "AI slop structure: 'Not X, but Y' — rewrite without the contrast crutch"),
    (r'(?i)and\s+that\s+matters', "AI slop: 'And that matters.' — filler closer, cut it"),
    (r'(?i)and\s+honestly\?', "AI slop: 'And honestly?' — LinkedIn filler, cut it"),
    (r'(?i)let\'?s\s+break\s+(?:it|this)\s+down', "AI slop: 'Let's break it down' — just break it down"),
    (r'(?i)here\'?s\s+(?:the\s+thing|why\s+(?:it|that)\s+matters)', "AI slop: 'Here's the thing' — start with the point"),
    (r'(?i)great\s+question!', "AI slop: 'Great question!' — sycophantic, just answer it"),
    (r'(?i)^absolutely!', "AI slop: 'Absolutely!' — forced chipperness"),
    # Adverb abuse
    (r'(?i)quietly\s+(?:revolutionary|devastating|reshaping|powerful|brilliant|transforming)', "AI slop: 'quietly [adjective]' — AI's favorite adverb"),
    # Em dash abuse
    (r'—[^—]*—', "AI slop: multiple em dashes — use commas or periods instead"),
]

SLOP_VISUAL_PATTERNS = [
    (r'(?:from|via|to)-(?:purple|violet|indigo|blue)-(?:400|500|600|700)', "AI default gradient — is this justified by the brand palette?"),
    (r'(?:bg|text|border)-(?:slate|zinc)-(?:100|200|300|400|500|600|700|800|900)', "default Tailwind gray scale — use semantic design tokens instead"),
    (r'style=\{\{', "inline style detected — use design tokens, not inline styles"),
    # Default/forbidden fonts (warn, not block — might be justified)
    (r'font-family:[^;]*(?:Roboto|Arial|system-ui)', "default font detected — is this a deliberate choice? See premium-craft.md"),
    # Noise textures without purpose
    (r'backdrop-filter:\s*blur.*(?:text|heading|title|label)', "blur applied near text — never blur readable text"),
]

# ============================================================
# 3. COMPONENT GATEKEEPER
# Detects raw layout patterns in PAGE files that should be components.
# Only triggers in page/view files, NOT in component files themselves.
# ============================================================

# Patterns that look like they should be a shared component
RAW_COMPONENT_PATTERNS = [
    # Card-like pattern (border + bg + rounded + padding in a raw div)
    (r'<div[^>]*className="[^"]*rounded-(?:xl|2xl|lg)[^"]*border[^"]*bg-',
     "raw card pattern — use a Card component from your design system instead of inline className"),
    # Stat/metric card pattern
    (r'<div[^>]*className="[^"]*rounded[^"]*border[^"]*p-4[^"]*">\s*\n\s*<p[^>]*text-xs',
     "raw stat card pattern — extract to a StatCard component"),
    # Empty state pattern (centered + muted text)
    (r'<div[^>]*className="[^"]*items-center[^"]*justify-center[^"]*py-\d+[^"]*text-(?:sm|center)',
     "raw empty state pattern — use an EmptyState component"),
]


def is_ui_file(file_path):
    if not file_path:
        return False
    is_web = file_path.endswith(".tsx") or file_path.endswith(".jsx")
    is_swift = file_path.endswith(".swift")
    if not (is_web or is_swift):
        return False
    if not any(pattern in file_path for pattern in UI_FILE_PATTERNS):
        return False
    if any(pattern in file_path for pattern in SKIP_PATTERNS):
        return False
    return True


def is_swift_file(file_path):
    return file_path and file_path.endswith(".swift")


def is_page_file(file_path):
    """Check if this is a page/view file (not a component definition)."""
    if "/components/" in file_path:
        return False
    # SwiftUI: Core/Extensions is the component library
    if "/Core/Extensions/" in file_path:
        return False
    return True


def find_project_root(file_path):
    """Walk up from the file to find the project root (has package.json, DESIGN-SYSTEM.md, or .xcodeproj)."""
    current = Path(file_path).parent
    for _ in range(20):  # max 20 levels up
        if (current / "package.json").exists() or (current / "DESIGN-SYSTEM.md").exists():
            return current
        # iOS: look for .xcodeproj
        if any(current.glob("*.xcodeproj")):
            return current
        parent = current.parent
        if parent == current:
            break
        current = parent
    return None


def check_design_system_exists(file_path):
    """Check if the project has a DESIGN-SYSTEM.md. Returns warning message or None."""
    root = find_project_root(file_path)
    if root is None:
        # No project root found — can't determine if DESIGN-SYSTEM.md exists
        return None
    if not (root / "DESIGN-SYSTEM.md").exists():
        return (
            "⚠️ No DESIGN-SYSTEM.md found in project root ({}).\n"
            "Create one using: ~/.claude/skills/design-system/references/design-system-template.md\n"
            "The design system defines your tokens, components, and brand-specific decisions.\n"
            "Without it, the hook can only check universal rules — not your brand's specific system."
        ).format(root)
    return None


# Session state: only warn about missing DESIGN-SYSTEM.md once per session per project
_warned_projects = set()


def check_violations(content, file_path):
    violations = []
    warnings = []

    if not content:
        return violations, warnings

    lines = content.split("\n")
    is_page = is_page_file(file_path)
    is_swift = is_swift_file(file_path)

    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if stripped.startswith("//") or stripped.startswith("import ") or stripped.startswith("*"):
            continue

        if is_swift:
            # ============================================================
            # SWIFTUI CHECKS
            # ============================================================

            # --- SwiftUI Color Violations (blocking) ---
            for pattern, msg in SWIFT_COLOR_PATTERNS:
                if re.search(pattern, line):
                    violations.append((i, f"[TOKEN] {msg}"))
                    break

            # --- SwiftUI Spacing Violations (blocking) ---
            for pattern, vtype in SWIFT_SPACING_PATTERNS:
                match = re.search(pattern, line)
                if match and vtype == "swift_spacing":
                    val = int(match.group(1))
                    if val not in VALID_SWIFT_SPACING and val > 0:
                        violations.append((i, f"[TOKEN] Spacing {val}pt not in scale — use {sorted(VALID_SWIFT_SPACING)}"))

            # --- SwiftUI Corner Radius Violations (blocking) ---
            for pattern, vtype in SWIFT_RADIUS_PATTERNS:
                match = re.search(pattern, line)
                if match and vtype == "swift_radius":
                    val = float(match.group(1))
                    int_val = int(val)
                    if int_val not in VALID_SWIFT_RADIUS and int_val > 0:
                        violations.append((i, f"[TOKEN] cornerRadius({int_val}) not in scale — use {sorted(VALID_SWIFT_RADIUS)}"))

            # --- SwiftUI Font Size Violations (blocking) ---
            for pattern, vtype in SWIFT_FONT_PATTERNS:
                match = re.search(pattern, line)
                if match and vtype == "swift_font":
                    val = int(match.group(1))
                    if val < SWIFT_MIN_FONT_SIZE:
                        violations.append((i, f"[TOKEN] Font size {val}pt below {SWIFT_MIN_FONT_SIZE}pt minimum — use .footnote or larger"))

            # --- SwiftUI Icon/Illustration Violations (warning) ---
            for pattern, msg in SWIFT_ICON_PATTERNS:
                if re.search(pattern, line):
                    violations.append((i, f"[BRAND] {msg}"))

            # --- SwiftUI Component Gatekeeper (blocking in page files) ---
            if is_page:
                for pattern, msg in SWIFT_COMPONENT_PATTERNS:
                    if re.search(pattern, line):
                        violations.append((i, f"[GATE] {msg}"))
                        break

            # --- AI Slop in SwiftUI strings (blocking) ---
            # Check string literals in Text("...") for slop
            text_match = re.search(r'Text\(\s*"([^"]+)"', line)
            if text_match:
                text_content = text_match.group(1)
                for pattern, msg in SLOP_COPY_PATTERNS:
                    if re.search(pattern, text_content):
                        violations.append((i, f"[SLOP] {msg}"))
                        break

        else:
            # ============================================================
            # WEB (REACT/TAILWIND) CHECKS
            # ============================================================

            # --- TOKEN VIOLATIONS (blocking) ---
            for pattern, msg in HARDCODED_COLOR_PATTERNS:
                if re.search(pattern, line):
                    violations.append((i, f"[TOKEN] {msg}"))
                    break

            for pattern, vtype in MAGIC_SPACING_PATTERNS:
                match = re.search(pattern, line)
                if match and vtype == "magic_spacing":
                    px_val = int(match.group(1))
                    if px_val not in VALID_SPACING_PX:
                        violations.append((i, f"[TOKEN] Magic spacing {px_val}px — use the spacing scale"))

            for pattern, vtype in TYPOGRAPHY_PATTERNS:
                match = re.search(pattern, line)
                if match and vtype == "magic_font_size":
                    px_val = int(match.group(1))
                    if px_val not in VALID_FONT_SIZES_PX:
                        violations.append((i, f"[TOKEN] Non-standard font size {px_val}px — use the type scale"))

            for pattern, msg in VISUAL_LANGUAGE_PATTERNS:
                if re.search(pattern, line):
                    violations.append((i, f"[TOKEN] {msg}"))

            # --- AI SLOP (blocking) ---
            for pattern, msg in SLOP_COPY_PATTERNS:
                if re.search(pattern, line):
                    violations.append((i, f"[SLOP] {msg}"))
                    break

            for pattern, msg in SLOP_VISUAL_PATTERNS:
                if re.search(pattern, line):
                    if "inline style" in msg:
                        violations.append((i, f"[SLOP] {msg}"))
                    else:
                        warnings.append((i, f"[SLOP] {msg}"))

            # --- COMPONENT GATEKEEPER (blocking in page files) ---
            if is_page:
                for pattern, msg in RAW_COMPONENT_PATTERNS:
                    if re.search(pattern, line):
                        violations.append((i, f"[GATE] {msg}"))
                        break  # One gatekeeper hit per line

    return violations, warnings


def format_output(file_path, violations, warnings, system_warning=None):
    parts = []

    if system_warning:
        parts.append(system_warning)
        parts.append("")

    if violations:
        parts.append(f"⛔ Design System BLOCKED — {len(violations)} violation(s) in {os.path.basename(file_path)}:\n")
        for line_num, violation in violations[:8]:
            parts.append(f"  Line ~{line_num}: {violation}")
        if len(violations) > 8:
            parts.append(f"\n  ... and {len(violations) - 8} more.")
        parts.append("\nFix these before proceeding. Check DESIGN-SYSTEM.md for correct patterns.")
        parts.append("Components must be defined in your design system before use in pages.")

    if warnings and not violations:
        parts.append(f"⚠️ Design System warnings in {os.path.basename(file_path)}:\n")
        for line_num, warning in warnings[:5]:
            parts.append(f"  Line ~{line_num}: {warning}")

    return "\n".join(parts)


def extract_content(tool_name, tool_input):
    if tool_name == "Write":
        return tool_input.get("content", "")
    elif tool_name == "Edit":
        return tool_input.get("new_string", "")
    elif tool_name == "MultiEdit":
        edits = tool_input.get("edits", [])
        return " ".join(edit.get("new_string", "") for edit in edits)
    return ""


def main():
    if os.environ.get("DISABLE_DESIGN_SYSTEM_HOOK", "0") == "1":
        sys.exit(0)

    try:
        raw_input = sys.stdin.read()
        input_data = json.loads(raw_input)
    except (json.JSONDecodeError, ValueError):
        sys.exit(0)

    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {})
    session_id = input_data.get("session_id", "default")

    if tool_name not in ["Edit", "Write", "MultiEdit"]:
        sys.exit(0)

    file_path = tool_input.get("file_path", "")
    if not is_ui_file(file_path):
        sys.exit(0)

    content = extract_content(tool_name, tool_input)
    if not content:
        sys.exit(0)

    # Check for DESIGN-SYSTEM.md existence (warn once per project per session)
    system_warning = None
    project_root = find_project_root(file_path)
    project_key = f"{session_id}:{project_root}" if project_root else session_id
    if project_key not in _warned_projects:
        system_warning = check_design_system_exists(file_path)
        if system_warning:
            _warned_projects.add(project_key)

    violations, warnings = check_violations(content, file_path)

    if violations:
        output = format_output(file_path, violations, warnings, system_warning)
        debug_log(f"BLOCKED: {file_path} — {len(violations)} violations")
        print(output, file=sys.stderr)
        sys.exit(2)

    if warnings or system_warning:
        output = format_output(file_path, [], warnings, system_warning)
        debug_log(f"WARNED: {file_path} — {len(warnings)} warnings")
        print(output, file=sys.stderr)
        sys.exit(0)

    debug_log(f"PASSED: {file_path}")
    sys.exit(0)


if __name__ == "__main__":
    main()
