# qa-review regression

The full suite: every flow, classified, ending in a production-readiness verdict. It replaces a QA team's hand-written regression scripts. It seeds from those scripts if they exist, generates the suite from code if they do not, and it owns and keeps the suite fresh so QA reviews the matrix instead of writing cases.

The two things that made past full regressions never finish, solved here together: the run resumes after a wedge instead of restarting, and stale flows are repaired before the run counts.

## First time on a repo: seed or generate the suite

- QA already has regression scripts (a sheet or doc): import them once with `crosscheck` (`modes/crosscheck.md`) to seed coverage, then keep the resulting flows in `.maestro/flows/` as the owned suite.
- No scripts exist: generate the suite from the code with `setup` (`modes/setup.md`), one flow per journey plus the screen-walk.
Either way the suite lives in `.maestro/`, and from here the library owns it.

## Every run (one command)

The mechanical part is one script, so anyone can run it and get the same pass:

```
scripts/qa-review-regression.sh --repo <repo>
```

It does, in order: freshness check, build, install, seed (config `seedCmd`, fresh fixture ids merged into the local `.env`), every flow one by one with wedge recovery, each red retried once, `--resume` until every flow has a result, then the UI review set (`<run>/ui-review/`). Throwaway flows are left out by config `excludeFlows`. The last line it prints is the run dir.

Then the agent:

1. Freshness. Read the freshness output (`~/.qa-review/<project>/gaps.json`). Selectors built from template strings in code (`${testID}-toggle`) show up as false alarms; confirm each against the code. Repair real rot and rerun just those flows: `scripts/qa-review-run.sh --repo <repo> --resume` (reruns the missing and failed ones in the same run dir).
2. Classify every red. Read `<run>/run-summary.json` only. For each red, open its `lastScreenshot` and classify it (crash / defect / flow-rot / env) per `references/regression-report.md`. Repair flow-rot in the same session and rerun it with `--resume`. A crash or defect is a release blocker.
3. UI and consistency pass. Review every screen in `<run>/ui-review/` against `references/ui-consistency.md`, the app's `designDoc` and `uiRules`. Write `<run>/ui-findings.json`. A screen that passed its flow but looks broken is a `blocker` finding, not a pass. This step is not optional: functional flows alone keep missing visual defects.
4. Build and publish the branded proof (`references/publish.md`), passing `--gaps` and `--product <run>/ui-findings.json`. Present it as the numbered regression-test-case matrix with the production-readiness line.
5. Verdict: GREENLIGHT only when zero crashes, zero defects, zero UI blockers, and every flow has a fresh result. Otherwise NO-GO, naming each blocker.

## Test runs stay out of product analytics

A regression must not pollute the dashboard the team reads. Before the first run on a project, make sure test traffic cannot reach it: the app should not report from a simulator or emulator, and the backend should skip test accounts (for Kapwa: `isSimulator()` in the mobile analytics service, and the server skips users whose phone is on `TEST_OTP_SILENT_NUMBERS`). If a project has no such switch, add one before running, or say plainly in the report that the run was recorded.

## Coverage upkeep (why QA reviews, not writes)

Each run's gap analysis (from `audit.md`, rule 8) lists screens no flow visits and branches with no unhappy-path flow. Add flows to close real gaps so the suite stays complete. QA reviews the matrix and the gaps, and signs off. They no longer hand-author cases.
