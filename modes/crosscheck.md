# qa-review crosscheck

Verify a QA test script case by case against the live app, then review the script itself. Verdicts and evidence rules: `references/verdicts.md`.

## 1. Ingest the script

- Google Sheet: read it via the available Drive/Sheets tool, or the export URL (`.../export?format=csv&gid=<gid>`); multi-tab sheets: ask which tab, or take the one named like "test cases"
- xlsx/csv file: parse locally
- Normalize into cases: `{ id, title, preconditions, steps[], expected }`. Ambiguous rows (merged cells, prose blobs) are normalized best-effort and flagged in the script review.

## 2. Map cases to flows

For each case, in order of preference: an existing committed flow already covers it (reuse, note the mapping); a small variation of one (parameterize or extend); nothing covers it (write a temp flow under `flows/tmp-<caseid>.yaml` following `references/conventions.md`). Group cases sharing a path into one flow with numbered screenshots per case checkpoint; one flow per case is wasteful.

## 3. Run

`scripts/scout-run.sh --repo <repo> --flows "<the mapped flows>"`. Missing creds or env: those cases become BLOCKED, the rest still run.

## 4. Verdicts

Read `run-summary.json`. Open screenshots only where needed to decide between FAIL / SCRIPT WRONG / NOT WIRED (a JUnit failure alone cannot tell you which; the screenshot can). Write `~/.scout/<project>/runs/<run>/crosscheck.json`:

```json
{ "source": "<sheet name>", "cases": [{ "id", "title", "verdict", "note", "evidence" }], "scriptReview": ["..."] }
```

Every non-PASS note is actionable: FAIL notes name the breaking step and behavior; SCRIPT WRONG notes give current text and replacement; NOT WIRED notes say where the journey dead-ends; BLOCKED notes name the exact blocker.

## 5. Script review

The `scriptReview` list, per `references/verdicts.md`: missing unhappy/edge cases per screen touched, ambiguous steps, untestable expectations, duplicates, missing preconditions. Current / should-be / paste-ready form.

## 6. Report

Rebuild with the crosscheck section:

```
node scripts/build-report.mjs --project <p> --manifest <repo>/.maestro/journeys.manifest.json \
  --config <repo>/.maestro/scout.config.json --debug <run>/debug --junit <run>/result.xml \
  --out <run>/report.html --crosscheck <run>/crosscheck.json --build "crosscheck <sheet> <date>"
```

Open it. Summarize: verdict tally, every FAIL and NOT WIRED named individually, top script-review fixes. Clean up `tmp-*.yaml` flows unless the user wants any promoted into the manifest (offer that: a crosschecked case is a free regression test).
