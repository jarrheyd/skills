#!/bin/bash
# Full design system audit
# Usage: ./audit-all.sh [directory]

DIR="${1:-.}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "🔍 Full Design System Audit"
echo "==========================="
echo "Directory: $DIR"
echo ""

bash "$SCRIPT_DIR/audit-colors.sh" "$DIR"
echo ""
echo "---"
echo ""
bash "$SCRIPT_DIR/audit-spacing.sh" "$DIR"
echo ""
echo "---"
echo ""
bash "$SCRIPT_DIR/audit-radius.sh" "$DIR"
echo ""
echo "---"
echo ""

# Dark mode usage check
echo "🌙 Dark Mode Check"
echo "==================="
echo "--- dark: classes (This app is light-mode only) ---"
rg -n '\bdark:' "$DIR" --glob '*.tsx' --glob '*.jsx' -g '!node_modules' 2>/dev/null || echo "  ✓ None found"

echo ""

# Typography check
echo "📝 Typography Check"
echo "==================="
echo "--- Non-standard font sizes ---"
rg -n 'text-\[\d+px\]' "$DIR" --glob '*.tsx' --glob '*.jsx' -g '!node_modules' 2>/dev/null || echo "  ✓ None found"

echo ""

# Component count
echo "📦 Component Summary"
echo "===================="
TSX_COUNT=$(find "$DIR" -name "*.tsx" -not -path "*/node_modules/*" | wc -l | tr -d ' ')
COMPONENT_COUNT=$(find "$DIR" -path "*/components/*.tsx" -not -path "*/node_modules/*" | wc -l | tr -d ' ')
PAGE_COUNT=$(find "$DIR" -name "page.tsx" -not -path "*/node_modules/*" | wc -l | tr -d ' ')
echo "  Total .tsx files: $TSX_COUNT"
echo "  Components: $COMPONENT_COUNT"
echo "  Pages: $PAGE_COUNT"

echo ""
echo "✅ Audit complete. Fix any violations above, then re-run."
