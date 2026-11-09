# Visual Asset Generation Guide

The design system skill can generate illustrations, backgrounds, icons, patterns, and visual assets using Gemini's image generation. Every app should have custom visuals that match its DESIGN-SYSTEM.md — not stock art, not text-only.

## Why This Matters

In 2026, text-on-white-cards is the new "website template from 2010." Every AI-built app looks identical:
- White/dark background
- Cards with borders
- Text, text, more text
- Maybe a Lucide icon
- Zero visual personality

The DESIGN-SYSTEM.md defines a visual direction. This guide makes sure that direction actually shows up in the app through generated visual assets.

## When to Generate Visuals

- **Onboarding**: The first impression. Should have a distinctive visual — illustration, pattern, gradient, or character.
- **Empty states**: Instead of "No data yet" in gray text, show something that feels alive and on-brand.
- **Login/signup**: The entry point needs to feel like the brand, not like a generic auth form.
- **Loading states**: An opportunity for personality (animated brand element, not just a spinner).
- **Error states**: Visual empathy, not just red text.
- **Landing/marketing pages**: Hero sections need visual impact.
- **Section dividers**: Visual rhythm between content sections.
- **Backgrounds**: Subtle patterns, gradients, or textures that make the canvas feel intentional.

## How to Generate with Gemini

Use `gemini-generate-image` to create assets. The key is crafting prompts that reference the brand's visual direction from DESIGN-SYSTEM.md.

### Prompt Formula
```
[Art style from DESIGN-SYSTEM.md] [Subject] for [context].
[Color constraints from palette].
[Mood/feeling from visual direction].
[Technical specs: transparent background, minimal, etc.]
```

### Example Prompts by Brand Type

**Warm Editorial Brand (example)**:
- "Minimal line illustration of a signal flag on a ship's mast, using only indigo (#5746AF) on transparent background. Single continuous line, editorial style, no fill."
- "Abstract organic shape suggesting growth and signal, warm parchment tones (#F8F7F4, #E5E2DD) with a single indigo accent. Suitable as a subtle background texture."
- "Simple geometric illustration of a megaphone made of overlapping transparent shapes in indigo and warm gray. Flat, editorial, minimal."

**Playful Consumer Brand**:
- "Cartoon mascot character waving, round friendly proportions, bright saturated colors matching brand palette [colors]. White background, suitable for app empty states."
- "Isometric illustration of [scene] with exaggerated proportions and bold shadows. Colors: [brand palette]. Fun but not childish."

**Technical/Developer Brand**:
- "Architectural blueprint-style diagram of [concept], monochrome with single accent color [hex]. Clean lines, engineering precision, dark background."
- "Abstract data visualization art showing flowing particles, deep navy background with electric [accent] highlights. Generative art aesthetic."

**Luxury/Premium Brand**:
- "Gold foil texture element on black, abstract organic shape suggesting [brand concept]. Rich metallic detail, suitable as decorative accent."
- "Minimalist photography-style composition of [subject], dramatic lighting, muted earth tones. High contrast, editorial."

## Asset Types to Generate

### 1. Hero Illustrations
Full-scene illustrations for onboarding, landing pages, feature sections.
- Size: Generate at highest quality, then resize
- Style: Must match DESIGN-SYSTEM.md visual direction exactly
- Usage: One per major section, not everywhere

### 2. Spot Illustrations
Small, focused illustrations for empty states, tooltips, features.
- Style: Simplified version of the hero style
- Consistency: Same line weight, same color palette, same level of detail across all spots
- Quantity: One per empty state, one per major feature

### 3. Background Patterns/Textures
Subtle visual elements that make the canvas feel alive.
- Opacity: Very subtle (5-15% opacity typically)
- Style: Abstract, organic, or geometric depending on brand
- Usage: Behind hero sections, onboarding, login — not everywhere

### 4. Icon Sets (Custom)
When Lucide icons aren't distinctive enough.
- Style: Must match illustration style
- Weight: Consistent stroke width across all icons
- Coverage: At minimum, the 6-10 primary navigation/feature icons

### 5. Character/Mascot (If Brand Has One)
- Poses: Minimum 5 (greeting, thinking, celebrating, error/sorry, pointing)
- Expressions: Match the brand's emotional range
- Style: Consistent across all poses — same proportions, same line weight
- Usage rules: Defined in DESIGN-SYSTEM.md character system section

### 6. Data Visualization Style
How charts, graphs, and metrics LOOK — not just what they show.
- Color mapping: Which brand colors for which data types
- Style: Rounded vs sharp, filled vs line, animated vs static
- Personality: A chart can have personality — curved lines feel different than angular ones

## Making Apps Look Different From Each Other

The reason all apps look the same is that they share structural patterns (sidebar + cards + text) and have NO visual layer. Here's how to differentiate:

### Layer 1: Color (Easiest)
Different palette = different feel. But this alone isn't enough.

### Layer 2: Typography (Medium)
Different fonts, different scale, different weight distribution. An app using a serif display font feels completely different from one using a geometric sans.

### Layer 3: Layout (Hard, High Impact)
Break the sidebar-cards-text pattern:
- **Full-bleed sections** instead of contained cards
- **Overlapping elements** instead of strict grid
- **Asymmetric layouts** where the "important" side is bigger
- **Scroll-driven reveals** instead of everything visible at once
- **Command palette as primary nav** instead of sidebar
- **Typography as navigation** — giant clickable words instead of icon+label
- **Canvas/spatial** instead of list/grid — elements positioned freely

### Layer 4: Visual Assets (Hard, Highest Impact)
Custom illustrations, characters, patterns, backgrounds. This is what makes an app feel like it has a soul. Two apps with different illustrations feel like different products even if the layout is identical.

### Layer 5: Motion (Bonus)
How things move, appear, and respond. Physics-based interactions, page transitions, micro-animations. This is the difference between "functional" and "alive."

## The "Is It Alive?" Test

Before shipping any screen, ask:
1. Does this screen have at least ONE visual element beyond text and icons?
2. Would removing the logo make this screen indistinguishable from a template?
3. Does the color usage go beyond "accent on buttons"?
4. Is there any motion or visual response to interaction?
5. Would a screenshot of this screen make someone want to use the app?

If any answer is "no," the screen needs more visual life.

## Generating for one app (example)

This app's visual direction (from DESIGN-SYSTEM.md):
- Warm editorial, premium magazine feel
- Indigo accent (#5746AF) on parchment (#F8F7F4)
- No illustrations... BUT this should change. The "no illustrations" rule was a placeholder.

Suggested visual assets for This app:
- **Onboarding hero**: Abstract mast/signal illustration in indigo line art
- **Empty states**: Minimal spot illustrations per section (brand = compass, assets = pen, calendar = clock, analytics = chart, competitors = telescope)
- **Login background**: Subtle warm gradient or organic pattern
- **Score visualization**: Custom radial gauge instead of just "87/100" text
- **Agent chat avatar**: A small distinctive mark or shape, not a generic bot icon
