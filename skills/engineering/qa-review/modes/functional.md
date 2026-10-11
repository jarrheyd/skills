# qa-review functional

Change-scoped proof: work out what this build changed, run the flows that cover it, and publish a branded proof that summarizes the changes and shows the results. This is the mode you run before marking a feature done, and it produces the shareable release proof.

## Steps

1. Locate `.maestro/qa-review.config.json` (no config: switch to setup mode). Refresh the brand:
   `node scripts/detect-brand.mjs --repo <repo> --project <name>`.
2. Find the affected flows:
   `node scripts/changed-flows.mjs --repo <repo> [--base <commit|tag>]`
   - Base defaults to the last certified proof commit in `~/.qa-review/<name>/.last-proof.json`, then the last git tag, then `HEAD~1`.
   - Reads the testIDs the changed screens emit and matches them to flows. Writes `changed.json` with `affected`, `skipped`, and `broad`.
   - If `broad` is true, the change touches a shared or central file and fans out to most flows. Run `regression` instead and say why.
3. Check freshness on the affected set and repair rot before the run counts:
   `node scripts/check-flow-freshness.mjs --repo <repo>`; for each `{kind:"rot"}` item on an affected flow, fix the selector against the current testID, then continue. A flow that fails on a stale selector tests nothing.
4. Run the affected flows:
   `scripts/qa-review-run.sh --repo <repo> --flows "<space-separated affected basenames>"`.
5. Read `<run>/run-summary.json` only. Open a failed flow's `lastScreenshot` to classify it (crash / defect / flow-rot / env per `references/regression-report.md`).
6. Write the change summary the proof leads with: plain, outcome-based, grouped by product area, in the app's own voice, from `git log <base>..HEAD` plus the diff. What a user would notice, not commit messages. Follow the copy rules in `references/publish.md` (deslopped, no jargon).
7. Build and publish the branded proof, and name the skipped flows so it never reads as a full pass. Follow `references/publish.md`: it rebuilds the report with the brand and change summary, publishes the shareable link, and stamps `.last-proof.json` with this commit so the next functional run diffs from here.
8. Report: what changed (the summary), affected vs skipped counts, pass/fail with any red's class, and the published link.

Functional never silences a red to ship. A real defect is a blocker; a flow-rot is repaired and rerun; an env failure is named and retried.
