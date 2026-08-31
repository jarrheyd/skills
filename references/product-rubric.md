# Product-pass rubric

Used by `scout audit --product`. Input: one representative screenshot per screen (deduped from the run's captures; never review the same screen twice). Output: `product-notes.json` as `{ "findings": [{ "screen", "finding", "fix", "shot" }] }`. Only real findings; a clean screen produces no entry.

Check each screen against these, in order:

1. Dead ends and unwired elements. Buttons, links, or menu items that go nowhere or to a placeholder. Anything visible in the screenshot that the flow could not activate.
2. State coverage. Does the screen handle empty, loading, and error states, or does it assume data? An empty screen with no guidance is a finding.
3. Requirement mismatches. When a spec, test script, or ticket was attached to the audit, compare what the screen shows against what it promised. Missing fields, absent features, renamed concepts.
4. Copy. Placeholder text left in, inconsistent terminology across screens, truncated labels, untranslated strings, error messages that blame the user or say nothing actionable.
5. Navigation sense. Can the user tell where they are and how to get back? Orphan screens with no exit, tab bars that vanish, back buttons that skip levels.
6. Data believability. Wrong formats (dates, currency), obviously stale or test data leaking into a screen that a real account would see.
7. Visual breakage. Overlapping elements, clipped text, controls pushed off-screen, keyboard covering the active input.

Rules:

- Every finding pairs with a concrete suggested fix, not just the observation.
- Cosmetic taste is out of scope; report what would confuse, block, or mislead a user.
- Cap the pass at the screens the run actually captured; name any screens that were not captured so the human knows the pass was bounded.
