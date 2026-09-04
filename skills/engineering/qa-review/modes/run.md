# qa-review run

Run flows and hand the human the report. The cheap, everyday mode.

## Steps

1. Locate the repo's `.maestro/scout.config.json` (no config: switch to setup mode).
2. Run: `scripts/scout-run.sh --repo <repo> [--tag <tag>] [--flows "<a.yaml b.yaml>"]`
   - `--tag smoke` (or `critical`) for the quick gate; no tag runs everything
   - The script handles guard-env, simulator/build, env injection, retry-once, summary, report, pruning
   - Reuse an installed build with `SCOUT_SKIP_BUILD=1` when the user says the build has not changed
3. Read `<run>/run-summary.json`. ONLY that file.
4. For each failed flow: open its `lastScreenshot`, state what broke in one line each. Do not open passing flows' screenshots.
5. Open the report for the human (`open <run>/report.html`).
6. Report: pass/fail count, the greenlight line, each failure with its one-line cause, any flow marked `retried` (it passed only on the second try: say so, a flake is a finding), where the report is.

## Fixing failures

Only when the user asks (or the invocation was "run and fix"): distinguish app bug (report it, do not paper over it) from flow rot (selector/copy drift: fix the flow, rerun just it with `--flows`). Never mark a journey-critical step `optional:` to force green.
