# Publishing the branded proof

Every mode's report is already themed from `~/.qa-review/<project>/brand.json` (the runner passes `--project`, and `build-report.mjs` auto-loads the brand). This file covers turning that report into a shareable link, the change-summary copy, and stamping the certified commit.

## 1. Rebuild with the extras (functional and regression)

The runner builds a plain results report. To add the change summary (functional), or the gaps matrix and UI findings (regression), rebuild it with the matching optional flags:

```
node scripts/build-report.mjs \
  --project <name> \
  --manifest <repo>/.maestro/journeys.manifest.json \
  --config   <repo>/.maestro/qa-review.config.json \
  --debug    <run>/debug \
  --junit    "<run>/result-*.xml joined by commas" \
  --brand    ~/.qa-review/<name>/brand.json \
  --summary  ~/.qa-review/<name>/change-summary.html   (functional only) \
  --gaps     ~/.qa-review/<name>/gaps.json             (regression only) \
  --product  <run>/ui-findings.json                    (regression: the UI and consistency pass) \
  --out      <run>/report.html
```

Smoke needs no rebuild; its report is already branded.

## 2. Change summary for functional

Write it to `~/.qa-review/<name>/change-summary.html` (or plain text) before the rebuild. Rules:

- Outcome-based and grouped by product area. What a user would notice, not commit messages or ticket ids.
- The app's own voice and tone, sampled from its UI copy. Warm apps read warm, terse tools read terse.
- Deslopped: no em dashes, no filler, no banned words, plain language a non-engineer gets in one pass.
- Name the flows that were skipped (the ones outside the change) so the proof never reads as a full pass.

## 3. Publish the link

The report is one self-contained HTML file with its screenshots, fonts, and logo embedded. Publish `<run>/report.html` with the Artifact tool for a hosted link, with a one-line description in the app's voice.

Publishing is agent-side. When the agent cannot publish (not Claude Code), hand over the local `report.html` path instead; it is fully portable.

Caveat to state when sharing externally: a published artifact is private by default, so a client or tester needs access granted before the link opens. Share the screenshots directly when they do not have access.

## 4. Stamp the certified commit

After a green proof, record what it certified so the next functional run diffs from here. Write `~/.qa-review/<name>/.last-proof.json` with `commit` (the `git rev-parse HEAD` of the repo), `artifactUrl` (the published link), `buildHash` (from `<run>/build.json`), and `at` (now).

Only stamp on a green proof. A red run leaves the previous baseline in place so the next run still sees the un-certified changes.
