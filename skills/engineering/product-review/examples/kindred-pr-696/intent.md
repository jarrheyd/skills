# Save for later reads as a control

Target: https://github.com/symphco/kindred/pull/696 (fix/tap-affordances into development, merged 2026-09-04)
Sources: PR description; the reviewer's own ask in chat ("the save link looks like body text, nobody taps it")
Figma exports: none (no design for this fix)

## Expectations

1. On a Life Story question, "Save for later" looks like a tappable control, not gray body text. (source: chat ask, confirmed 2026-09-04)
2. The control shows a saved state that is visibly different from the unsaved state. (source: PR description)
3. "Share a recipe" is sentence case everywhere it appears as a title. (source: PR description)
4. The recipe import failure title is warm and plain, not a capitalized system message. (source: PR description; confirmed wording 2026-09-04: "We couldn't read that recipe")
5. The save control does not crowd or overlap the question text on a small phone. (source: chat ask, confirmed 2026-09-04)

## Resolved questions

- Does "tappable" mean a button, or an icon plus label? -> Icon plus label in the brand color is enough; a boxed button would be too heavy. (2026-09-04)
- Should the recipe copy change reach the create hub too, or only the intro screen? -> Everywhere the title shows. (2026-09-04)

## Out of scope

- Any change to what "save for later" does after the tap.
