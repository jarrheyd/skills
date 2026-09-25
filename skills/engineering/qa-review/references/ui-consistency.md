# UI and consistency pass

The part functional flows miss. A flow can pass every testID and still ship a screen that looks broken. This pass looks at every screen a run captured and reports what a careful human would.

## Inputs

- `<run>/ui-review/index.json` and its downscaled screens, built by `scripts/ui-gallery.mjs` (the regression wrapper does this).
- The app's design doc, `designDoc` in `qa-review.config.json` (for Kapwa `apps/mobile/DESIGN.md`). Skim its rules once per run.
- The app's own rules, `uiRules` in `qa-review.config.json`. Each is a short sentence a screen either follows or breaks.

## How to review (token budget)

Look at screens in batches of 6 to 10, grouped by flow. Every screen gets looked at once; do not reopen full-size shots unless a finding needs a closer look. Compare screens of the same kind across flows (every bottom sheet, every card, every header) because inconsistency only shows side by side.

## What counts as a finding

Always check:
1. Text cut off, truncated with "..." on a button or title, or overlapping other text.
2. A single word alone on the last line of a sentence (an orphan).
3. Buttons with no label, a label that does not fit, or an action pushed off screen or under the keyboard or home indicator.
4. The same component looking different on two screens (card, header, sheet grabber, empty state, button shape, icon for the same action).
5. Two primary buttons competing in one region; a destructive action styled as primary.
6. Wrong or generic loader, stuck spinner, blank screen, placeholder text left in.
7. Cramped or uneven spacing against the rest of the app; content touching the screen edge.
8. Casing that breaks the app's rule (titles, buttons, tabs).
9. A dead end: no way back, a sheet that cannot close, an action that opened the wrong thing.
10. Any rule in `uiRules` broken.

Not a finding: seeded test data looking odd (names like "Test"), a keyboard being open, simulator status bar.

## Output

Write `<run>/ui-findings.json`:

```json
{ "title": "UI and consistency", "sub": "Every captured screen reviewed against the design rules.",
  "findings": [ { "screen": "<flow> / <screenshot name>", "severity": "blocker|fix|polish",
                  "finding": "what is wrong, plainly", "fix": "the concrete change", "shot": "<source png path from index.json>" } ] }
```

Severity: `blocker` means a user cannot finish the task or the screen looks broken (counts against GREENLIGHT like a defect). `fix` is a visible inconsistency to correct before launch. `polish` is minor. Pass it to the report with `--product <run>/ui-findings.json`.

Plain words in findings: say what a user sees ("the Save button is cut off to 'Sa...'"), not the component name.
