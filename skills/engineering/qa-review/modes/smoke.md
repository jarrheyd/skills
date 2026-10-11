# qa-review smoke

The fast gate: run the core flows, hand back a branded pass/fail proof. Use it after a change set, before a commit, or any time you want a quick "does the app still work".

## Steps

1. Locate the repo's `.maestro/qa-review.config.json` (no config: switch to setup mode).
2. Refresh the brand so the proof wears the app's own look:
   `node scripts/detect-brand.mjs --repo <repo> --project <name>`
   (writes `~/.qa-review/<name>/brand.json`; a miss falls back to a neutral palette, never blocks).
3. Run the core flows:
   `scripts/qa-review-run.sh --repo <repo> --tag smoke`
   - `smoke` is the fixed core set; use `--tag critical` if that is the app's crash-guard tag.
   - The script handles guard-env, build/simulator, env injection, per-flow isolation, wedge recovery, retry-once, summary, report, pruning, and opening the report.
   - `QA_REVIEW_SKIP_BUILD=1` reuses the installed build when the user says nothing changed.
4. Read `<run>/run-summary.json`. ONLY that file. For each failed flow open its `lastScreenshot` and say what broke in one line.
5. The report at `<run>/report.html` is already brand-themed from `brand.json`. To publish a shareable link, follow `references/publish.md`.
6. Report: pass/fail count, the greenlight line, each failure with its one-line cause, any `retried` flake, and the report path or published link.

Smoke never edits flows or app code. A red is a finding, not something to paper over. Deeper coverage is `functional` (what changed) or `regression` (everything).
