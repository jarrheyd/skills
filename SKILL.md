---
name: qa-review
description: (alias "scout") Maestro e2e audit skill for any web or mobile app. Walks the app screen per screen, captures evidence, and builds a skimmable local HTML report for QA and product review. Use when the user says "scout", wants to set up e2e flows, run a pre-deployment audit, cross-check a QA test script against the live app, review or author a test script, or wants screenshot proof that flows work before greenlighting a release.
version: 1.0.0
user-invocable: true
argument-hint: "[setup|run|crosscheck|audit|review] [target]"
license: MIT
---

# qa-review

Drive the app the way a user would, keep the proof, and let a human greenlight from one report. Maestro runs the flows on a simulator (mobile) or Chrome (web); scripts assemble the evidence; the AI reads only a small summary. Works with any AI agent that can run shell commands.

## Modes

| Invocation | Mode file | What it does |
| --- | --- | --- |
| `scout setup` | `modes/setup.md` | Bootstrap a project: generate flows, manifest, screen-walk from the code |
| `scout run [tag]` | `modes/run.md` | Run flows (optionally one tag), build the report |
| `scout crosscheck <sheet-or-file>` | `modes/crosscheck.md` | Verify a QA test script case by case against the live app |
| `scout audit [--changed] [--product]` | `modes/audit.md` | Pre-deployment full audit + coverage gap analysis |
| `scout review <script>` | `modes/review.md` | Review or author a QA test script without driving the app |

Read ONLY the mode file for the invoked mode. If no mode is named, ask which one, or infer it: a spreadsheet or test script link means crosscheck; "before we ship / deploy" means audit; a repo with no `.maestro/` means setup.

## Where things live

- Target repo (committed, the only repo footprint): `.maestro/flows/*.yaml`, `.maestro/journeys.manifest.json`, `.maestro/scout.config.json`
- Local device (never committed): `~/.scout/<project>/` holds `.env` (credentials, user-filled) and `runs/<timestamp>/` (Maestro debug output, screenshots, JUnit XML, `run-summary.json`, `report.html`)
- Skill scripts: `scripts/` in this skill directory. Call them with absolute paths; they take the project via `--project <name>` or `SCOUT_PROJECT`.

`scout.config.json` (committed, no secrets): `{ "project": "<name>", "platform": "mobile|web", "appId" | "url", "buildCmd", "installCmd", "errorCopy": ["..."], "envKeys": ["SCOUT_USER", ...] }`.

## Hard rules (every mode)

1. Token efficiency. Scripts do the driving and the report assembly. After a run, read `run-summary.json` only. Open a screenshot only when its step failed or a mode explicitly flags it. Never page through full filmstrips; the human does that in `report.html`.
2. Credentials live only in `~/.scout/<project>/.env`. You write placeholder keys, the user fills values. Never read the values back into chat, never put them in flows (flows use `${SCOUT_USER}`-style env refs), never screenshot a password on screen.
3. Never production. `scripts/guard-env.sh` runs before every suite. If the target does not look like dev/staging/localhost it refuses; only the user exporting `SCOUT_ALLOW_PROD=1` overrides it. Test or staging accounts only.
4. Fail loud. Never swallow a failing step to keep a run green. A bounded or skipped check is named in the summary so "passed" never quietly means "did not run".
5. Finish with the report. Every run ends by opening `report.html` for the human (`open` on macOS, `xdg-open` on Linux). The report is the deliverable; your text is a short verdict on top of it.
6. Repo hygiene. Nothing generated lands in the target repo except flows, manifest, and config. If a project insists on in-repo output, append `templates/gitignore-snippet` to its `.gitignore` first.

## Flow-writing rules

Follow `references/conventions.md` for every flow you write or edit. Short version: testID selectors first, `_`-prefixed reusable partials via `runFlow:`, numbered `takeScreenshot: 01-name` steps at the moments that matter, `assertNotVisible` with the app's literal error copy after every screen, idempotent conditional steps for shared accounts, bounded repeats, explicit timeouts.

## Prerequisites (check before first run)

- `maestro` on PATH (`~/.maestro/bin`); install: `curl -fsSL "https://get.maestro.mobile.dev" | bash`
- A Java runtime (Maestro needs it): `brew install --cask temurin` on macOS
- Mobile: Xcode + booted simulator, or Android emulator. Web: Chrome.

## References

| File | Purpose |
| --- | --- |
| `references/conventions.md` | Flow YAML rules distilled from production suites |
| `references/verdicts.md` | Crosscheck verdict definitions + evidence bar |
| `references/product-rubric.md` | The `--product` UX review rubric |
| `references/web-driving.md` | Maestro on web: url config, selectors, quirks |
