#!/bin/bash
# Audit: Find incorrect border radius usage
# Usage: ./audit-radius.sh [directory]

DIR="${1:-.}"

echo "⭕ Design System Audit: Border Radius"
echo "======================================"
echo ""

# Cards should use rounded-2xl
echo "--- Cards with wrong radius (should be rounded-2xl) ---"
rg -n 'bg-card[^"]*rounded-(?:sm|md|lg)\b' "$DIR" --glob '*.tsx' --glob '*.jsx' -g '!node_modules' 2>/dev/null || echo "  ✓ None found"
rg -n 'border-border[^"]*rounded-(?:sm|md)\b' "$DIR" --glob '*.tsx' --glob '*.jsx' -g '!node_modules' 2>/dev/null || echo "  ✓ None found"

echo ""

# Heavy shadows on cards
echo "--- Cards with heavy shadows (should use border only) ---"
rg -n 'bg-card[^"]*shadow-(?:md|lg|xl|2xl)' "$DIR" --glob '*.tsx' --glob '*.jsx' -g '!node_modules' 2>/dev/null || echo "  ✓ None found"

echo ""

echo "Radius guide: Cards=rounded-2xl, Tabs=rounded-xl, Buttons/Inputs=rounded-lg, Badges=rounded-md"
