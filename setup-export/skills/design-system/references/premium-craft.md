# Premium Craft Guide

Rules for making designs feel crafted, not generated. Sourced from design critique of AI-generated UIs.

## Typography Craft

### Font Selection
- **Never use default/overused fonts without justification.** Inter, Roboto, Arial, system-ui, Space Grotesk are the AI defaults. If you're using one, you need a brand reason.
- **Distinctive pairing > safe pairing.** Pair fonts deliberately: a striking serif for headings + clean geometric sans for body. Or monospace for metadata + humanist sans for content. The pairing IS the personality.
- **When in doubt, go uncommon.** Fonts that work beautifully but aren't overused: Söhne, PP Neue Montreal, Instrument Serif, Satoshi, General Sans, Cabinet Grotesk, Clash Display, Fraunces.

### Typography Execution
- **Semantic line breaks.** Line breaks must make sense. "Precision Tools / For Creators" not "Precision Tools For / Creators". Never let flexbox or CSS break text at meaningless points.
- **Push scale contrast.** Don't be afraid of massive screen-filling headlines (48-96px) paired with tiny metadata (10-12px). The contrast IS the hierarchy.
- **Absolute consistency within components.** If nav uses ALL CAPS, every nav item is ALL CAPS. If headings are sentence case, every heading is sentence case. One inconsistency kills the system.
- **Tracking matters.** Tight tracking (-0.02 to -0.04em) on large headings. Normal or slightly loose on body. Widest tracking on overlines/labels. These details separate craft from default.

## Color Craft

### Selection
- **Never use default Tailwind colors as brand.** `blue-500`, `slate-200`, `zinc-800` are the AI palette. If your brand colors are indistinguishable from Tailwind defaults, you haven't designed yet.
- **Create atmosphere, not just tokens.** Color should create a FEELING, not just label elements. The background color alone should tell you which brand you're in.
- **Warm off-whites have personality.** `#F8F7F4`, `#FAF9F6`, `#F5F0EB` feel editorial and premium. `#FFFFFF` feels clinical. `#F8FAFC` (Tailwind slate-50) feels default.

### Application
- **Borders and shadows: pick ONE approach and commit.**
  - Editorial/minimal: thin warm borders, no shadows (or shadow-sm on hover only)
  - Brutalist: thick black borders, hard offset shadows (`4px 4px 0px black`)
  - Ethereal: no borders, soft wide shadows with low opacity
  - Glassmorphic: translucent borders, backdrop-blur, no solid shadows
  - NEVER mix approaches on the same page
- **Color communicates state.** Don't use brand colors decoratively. Color should MEAN something: success, warning, active, selected, scoring.

## Layout Craft

### Structure
- **Avoid predictable 12-column grid.** The bootstrap/Tailwind default grid is the layout equivalent of Inter font — it works but it's invisible.
- **Spatial composition over grid compliance.** Embrace asymmetry, overlap, diagonal flow, grid-breaking elements. The layout should have visual tension, not just alignment.
- **Generous negative space OR controlled density — not the middle.** The worst layouts are "sort of spacious, sort of dense." Commit to either:
  - High-end editorial: vast white space, content breathes
  - Dense cockpit: controlled clutter, every pixel earns its place
  - The mushy middle signals no decision was made

### Scroll & Flow
- **If the page scrolls, SHOW it.** Always include a visual indicator: a scroll line, an arrow, peaking content from below the fold, a "scroll" label. Never let content disappear below a flat edge.
- **Visual rhythm between sections.** Alternate dense and spacious. Use full-bleed visual breaks. Change background tint between sections. Create a cadence like music — verse, chorus, bridge.

## Interaction Craft

### Animation
- **Purposeful motion only.** Every animation must answer "what does this communicate?" If the answer is "it looks cool," remove it.
- **No conflicting animations.** Don't have background blobs moving left while foreground cards float up. Motion should have a unified direction and purpose.
- **Immediate hover states.** All interactive elements need clear, instant hover feedback. If using 3D/clay UI, press states must be immediate — slow transitions on buttons feel broken.
- **Stagger, don't blast.** When multiple elements appear, stagger them (50-100ms delay each). Everything appearing at once feels like a page load, not a design.

### State Feedback
- **Score states should be VISUAL, not just text.** A score of 92/100 should feel different from 45/100 — different colors, different visual weight, maybe even different component treatment.
- **Active elements look active.** The currently selected nav item, the focused input, the active tab — these should be unmistakable without reading the text.

## Aesthetic Recipes

When choosing a visual direction for DESIGN-SYSTEM.md, here are proven combinations. Pick one and commit fully.

### Editorial / Magazine
- Background: warm off-white (`#FAF9F6`)
- Typography: flowing serif for headings (Playfair, Instrument Serif, Fraunces) + legible small sans for body
- Layout: asymmetric, print-inspired, thin divider lines
- Borders: thin, warm gray
- Shadows: none or barely-there on hover
- Energy: calm, confident, sophisticated

### Brutalist / Industrial
- Background: pure white or pure black
- Typography: bold chunky sans in ALL CAPS (Clash Display, Satoshi Black)
- Layout: harsh grid, no rounded corners, thick borders
- Borders: thick black, hard offset shadows (`box-shadow: 4px 4px 0px`)
- Shadows: solid, un-blurred
- Energy: aggressive, intentional, loud

### Terminal / Technical
- Background: pitch black (`#000000` or `#0A0A0A`)
- Typography: strict monospace only (JetBrains Mono, Space Mono, Berkeley Mono)
- Layout: dense, information-heavy, status indicators everywhere
- Borders: 1px with low-opacity colored glow
- Decorations: bracketed text `[ LIKE THIS ]`, exposed grid lines, blinking cursors
- Energy: precise, hacker, functional

### Ethereal / Organic
- Background: soft non-standard pastels (avoid purple)
- Typography: thin, light-weight humanist sans
- Layout: extreme negative space, floating elements, soft curves
- Borders: none — deep, soft, wide-spread shadows at low opacity
- Decorations: organic shapes, blur effects (on backgrounds, never on text)
- Energy: calm, dreamy, premium

### Neo-Retro
- Background: saturated solid colors or cream
- Typography: retro display fonts + modern geometric sans
- Layout: bold geometry, oversized elements, grid-breaking overlaps
- Borders: thick colored borders, rounded corners pushed to extremes (full pills)
- Decorations: halftone patterns, duotone imagery, bold color blocks
- Energy: playful, nostalgic, confident

## The Craft Checklist

Before shipping any screen:
- [ ] Font choice is deliberate, not default (Inter/Roboto = unjustified)
- [ ] Color creates atmosphere, not just labels
- [ ] Layout has visual tension (asymmetry, scale contrast, rhythm)
- [ ] Borders/shadows follow ONE consistent approach
- [ ] Hover states exist on ALL interactive elements
- [ ] Animations are purposeful, not decorative
- [ ] Scroll indicators exist if content is below the fold
- [ ] Typography has semantic line breaks
- [ ] Scale contrast exists (large headlines + small metadata)
- [ ] The aesthetic recipe is clear and fully committed to
