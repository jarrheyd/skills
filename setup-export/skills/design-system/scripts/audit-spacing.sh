#!/bin/bash
# Audit: Find magic spacing values in UI files
# Usage: ./audit-spacing.sh [directory]

DIR="${1:-.}"

echo "📏 Design System Audit: Magic Spacing Values"
echo "============================================="
echo ""

# Find arbitrary pixel values in spacing utilities
echo "--- Arbitrary spacing values (p-[Npx], m-[Npx], gap-[Npx]) ---"
rg -n '(p|px|py|pt|pb|pl|pr|m|mx|my|mt|mb|ml|mr|gap|space-[xy])-\[\d+px\]' "$DIR" --glob '*.tsx' --glob '*.jsx' -g '!node_modules' 2>/dev/null || echo "  ✓ None found"

echo ""

# Find arbitrary rem values
echo "--- Arbitrary rem values ---"
rg -n '(p|m|gap|space)-\[\d+(\.\d+)?rem\]' "$DIR" --glob '*.tsx' --glob '*.jsx' -g '!node_modules' 2>/dev/null || echo "  ✓ None found"

echo ""

echo "Valid spacing scale: 0, 0.5, 1, 1.5, 2, 3, 4, 5, 6, 8, 10, 12, 16, 20, 24, 32, 40, 48, 64"
echo "Use Tailwind classes: p-1, p-2, p-3, p-4, p-5, p-6, p-8, etc."
