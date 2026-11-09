#!/bin/bash
# SwiftUI Design System Audit
# Usage: ./audit-swift.sh [directory]
# Checks SwiftUI code against design system tokens

DIR="${1:-.}"

echo "🎨 SwiftUI Design System Audit"
echo "=============================="
echo "Directory: $DIR"
echo ""

# ---- Colors ----
echo "🎨 Color Violations"
echo "==================="
echo "--- .foregroundColor(.white/.black/.gray) ---"
grep -rn '\.foregroundColor(\.\(white\|black\|gray\))' "$DIR" --include="*.swift" 2>/dev/null || echo "  ✓ None found"
echo ""
echo "--- Color(red:green:blue:) ---"
grep -rn 'Color(\s*red:' "$DIR" --include="*.swift" 2>/dev/null || echo "  ✓ None found"
echo ""
echo "--- UIColor.black/white/gray ---"
grep -rn 'UIColor\.\(black\|white\|gray\|systemGray\)' "$DIR" --include="*.swift" 2>/dev/null || echo "  ✓ None found"
echo ""

# ---- Spacing ----
echo "📏 Spacing Violations"
echo "====================="
echo "--- padding values not in {4,8,12,16,24,32} ---"
grep -rn '\.padding(\s*[0-9]' "$DIR" --include="*.swift" 2>/dev/null | grep -vE 'padding\(\s*(4|8|12|16|24|32)\s*\)' || echo "  ✓ None found"
echo ""
echo "--- padding(.direction, value) not in scale ---"
grep -rn '\.padding(\.\w\+,\s*[0-9]' "$DIR" --include="*.swift" 2>/dev/null | grep -vE ',\s*(4|8|12|16|24|32)\s*\)' || echo "  ✓ None found"
echo ""

# ---- Corner Radius ----
echo "⭕ Corner Radius Violations"
echo "==========================="
echo "--- cornerRadius values not in {2,4,8,12,24} ---"
grep -rn '\.cornerRadius(\s*[0-9]' "$DIR" --include="*.swift" 2>/dev/null | grep -vE 'cornerRadius\(\s*(2|4|8|12|24)\s*\)' || echo "  ✓ None found"
echo ""

# ---- Font Sizes ----
echo "📝 Font Size Violations"
echo "======================="
echo "--- .font(.system(size: N)) where N < 13 ---"
grep -rn '\.font(\.system(size:\s*[0-9]' "$DIR" --include="*.swift" 2>/dev/null | grep -E 'size:\s*([0-9]|1[0-2])\s*[,)]' || echo "  ✓ None found"
echo ""

# ---- Icon/Illustration Usage ----
echo "🖼️ Icon/Illustration Audit"
echo "=========================="
echo "--- AppEmptyState using icon: instead of illustration: ---"
grep -rn 'AppEmptyState.*icon:' "$DIR" --include="*.swift" 2>/dev/null || echo "  ✓ None found (all use illustrations)"
echo ""
echo "--- Screens missing AppAmbientBackground ---"
for f in $(find "$DIR" -name "*View.swift" -path "*/Features/*" 2>/dev/null); do
    if ! grep -q "AppAmbientBackground" "$f" 2>/dev/null; then
        echo "  ⚠ $f"
    fi
done
echo ""

# ---- Component Usage ----
echo "📦 Component Usage"
echo "=================="
echo "--- Inline TextField (should use AppInputBar/AppSearchBar) ---"
grep -rn 'TextField("message app' "$DIR" --include="*.swift" 2>/dev/null || echo "  ✓ None found"
grep -rn 'TextField("[Ss]earch' "$DIR" --include="*.swift" -l 2>/dev/null | grep -v "AppComponents" || echo "  ✓ Search bars use components"
echo ""

# ---- Copy Rules ----
echo "✍️ Copy Violations"
echo "==================="
echo "--- Exclamation marks in Text() ---"
grep -rn 'Text("[^"]*!"' "$DIR" --include="*.swift" 2>/dev/null || echo "  ✓ None found"
echo ""

# ---- Summary ----
SWIFT_COUNT=$(find "$DIR" -name "*.swift" -not -path "*/build/*" 2>/dev/null | wc -l | tr -d ' ')
VIEW_COUNT=$(find "$DIR" -name "*View.swift" -not -path "*/build/*" 2>/dev/null | wc -l | tr -d ' ')
echo "📊 Summary"
echo "=========="
echo "  Total .swift files: $SWIFT_COUNT"
echo "  View files: $VIEW_COUNT"
echo ""
echo "✅ Audit complete. Fix any violations above, then re-run."
