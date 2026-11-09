# Design/UI Slop Patterns

Visual and structural patterns that make UI instantly recognizable as AI-generated. Each pattern includes detection criteria, the "why this?" test, and what to do instead.

## The Core Problem: Distributional Convergence

Every AI design tool (v0, Lovable, Bolt, Cursor) generates from the same training distribution. The output converges toward the statistical mean: same fonts, same colors, same layouts, same component styling. A fintech dashboard is indistinguishable from a CRM is indistinguishable from a project management tool. AI slop sites record conversion rates 91% lower than quality inventory.

## The 14 Patterns

### 1. Purple Gradient Disease
Dark background + neon purple/blue glowing gradients. The official color scheme of "we used AI." Tailwind ships rich indigo/violet families as defaults, and AI tools trained on these patterns reproduce them endlessly.
- **Detection**: Purple/blue gradients used decoratively without brand justification
- **The test**: "Is this purple because the brand IS purple, or because AI defaulted to it?"
- **Fix**: Colors come from brand palette. If the brand isn't about AI/tech/crypto, purple gradients are slop. Even if it IS tech, consider whether purple is a deliberate choice or a default.

### 2. The Default Layout (Sidebar + Topbar)
Logo top-left, sidebar with 6 nav items, top bar with search + avatar. The Salesforce layout from 2015. Every AI-generated dashboard uses this because it's the most common pattern in training data.
- **Detection**: This layout without questioning whether it serves the use case
- **The test**: "Is a persistent sidebar the right navigation for THIS app? Or did we just... not think about it?"
- **Alternatives**: Command palette (Raycast), floating contextual nav, tab bar, full-screen sections, typography-as-navigation, bottom bar, drawer nav

### 3. Bento Box Abuse
Apple-style grid of rounded cards used as a content dump. AI generates these because grids are mathematically simple and look "designed."
- **Detection**: Grid of equal-sized cards where content importance varies wildly
- **The test**: "Does every card deserve equal visual weight? What's the ONE thing on this page?"
- **Fix**: Use hierarchy. One hero element, supporting elements smaller. Not everything needs a card. Flat content with dividers. Asymmetric grid with one large + several small.

### 3b. Bar Line Under Every Heading
A colored horizontal rule under each section heading, or a decorative `<hr>` between sections. AI reaches for it to signal "this is a section." In a document (or an HTML-to-Google-Doc conversion, where `h2{border-bottom}` becomes a `---` rule) it reads as machine-generated section furniture.
- **Detection**: `h1`-`h6` styled with `border-bottom`, standalone `<hr>` between blocks, a `---` rule under headings in a converted doc
- **The test**: "Does this heading need a line drawn under it, or is the bold weight plus the space above it already the divider?"
- **Fix**: Delete the rule. Let heading weight, size, and generous whitespace mark the section. If you truly need a visual break, use spacing, not a bar. (Enforced in `design_slop_hook.py`.)

### 4. Shadow Soup
Every component has a different shadow depth, blur radius, and border treatment. Cards, buttons, and inputs all look like they're from different apps.
- **Detection**: More than 2 shadow values on a single page. Mix of bordered and shadowed cards.
- **The test**: "Do these shadows follow a consistent elevation system?"
- **Fix**: ONE approach: borders OR shadows. ONE system: rest state, hover state, active state. That's it.

### 5. Stock Illustration Disease
People carrying oversized objects. 3D metallic blobs. Gradient mesh backgrounds with no purpose. Abstract illustrations that communicate nothing about the brand.
- **Detection**: Decorative imagery that works for any product
- **The test**: "What does this illustration tell you about OUR product that text doesn't?"
- **Fix**: Show real UI, real data, real screenshots. Or use no imagery — let typography carry. Custom illustrations that reference the brand's visual language.

### 6. Unchanged Component Libraries
Using shadcn/ui, Material UI, or Chakra with zero customization. The same rounded-md buttons, the same gray-200 borders, the same slate color palette out of the box.
- **Detection**: Components identical to library defaults. Someone can name your UI library by looking at your app.
- **The test**: "Have we made this ours, or are we wearing someone else's clothes?"
- **Fix**: Every component customized to the brand. Different border radius, different color, different hover behavior, different font — SOMETHING that makes it not-default.

### 7. The Feature Grid
3-column grid of features, each with an icon + heading + one-sentence description. The homepage formula since 2018.
- **Detection**: Features as equal-weight grid items
- **The test**: "Is this the best way to show what our product does? Or just the easiest?"
- **Fix**: Tell a story. Show the product in action. One feature at a time, full-bleed. Before/after. Interactive demo. Anything except the grid.

### 8. Inter/System Font Default
AI tools default to Inter, Roboto, Arial, or system-ui. These are the typographic equivalent of lorem ipsum — they signal no design decision was made.
- **Detection**: Using these fonts without brand justification
- **The test**: "Did we CHOOSE this font, or did we just not change it?"
- **Fix**: Choose a typeface that reflects the brand. Distinctive serif for editorial. Monospace for technical. Bold geometric for playful. The font IS the personality.

### 9. Uniform Border Radius
16px (rounded-2xl) on everything. Cards, buttons, inputs, modals, badges — all the same radius. AI applies one radius value globally because it's safe.
- **Detection**: Same border radius on all elements regardless of size or function
- **The test**: "Should a 32px badge and a 400px card really have the same corner radius?"
- **Fix**: Radius should be proportional to element size and semantic to element type. Buttons can be pill-shaped while cards are slightly rounded while badges are fully round. Or go sharp: 0px radius is a statement.

### 10. Glassmorphism Without Purpose
Frosted glass cards floating in voids of soft pastel. Backdrop-blur on everything. Used because it looks "modern" without serving any function.
- **Detection**: backdrop-blur, translucent backgrounds used decoratively
- **The test**: "Is the translucency showing something behind the card that matters? Or is it just... there?"
- **Fix**: Glassmorphism makes sense when layering matters (a panel over live content). If the background is static, use a solid color.

### 11. Gradient Blob Decorations
Soft, blobby, multicolor gradients floating behind content. Purely ornamental shapes in corners and backgrounds.
- **Detection**: Abstract gradient shapes with no semantic meaning
- **The test**: "What happens if I delete these blobs?" If nothing is lost, delete them.
- **Fix**: Backgrounds should either be solid (the content does the work) or meaningful (a texture that reinforces the brand, data visualization, a real photograph).

### 12. Excessive Whitespace (The Middle)
Generous but purposeless spacing. Everything floats in a sea of space — not the confident white space of editorial design, just unused pixels.
- **Detection**: All elements have similar, generous spacing. No contrast between dense and spacious sections.
- **The test**: "Is this space deliberate (editorial, breathing room) or just unfilled?"
- **Fix**: Commit to either editorial white space (vast, intentional, with contrast) or controlled density (every pixel earns its place). The mushy middle signals no decision was made.

### 13. Dark Mode as Default
Dark mode because "it looks techy" without considering whether the brand or use case justifies it. AI defaults to dark because it's visually impressive in screenshots.
- **Detection**: Dark background without brand justification
- **The test**: "Is our audience using this at 2am in a dark room, or at 10am in an office?"
- **Fix**: Light mode is the right default for most products. Dark mode should be offered as an option, not a default, unless the brand identity specifically calls for it.

### 14. Missing States
Beautiful happy-path screens. But no empty states, no error states, no loading states, no edge cases.
- **Detection**: Only the "data exists and everything works" state is designed
- **The test**: "What does a brand-new user with zero data see?"
- **Fix**: Empty, error, loading, and edge states designed FIRST. These states are where personality lives.

## The Design Slop Checklist

Before shipping any screen, verify:
- [ ] Color palette is brand-specific, not Tailwind/AI defaults
- [ ] Font choice is deliberate, not Inter/Roboto/system
- [ ] Layout has been questioned — not sidebar+topbar by default
- [ ] Components are customized, not library defaults
- [ ] Shadow/border approach is consistent (ONE system)
- [ ] Border radius varies by element type and size
- [ ] Decorative elements serve the brand (or are removed)
- [ ] Spacing has contrast (dense + spacious, not uniform)
- [ ] All states designed: empty, error, loading, edge cases
- [ ] A screenshot alone communicates which brand this is
- [ ] No subtitle, helper line or caption that explains the screen. Delete each one and check a first-time user can still do the task (see "Interface copy that explains itself" in the copy dictionary)

## AI design tells - full checklist (2026-08-27)

Regex-caught by `hooks/design_slop_hook.py` are marked (hook); the rest need a reviewer's eye (judgment). Applies to landing pages, decks, and app UI.

**Color & light**
- Harsh / over-gradients, multiple gradients as decoration (hook: 4+). One purposeful gradient is fine.
- AI purple, purple-and-black, the #667eea->#764ba2 gradient (hook).
- Rainbow / neon / basic-pastel palettes with no brand logic (judgment).
- Radial orbs and glowing blobs in the background (hook: blur blob / radial).
- Pure #ffffff page background instead of an intentional off-white (judgment; his brands use chalk/off-white).

**Depth & shape**
- Drop-shadow filter and the generic rgba(0,0,0,0.1) card shadow (hook).
- Soft-corner-radius on everything, uniform (judgment).
- Faint hairline card outlines, the invisible border (hook).
- Liquid glass / glassmorphism, backdrop blur (hook).

**Layout & components**
- 3 feature cards in a row; bento grids; dot grids (judgment).
- Colored left stripe / accent-border cards (hook).
- 3 pricing tiers as the default shape (judgment).
- Terminal-window mockup as a hero prop (hook, best-effort).
- Fake testimonials; no real product demos or screenshots (judgment).
- Stock team photos and fake product shots (a generic dashboard on a laptop) in place of real people and real screens (judgment).
- Footer and nav links that go nowhere (`href="#"`, "About" with no page behind it) (judgment).
- Missing TOS / privacy policy / skeleton loaders on a "real" product (judgment - real products have these).

**Icons, type, motion**
- Lucide icons; Inter / Geist / Space Grotesk as the default typeface (hook).
- Emojis and sparkle icons as decoration (judgment).
- A white icon inside a solid colored circle, repeated per feature (judgment).
- Checkmark-bullet lists everywhere (judgment).
- Animated arrows, gratuitous hover animations (judgment).

## Slide-specific tells (2026-08-27 - do NOT do these in decks)

- **No eyebrow / kicker** - the little label above a slide headline ("THE PROBLEM", "INTRODUCING X"). Delete it; the headline stands alone. (hook, in HTML and JSX: an eyebrow-style class, or a short uppercase line directly above a heading)
- **No dash / rule at the top** of a slide as ornament.
- **No explainer header** that restates what the slide is ("This slide covers..."). The content IS the explanation.
- **No footer caption** that re-explains the slide at the bottom. Both the top explainer and bottom caption make a slide wordy - cut both.
- A slide is one idea, shown - not an idea wrapped in a label, a header, and a caption. See the "no corner chrome" rule.
- **No summary closing slide.** A closing slide, if you need one, is a thank-you or contact info - never a recap of what was just shown. The deck already made the point.

## Deck tells learned from live correction (2026-09-17)

Caught by hand across an eight-round strategy-deck review the write-hooks never saw, because the deck lived in Claude Design and Google Slides. Judgment tells for the review agent.

- Comma two-beat headline. A slide title built as two short parallel or imperative clauses joined by a comma, like "All-in prices, held at the counter" or "Surface every tier, unblock stuck supply". It is the antithesis cadence moved into a heading. Fix: one plain clause a person would say out loud.
- Wordy feature-card grid. Three or more cards, each an icon plus a bold title plus a description sentence. It fails the three-second executive skim. Fix: let the headline and one visual carry the point, cut the card sentences to short labels, or drop the grid.
- Staged mockup. A social post that does not look like how people actually post: an arty stock silhouette with a clean Book button overlaid, or a tidy card with a booking tile. Fix: match the real platform, a native reel with caption, side icons and link in bio, or a real Facebook page post with reactions and comments.
- Outcome dressed as strategy. A play or strategy slide whose headline states a value or promise, like "What you see is what you pay", instead of the move you make, like "Get providers to commit to all-in prices". Fix: headline the action, show the mechanism, and name the hard part.
- Unverified specifics as fact. Provider counts, adoption ratios, or first-shown prices stated flat with no source you would defend. Fix: verify it, cut it, or mark it a target. Keep a per-deck claims ledger the author can veto.
- Footers and source lines on slides. Citation lines, production-data stamps, and page furniture at the bottom. Fix: cut them, a slide is one idea shown.
- Outdated tactics. For a strategy or marketing deck, check the plays against current trends so nothing reads as years old (search-only where the move is AI answers and creator-first).

## Less is more (2026-10-21)

From Jakub Krehel, "Less is more, more or less" (https://jakub.kr/writing/less-is-more). AI makes adding free, so every element now has to earn its place, and removal is the default.

- Gratuitous text: labels, captions and helper lines the reader does not need. An eyebrow or kicker over a heading (hook), a decorative badge ("New", "Beta", "AI") on something that is neither new nor beta, an explainer header or footer, a closing recap. Fix: delete each one, then check a first-time user still gets it.
- Decoration with no information: icons beside every heading, dot grids, ornamental dividers, a pill that repeats the heading, a status dot that never changes. Delete it; if nothing is lost, leave it deleted.
- Motion that ignores frequency. Animation scales with how often it fires. A menu, hover, tab switch or toggle used all day gets little or no motion; a 300ms open on a menu used 200 times a day is six hours a year of waiting. Rare moments (first run, a finished upload, a page change) can carry more. Fix: for frequent controls, cut the entry animation and the hover fade, keep a short exit if any.
- Adding instead of deciding: three ways to do one thing, a setting for every edge case, a second panel that repeats the first. Pick one and cut the rest.

## Catalog tells (2026-11-02)

From Impeccable's slop catalog (impeccable.style/slop, 67 patterns) and Ridd's live portfolio reviews. The hook now blocks these, each only when two signals meet so ordinary markup passes:

- An "Introducing" or "New:" pill above the hero. Say the news in the headline or cut it.
- A pulsing dot next to "all systems operational". Show status only where a real feed backs it.
- A glow that follows the cursor (mousemove plus a radial gradient on CSS variables). It is the first hover effect AI hands out.
- A giant "10M+" with a tiny label. Use a real, sourced number in a sentence, or drop it.
- "01 / Features" style section labels over a heading. A bare number set as a design element (a deck divider, a post index) passes.
- An icon tile above every heading, three or more times.
- Cards inside cards (`.card .card`). Flatten to one surface.

The same tells in Tailwind and JSX block too (11-02): `from-purple-500` gradients, `font-inter`, Inter from Google Fonts or next/font, `bg-clip-text`, `backdrop-blur` on a see-through white card, `border-l-4`, `blur-3xl` halos, icon tiles sized `h-12 w-12 rounded-xl`, rounded bordered cards nested in each other, three identical feature cards, a cursor glow built from a template string, beige with an italic serif (skipped when the project has a DESIGN-SYSTEM.md, BRAND-SYSTEM.md or DESIGN.md), and launch copy such as "supercharge" or "unleash".

Review only, no hook: a small label above a heading written in normal case, and grey subtext under every heading. In product screens these are form titles and helper text (770 matches in client apps, nearly all real information), so a hook would block good work. On a marketing page or portfolio, cut them during the impeccable critique.

## Unslop pass, 20 fixes (2026-11-08)

From Charles Liu's reel "20 Ways to Unslop AI Designs" (instagram.com/reel/DfcnAJFhAa1). Run these as a last pass on any page, deck or mock before it ships. Where a fix is already a rule above, the line points to it.

1. Delete filler badges. A "Most popular" or "New" pill only stays when it is true and helps a choice (see Less is more).
2. Drop redundant labels. If the heading says it, the label over it goes (eyebrows, Less is more).
3. Unitalicize the random word in the headline. One italic word in a sans or serif headline is the AI "tasteful" move. The hook blocks it unless the project has a DESIGN.md that says why.
4. Mono only where it means code, numbers in a table, or a terminal. Not for labels, tags or decoration.
5. Use a design system: one set of type sizes, colors, radii and spacing, read from the brand's tokens, never picked per screen.
6. Show the actual product. A real screen beats an icon grid or a feature card (Stock Illustration Disease, The Feature Grid).
7. Enlarge the main feature. One thing on the screen is big. Everything else steps down.
8. Group with spacing. Related items sit close and groups sit apart, with no boxes doing that job (Bento Box Abuse).
9. Make the headline specific: what it does for whom, in words a competitor could not paste onto their site.
10. Emphasize the one CTA. One filled button per view, and the rest are quieter.
11. Add one accent color and use it for the thing to press or notice. One, not a palette.
12. Keep icons consistent: one set, one stroke weight, one size per context.
13. Remove embellishments: arrows, sparkles, glows and lines that point at nothing.
14. Nested radius: inner radius = outer radius minus the padding between them. A 24 px card with 8 px padding holds a 16 px button, not another 24 px one.
15. Improve text contrast. Check with APCA (the standards repo's `check.mjs`). Body text at Lc 60 or more, and muted text still at Lc 45 or more.
16. Wrap headlines on purpose: `text-wrap: balance` on headings, no single word left alone on the last line.
17. Align by eye, not by pixel box. Nudge play icons, quote marks and round shapes so they look centered, even when the box math says otherwise.
18. Tabular figures for any number that changes or lines up: prices, counters, tables (`font-variant-numeric: tabular-nums`).
19. Add loading states: a skeleton in the shape of the real content, never a blank area or a lone spinner (Missing States).
20. Animate useful feedback: the press, the add, the save. Motion confirms an action and never decorates (see the review-animations skill).

## 30 signs a site was vibecoded (2026-11-08)

From Niki Aroca's reel "30 reasons your site looks vibecoded" (instagram.com/reel/DfX3LIIIvub). "Hook" means the write hook blocks it. "Check" means a reviewer looks for it, because a script cannot see it in one file.

Look:
1. Purple-to-blue gradients (hook).
2. Three feature cards in a row (hook).
3. Fake testimonials: a quote with no real name, role, or company. Check.
4. Sparkle icons everywhere (hook, 2 or more).
5. "It's not X, it's Y" copy (copy hook).
6. Gradient headline text (hook).
7. Glassmorphism everywhere (hook).
8. Pointless terminal windows, a fake code panel that shows nothing real (hook).
9. Generic buzzword copy (copy hook).
10. Untouched shadcn/ui: default radius, gray, and focus ring. Check (Unchanged Component Libraries).
11. Glowing background orbs (hook).
12. Emojis in every heading (hook).
13. Badges above headlines (hook).
14. Em dashes everywhere (copy hook).
15. Lucide icons everywhere (hook).

Build:
16. Empty bento grids (hook).
17. Generic three-tier pricing: Basic, Pro, and Enterprise with a "Most popular" badge on the middle one. Check.
18. Everything fades in on scroll (hook, 6 or more).
19. Cursor-following beams (hook).
20. Low-contrast dark mode. Check with APCA.
21. Inconsistent spacing: gaps that come from no scale. Check.
22. Vague button labels ("Learn more", "Get started", "Submit"): a button says what happens. Check.
23. No real product demos: a real screen or a recording beats a mockup. Check.
24. Claims without proof: every number needs a source. Check.

Trust:
25. Forms asking for too much: only the fields the next step needs. Check.
26. Forms that don't work by keyboard. Clickable divs and spans with no role or tabIndex are a hook; tab order and focus are a check.
27. Broken third-party embeds. Check by loading the page.
28. Placeholder business info: lorem ipsum, 555 numbers, example.com, Acme, John Doe (hook).
29. No privacy policy. Check on any site that collects data.
30. No terms and conditions. Check on any site that sells or signs people up.
