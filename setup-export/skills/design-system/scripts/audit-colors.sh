#!/bin/bash
# Audit: Find hardcoded colors in UI files
# Usage: ./audit-colors.sh [directory]

DIR="${1:-.}"

echo "🎨 Design System Audit: Hardcoded Colors"
echo "========================================="
echo ""

# Find hardcoded hex colors in className attributes
echo "--- Hex colors in className ---"
rg -n 'className=["\x27][^"\x27]*#[0-9a-fA-F]{3,8}' "$DIR" --glob '*.tsx' --glob '*.jsx' -g '!node_modules' -g '!globals.css' -g '!DESIGN-SYSTEM.md' 2>/dev/null || echo "  ✓ None found"

echo ""

# Find arbitrary Tailwind colors
echo "--- Arbitrary Tailwind colors (bg-[#...], text-[#...]) ---"
rg -n '(bg|text|border|ring|fill|stroke)-\[#[0-9a-fA-F]+\]' "$DIR" --glob '*.tsx' --glob '*.jsx' -g '!node_modules' -g '!globals.css' 2>/dev/null || echo "  ✓ None found"

echo ""

# Find inline style colors
echo "--- Inline style colors ---"
rg -n 'style=\{\{[^}]*color.*#[0-9a-fA-F]' "$DIR" --glob '*.tsx' --glob '*.jsx' -g '!node_modules' 2>/dev/null || echo "  ✓ None found"

echo ""
echo "Done. All colors should use Tailwind tokens (bg-card, text-foreground, etc.)"
