# Intent model template

Saved at `~/.product-review/<project>/<feature>.md`. Local only; holds the user's candid expectations.

```markdown
# <feature name>

Target: <PR link / branch / URL>
Sources: <ticket key + link>, <Figma link>, <PR>, <chat message ref>
Figma exports: shots/expected/<frame>.png (when pulled)

## Expectations

1. <one sentence, observable> (source: ticket AC-2)
2. <one sentence, observable> (source: Figma frame "Cart"; confirmed 2026-09-01)
3. <one sentence, observable> (source: user, grilled 2026-09-01: "empty circle shows the invite prompt, not a blank list")

## Resolved questions

- <the question asked> -> <the user's answer, dated>

## Out of scope (explicitly not expected)

- <things the user said do not matter for this review>
```

Rules: every expectation is checkable on a screen or in behavior; vague lines get split during the grill. `confirmed <date>` marks answers that came from the user rather than a document. Re-reviews update this file instead of starting over.
