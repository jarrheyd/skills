# Example: Kindred PR 696, code-only

A recorded product-review run against a real, merged pull request, so the skill's output has a proven shape to copy. It ran in code-only mode: no build or simulator, the diff is the evidence, and the one visual expectation stays CAN'T TELL on purpose.

- `intent.md`: the confirmed intent model, in the `references/intent-model.md` shape.
- `review.json`: the verdicts, each citing a file and line in the diff.
- `report.html`: what `scripts/build-review.mjs` renders from `review.json`.

Rebuild the report:

```bash
node scripts/build-review.mjs --review examples/kindred-pr-696/review.json --out examples/kindred-pr-696/report.html
```
