# qa-review audit

The pre-deployment gate: run everything, find what coverage misses, end with an explicit greenlight call. Flags: `--changed` (diff-scoped), `--product` (UX pass).

## 1. Scope

Default: the FULL manifest; regressions land in untouched screens, so pre-deploy never trims. `--changed` only when the user asks for a mid-sprint quick check: map `git diff <base>` touched files to screens to flows (via the routes/screens found in code), run those; name the flows skipped so the result never reads as a full audit.

## 2. Run

`scripts/scout-run.sh --repo <repo>` (add `--flows` for the changed set). Read `run-summary.json`; open only failing flows' last screenshots.

## 3. Gap analysis (every audit)

Compare the code's screen/route map against the manifest:

- Screens no flow visits
- Branches without an unhappy-path flow (validation errors, declined payment, empty states, permission denials)
- Manifest entries still `planned: true`

Write `<run>/gaps.json`: `{ "items": [{ "area", "kind": "happy|unhappy|edge", "note" }] }`. Propose the top gaps as new flows; on approval, build them, add manifest entries, and they join the next audit. Coverage ratchets up; it never silently shrinks.

## 4. Product pass (only with --product)

Dedupe the run's screenshots to ONE per screen (by flow + screenshot name). Review each against `references/product-rubric.md`. Write `<run>/product-notes.json`. This is the only mode step that spends tokens on passing screenshots; without the flag, skip entirely.

## 5. Report and verdict

```
node scripts/build-report.mjs --project <p> --manifest ... --config ... --debug <run>/debug \
  --junit <run>/result.xml --out <run>/report.html --gaps <run>/gaps.json \
  [--product <run>/product-notes.json] --build "pre-deploy audit <date>"
```

Open it. Then the verdict, first line, one of:

- GREENLIGHT: all flows green, no blocking product findings. Gaps listed as future work.
- NO-GO: name each failing flow and blocking finding. What must change, nothing else.

Never greenlight with a red flow "explained away" in prose; fix the flow or the app first, or say NO-GO.
