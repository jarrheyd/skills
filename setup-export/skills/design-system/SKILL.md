---
name: design-system
description: Design director for app UI: makes each app visually distinct and checks its DESIGN-SYSTEM.md shows up in the interface. Use when building or reviewing an app design system.
---

# Design System Skill — Design Director

Not a linter. Not a template. A creative director that makes each app visually distinctive, alive, and unmistakably its own brand.

Two apps using this skill should look like they were designed by different teams — because they WERE designed around different brand identities. The skill enforces that each app's DESIGN-SYSTEM.md actually manifests in the UI through:
- **Custom visual assets** drawn in code or made from real photos and screens (illustrations, patterns, backgrounds); Gemini images only when a client asks
- **Bold layout choices** that break the 2010s sidebar-cards-text template
- **Token enforcement** that prevents hardcoded values and AI slop
- **Component gating** that prevents raw className soup in page files
- **Visual life** — every screen must pass the "Is It Alive?" test

## Before choosing a look

A new brand, platform or rebrand starts with the owner picking real references (UI screens, photos, identities) they love, before any look is chosen. If you keep a brand references repo, read its brief for the brand first: <ADD YOUR OWN>. Name the art-style recipe and website pattern you follow; never re-describe a look from memory. No AI-generated images unless a client asks (principle `no-generated-images`): real photos, real screens or code-drawn art.

## Activation

This skill activates **automatically** through two mechanisms:

1. **PreToolUse Hook** (`hooks/design_system_hook.py`): Runs on every Write/Edit to `.tsx`/`.jsx` files in `components/` or `app/` directories. Blocks writes that contain hardcoded colors, magic spacing, wrong radii, heavy shadows, or dark mode classes. Set `DISABLE_DESIGN_SYSTEM_HOOK=1` to bypass.

2. **Manual invocation**: Use `/design-system` or ask Claude to audit the design system.

## How It Works

### Automated Enforcement (Hooks)

The PreToolUse hook intercepts file writes and checks for:

| Violation | What's caught | Action |
|-----------|--------------|--------|
| Hardcoded colors | `bg-[#fff]`, `text-[#333]`, `style={{ color: '#...' }}` | **Block** |
| Arbitrary Tailwind colors | `bg-[rgb(...)`, `text-[#hex]` | **Block** |
| Magic spacing | `p-[17px]`, `gap-[11px]` (values not in 4px grid) | **Block** |
| Wrong card radius | Card with `rounded-md` instead of `rounded-2xl` | **Block** |
| Heavy card shadows | `shadow-md/lg/xl` on cards at rest | **Block** |
| Dark mode classes | `dark:` prefix (when project is light-only) | **Block** |
| Magic font sizes | `text-[28px]` (values not in type scale) | **Block** |

The hook reads `DESIGN-SYSTEM.md` from the project root for project-specific tokens. If the file doesn't exist, create one using the template in `references/design-system-template.md`.

### Manual Audit (Scripts)

Run full or targeted audits from the command line:

```bash
# Full audit
bash ~/.claude/skills/design-system/scripts/audit-all.sh ./src

# Specific audits
bash ~/.claude/skills/design-system/scripts/audit-colors.sh ./src
bash ~/.claude/skills/design-system/scripts/audit-spacing.sh ./src
bash ~/.claude/skills/design-system/scripts/audit-radius.sh ./src
```

### Agent Audit

For deep analysis, use the design auditor agent (`agents/design-auditor.md`) which:
- Scans all UI files and extracts every visual value
- Compares against DESIGN-SYSTEM.md tokens
- Reports violations by severity (critical/warning/info)
- Suggests exact fixes with before/after code
- Generates a compliance score

## Workflow for Any UI Change

### Phase 1: Read the Design System
Before writing any UI code, read `DESIGN-SYSTEM.md` in the project root.

### Phase 2: Component Check
1. Does the UI element I need already exist? **USE IT.** Check `references/component-patterns.md` for standard patterns.
2. If not, should it be shared (used 2+ times)? **CREATE IT** in the component library first.
3. If truly single-use, it can be inline BUT must use design tokens.

### Phase 3: Write Code
The PreToolUse hook will automatically validate your writes. If blocked, fix the violation and retry.

### Phase 4: Visual Audit
Before finishing any UI work, verify:
- [ ] All colors from design tokens (no hardcoded hex/rgb)
- [ ] All spacing from the spacing scale (no magic numbers)
- [ ] All typography from the type scale (no ad-hoc font sizes)
- [ ] Correct border radius per element type
- [ ] No shadows on cards at rest
- [ ] Brand voice in all copy (no exclamation marks, no "oops")
- [ ] Consistent with adjacent screens

### Phase 5: Make It Alive
Run the "Is It Alive?" test:
- [ ] At least ONE visual element beyond text and icons per screen
- [ ] Removing the logo would NOT make this look like a template
- [ ] Color communicates state, not just decorates buttons
- [ ] At least one interactive surprise or visual response
- [ ] Visual rhythm — dense and spacious sections alternate
- [ ] A screenshot would make someone want to use the app

If the screen fails: draw visual assets in code or use real material from the taxonomy sources, break the layout, add color-as-communication, add motion. Read `references/visual-generation.md` and `references/bold-layouts.md`.

### Phase 6: Consistency Sweep
Compare against other screens:
- Same visual language?
- Same component library?
- Same empty state treatment?
- Same typography hierarchy?

## References

| File | Purpose |
|------|---------|
| `references/design-system-template.md` | Framework template for defining a new app's system |
| `references/bold-layouts.md` | 8 layout patterns that break the 2010s template + "Is It Alive?" test |
| `references/visual-generation.md` | How to generate brand-specific illustrations/assets via Gemini |
| `references/deslop.md` | AI slop detection (visual + copy + structural) + what to do instead |
| `references/violation-examples.md` | Common violations with before/after fixes |
| `references/component-patterns.md` | Reusable component code patterns (adapt to your brand) |
| `agents/design-director.md` | Creative review — questions defaults, pushes for brand-specific boldness |
| `agents/design-auditor.md` | Token/pattern compliance audit |
| `scripts/audit-all.sh` | Full codebase scan |

## Key Rules

### The Three Laws (Universal, Every App)
1. **Deliberate > Default.** Every choice must pass "Why this?" If the answer is "because that's how it's usually done," reconsider.
2. **System > Instance.** No component, color, spacing, or pattern exists outside DESIGN-SYSTEM.md. Add to the system first, then use it.
3. **Brand > Convention.** The brand's visual direction determines layout, navigation, color, typography — not templates, not trends, not what other apps do.

### System Integrity (Universal, Every App)
4. **Token-only values**: Never hardcode colors, spacing, or font sizes. Always reference the project's defined tokens.
5. **Component gatekeeper**: Nothing renders without being in the Component Library section of DESIGN-SYSTEM.md.
6. **Update the system, not the instance**: Need a new pattern? Define it in the system first. If you skip this, you're creating slop.
7. **Consistency once decided**: Once a choice is in the system, it applies everywhere. No "well, on THIS page I'll do it differently" without updating the system.

### UX Integrity (Universal, Every App)
8. **Disconnected service = minimal UI**: Hide actions for unconnected services. Show only the connect prompt.
9. **No redundant views**: One source of truth per data type. If two views show the same data, consolidate.
10. **Feature removal = full audit**: Grep all references. Don't just delete from one screen.
11. **Every state is designed**: Empty, error, loading, and edge states are designed FIRST. The happy path is the easy part.
12. **App icon matches the system**: The icon's visual language aligns with the brand identity in DESIGN-SYSTEM.md.

### Anti-AI Slop (Universal, Every App)
13. **No generic copy**: "Elevate your workflow," em dash abuse, "Not X, but Y," "quietly revolutionary" — see `references/deslop.md` for the full list. These are blocked by the hook.
14. **No unjustified defaults**: Left sidebar, card grid, purple gradient, dark mode — fine IF justified by brand. Slop if chosen by default.
15. **No one-off visual patterns**: If a div has custom styling, it should be a component. Ad-hoc className combos are how visual inconsistency creeps in.

### The Bold Question (Per App, Per Page)
16. **"What is the ONE choice on this page that could only belong to this brand?"** If the answer is "nothing" — the page needs more brand-specific intentionality. Not weird for weird's sake. Bold because the brand justifies it.
