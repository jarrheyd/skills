# [App Name] Design System

> Last updated: [date]
> Version: 1.0

---

## Visual Direction

**This is the most important section.** Every design decision flows from here. If two people disagree on a UI choice, this section settles it.

**North Star**: [What does the app FEEL like? Not "clean" or "modern" — those mean nothing. What real-world experience does it evoke? "A warm desk with your smartest colleague." "A cockpit where every dial matters." "A sketchbook that remembers everything."]

**The Feeling**: [One sentence: "Opening this app should feel like..."]

**Apps We Admire** (and SPECIFICALLY what we take from each):
- [App 1] — [exact trait]: [why it fits our brand, not just "it looks nice"]
- [App 2] — [exact trait]: [why it fits our brand]

**What We Explicitly Avoid** (and why):
- [Anti-pattern 1] — [why it doesn't fit THIS brand, not just "it's bad"]
- [Anti-pattern 2] — [why]

**Our Bold Bet**: [What is the ONE unconventional design decision that defines this app? The thing that makes it ours? This could be a layout choice, a navigation pattern, a visual element, or a voice decision.]

---

## Brand Identity

**Name**: [How the name is written — case, spacing, always/never with tagline]
**Tagline**: [If any]
**Logo**: [Description. When to show, when not to. Minimum size.]
**Character/Mascot**: [If any — describe personality, art style, when they appear]

---

## Brand Voice & Tone

> This applies to ALL user-facing text: buttons, labels, headings, empty states, errors, tooltips, onboarding.

**Personality**: [2-3 adjectives — but define what each MEANS for this brand]
**Speaks Like**: [A specific person or archetype — "a senior designer who's direct but kind"]
**Never Speaks Like**: [The anti-pattern — "a corporate chatbot" / "an overeager intern"]

**Voice Rules**:
- [e.g., "Sentence case, never Title Case"]
- [e.g., "No exclamation marks in UI labels"]
- [e.g., "Use 'you' not 'the user'"]
- [e.g., "One idea per sentence"]

**Good Examples**:
- "[actual example]" — [why it works for this brand]

**Bad Examples**:
- "[actual example]" — [why it doesn't work for this brand]

**AI Slop Banned Phrases** (add to this list as you catch them):
- [phrases that would make this app sound generic]

---

## Color Tokens

> Define semantic tokens, not raw colors. Every color has a NAME and a PURPOSE.

| Token | Value | Purpose |
|-------|-------|---------|
| `background` | [hex] | [when/where this appears] |
| `card` | [hex] | [elevated surfaces] |
| `surface` | [hex] | [inset areas, input backgrounds] |
| `border` | [hex] | [dividers, card edges] |
| `foreground` | [hex] | [primary text, primary interactive] |
| `muted-foreground` | [hex] | [secondary text, labels] |
| `primary` | [hex] | [brand accent — interactive highlights] |
| `success` | [hex] | [positive states] |
| `warning` | [hex] | [caution states] |
| `destructive` | [hex] | [errors, danger] |

**Why these colors**: [Brief explanation of the palette rationale — warm because..., muted because..., this accent because...]

**Rules**:
- Never hardcode hex values in components. Always reference tokens.
- [Any brand-specific color rules — e.g., "accent is used sparingly, never for large surfaces"]

---

## Typography Scale

| Level | Font | Size | Weight | Tracking | Usage |
|-------|------|------|--------|----------|-------|
| Display | [font] | [size] | [weight] | [tracking] | [where] |
| Title | | | | | |
| Heading | | | | | |
| Body | | | | | |
| Small | | | | | |
| Caption | | | | | |
| Mono | | | | | [when to use monospace] |

**Why this type system**: [e.g., "Tight tracking on headings because the brand is editorial" or "Monospace for data because the brand is precision-focused"]

---

## Spacing Scale

| Token | Value | Usage |
|-------|-------|-------|
| [scale values] | | |

**Standard Measurements**:
- Content max-width: [value] — [why]
- Screen padding: [value]
- Card padding: [value]
- Card corner radius: [value] — [why this radius]
- Card border style: [borders/shadows/neither] — [why]
- Between cards: [value]

---

## Component Library

> **GATEKEEPER RULE: No UI element renders unless it's listed here.**
> Before implementing ANY new visual element, add it here first with its pattern and rules.

| Component | Purpose | Where it lives | Key variants |
|-----------|---------|----------------|--------------|
| [Component] | [What it's for] | [file path] | [variants if any] |

**Adding a new component**:
1. Define it here with purpose, pattern, and variants
2. Explain WHY existing components can't serve this need
3. Implement it in the component library
4. THEN use it in pages

---

## Layout Decisions

> These are the STRUCTURAL choices that define how this app feels. Each must be justified.

**Primary navigation pattern**: [sidebar / tab bar / command palette / contextual / other]
- **Why**: [brand/UX justification, not convention]
- **Rejected alternatives**: [what we considered and why we didn't]

**Page structure**: [describe the general anatomy of a page]
- **Why**: [what about the brand/use case drives this structure]

**Empty state pattern**: [how empty screens look and feel]
- **Why**: [what tone does this set]

**Loading state pattern**: [how loading feels]

**Error state pattern**: [how errors feel]

---

## Iconography

**Icon set**: [which set and why]
**Style rules**: [stroke width, size, when filled vs outlined]

---

## Animation & Motion

| Context | Duration | Easing | Notes |
|---------|----------|--------|-------|
| [context] | [ms] | [easing] | |

**Motion philosophy**: [e.g., "Minimal and functional" or "Playful and responsive" — justified by brand]

---

## What Makes This App OURS

> This section captures the choices that differentiate this app from everything else in its category. If you removed the logo, would someone still recognize this as [App Name]?

1. [Bold choice #1] — [why it's ours]
2. [Bold choice #2] — [why it's ours]
3. [Bold choice #3] — [why it's ours]

---

## Rejected Patterns

> Document what we tried and abandoned, so we don't re-debate.

| Pattern | Why we rejected it |
|---------|-------------------|
| [pattern] | [reason] |

---

## Do's and Don'ts

### Do
- [brand-specific do's]

### Don't
- [brand-specific don'ts]
