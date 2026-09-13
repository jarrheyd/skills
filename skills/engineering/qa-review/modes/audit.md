# qa-review audit

The pre-deployment gate: run everything, find what coverage misses, end with an explicit greenlight call. Flags: `--changed` (diff-scoped), `--product` (UX pass).

## 1. Scope

Default: the FULL manifest; regressions land in untouched screens, so pre-deploy never trims. `--changed` only when the user asks for a mid-sprint quick check: map `git diff <base>` touched files to screens to flows (via the routes/screens found in code), run those; name the flows skipped so the result never reads as a full audit.

## 2. Run

`scripts/qa-review-run.sh --repo <repo>` (add `--flows` for the changed set). Read `run-summary.json`; open only failing flows' last screenshots.

## 3. Gap analysis (every audit)

Compare the code's screen/route map against the manifest:

- Screens no flow visits
- Branches without an unhappy-path flow (validation errors, declined payment, empty states, permission denials)
- Manifest entries still `planned: true`

Then a flow-freshness check (rule 8): cross-reference every selector each flow uses against the testIDs present in the current code. A selector with no match is rot, and a rotted flow tests nothing while looking green or red for the wrong reason. Repair rot in this audit, not later.

Write `<run>/gaps.json`: `{ "items": [{ "area", "kind": "happy|unhappy|edge|rot", "note", "flow"?, "selector"? }] }`. Propose the top gaps as new flows; on approval, build them, add manifest entries, and they join the next audit. Coverage ratchets up; it never silently shrinks.

## 4. Product pass (only with --product)

Dedupe the run's screenshots to ONE per screen (by flow + screenshot name). Review each against `references/product-rubric.md`. Write `<run>/product-notes.json`. This is the only mode step that spends tokens on passing screenshots; without the flag, skip entirely.

## 5. Report and verdict

```
node scripts/build-report.mjs --project <p> --manifest ... --config ... --debug <run>/debug \
  --junit <run>/result.xml --out <run>/report.html --gaps <run>/gaps.json \
  [--product <run>/product-notes.json] --build "pre-deploy audit <date>"
```

This rebuild replaces the one the runner made, so open it again: `scripts/open-report.sh <run>/report.html`. Present the run as a regression-test-case matrix and classify every red by class, per `references/regression-report.md`: one numbered case per flow with its status and, when not passing, its class (CRASH / DEFECT / FLOW-ROT / ENV) and evidence; a coverage line; and the production-readiness line. Then the verdict, first line, one of:

- GREENLIGHT: all flows pass, no open CRASH or DEFECT, no BLOCKED case hiding an untested critical journey. Gaps and future flows listed as follow-ups.
- NO-GO: name each open CRASH and DEFECT case and each blocking product finding. What must change, nothing else.

Never greenlight with a red flow "explained away" in prose. A CRASH or DEFECT is fixed in the app first. A FLOW-ROT is repaired and rerun so the final report has no unclassified reds. An ENV failure is retried, never counted against the app.
