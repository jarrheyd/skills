# Phase 3: verdict

One verdict per intent item, then one overall call. Every verdict cites a screenshot or a named code place. Plain language throughout.

## Per-expectation verdicts

- MATCHES: built as expected. Cite the screenshot. Note stays empty.
- DRIFTED: built, but differently. The note shows expected vs actual in one breath ("you expected the invite on the circle page; it is inside the settings menu") and says whether the drift reads deliberate (a consistent pattern elsewhere) or accidental. Never assume bad intent; the builder may have had a reason, which is exactly what the conversation is for.
- MISSING: expected, not there or not connected. "The button exists but tapping it does nothing" is MISSING with the screenshot of the dead end.
- EXTRA: built, never asked for. Neutral flag: could be scope creep, could be a good call the user should know about. Name what it is and roughly what it must have cost.
- CAN'T TELL: the state or screen was unreachable (needs data, an account role, a build). The note names exactly what would unlock it. Never guess from code alone when the expectation is visual.

## The overall call

- ALIGNED: no MISSING, no accidental-looking DRIFTED, EXTRAs are minor. Say it plainly and list any small notes.
- NEEDS A CONVERSATION: name the 2 or 3 items to discuss with the team, most consequential first. This is an agenda, not a rejection; there is no "failed" overall verdict by design.

## Rules

- An expectation not in the confirmed intent model produces no verdict. Notice something off outside the model: put it under EXTRA observations at the end, clearly separated, and offer to add it to the model for next time.
- Code quality issues spotted along the way: one line, "worth a /code-review pass", nothing more.
- Write `review.json` in the review folder: `{ "feature", "target", "overall": "ALIGNED|NEEDS A CONVERSATION", "items": [{ "n", "expectation", "verdict", "note", "actual": "<shot path>", "expected": "<figma export path>", "code": "<file:line>" }], "extras": ["..."], "bounds": ["code-only", "screen X unreachable"] }`. The report builder renders from this file.
