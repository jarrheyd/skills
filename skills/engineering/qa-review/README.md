# qa-review

An e2e audit skill for AI coding agents. Plug it into any web or mobile project and it walks the app the way a user would, keeps screenshot evidence on your machine, and builds one skimmable HTML report you can greenlight a release from.

Maestro does the driving (iOS simulator, Android emulator, or Chrome for web). Plain scripts assemble the report, so the agent spends almost no tokens on evidence and the whole thing works with any model that can run shell commands.

## What it does

- `qa-review smoke`: the fast gate, core flows only, branded pass/fail proof
- `qa-review functional`: runs only the flows this build touched and summarizes the changes
- `qa-review regression`: the full suite, one repeatable command, with a UI and consistency pass, ending in GREENLIGHT or NO-GO (see below)
- `qa-review setup`: reads a project's code, generates flows + a screen-walk + a journey manifest, runs them until green, commits only the YAML. `--blackbox` works from just a staging URL or an installable build when you have no codebase access
- `qa-review run [tag]`: runs flows, builds the report
- `qa-review crosscheck <sheet>`: verifies a QA test-script spreadsheet case by case against the live app (PASS / FAIL / SCRIPT WRONG / NOT WIRED / BLOCKED) and reviews the script itself
- `qa-review audit [--changed] [--product]`: the pre-deploy gate: full run, coverage gap analysis, optional UX pass, ends in GREENLIGHT or NO-GO
- `qa-review review <script>`: reviews or writes a QA test script without driving the app

## Where things go

- Committed to your repo: `.maestro/flows/*.yaml`, `journeys.manifest.json`, `qa-review.config.json`. A few KB; the flows are team assets.
- Your machine only: `~/.qa-review/<project>/` with your `.env` (test credentials, you fill it) and `runs/` (screenshots, JUnit, `report.html`). The last 2 runs are kept, older ones auto-pruned.
- Never: screenshots or reports in the repo, credentials anywhere but your `.env`, runs against production (the guard refuses any target whose hostname labels or bundle-id segments carry no dev/staging/test marker, and checks every flow's own `url:` too).

Note: `buildCmd` and `installCmd` in the committed `qa-review.config.json` are executed by the runner. Treat that file like a build script: review changes to it in code review.

## Install

As part of the `jarrheyd-skills` plugin:

```bash
claude plugin marketplace add jarrheyd/skills
claude plugin install jarrheyd-skills@jarrheyd
```

Or as editable files through skills.sh:

```bash
npx skills@latest add jarrheyd/skills --skill=qa-review
```

Claude Code picks it up as `/qa-review`. One name throughout: `qa-review.config.json`, `qa-review-run.sh`, `QA_REVIEW_*` env vars, and `~/.qa-review/` as the evidence root. A project onboarded before this rename needs those four renamed; `MIGRATING.md` has the commands. For other agents, point them at `SKILL.md`; everything is plain markdown and scripts.

Prerequisites:

```bash
curl -fsSL "https://get.maestro.mobile.dev" | bash   # maestro, adds ~/.maestro/bin
brew install --cask temurin                           # Java runtime (macOS)
```

iOS projects need Xcode with a simulator. Android needs `adb` on PATH and a running emulator or device (`platform: android`, best-effort: the runner picks the first online device). Screenshots are downscaled with macOS `sips`; on Linux they embed at full size and the report gets larger.

## Quickstart

```bash
cd your-app
claude
> /qa-review setup
# answer the env questions, fill ~/.qa-review/<project>/.env with test creds
> /qa-review audit
# open the report and greenlight
```

## Regression for a QA team

One command, the same pass every time, on any project that has been set up:

```bash
node <skill>/scripts/qa-review-doctor.mjs --repo .     # is this project ready? fixes listed per item
<skill>/scripts/qa-review-regression.sh --repo .       # the full pass
```

Or ask the agent: `/qa-review regression`. The script:

1. Checks every flow's selectors against the current code and lists the stale ones.
2. Builds the app, installs it, and reseeds test data (`seedCmd`), so a deleted fixture never breaks a run.
3. Runs every flow one at a time. A stuck driver is killed before each flow, and each red flow gets one retry.
4. Runs multi-step scenarios through the project's own scripts (`scenarios`), in order, with their results filed into the same report.
5. Resumes until every flow has a result. `--resume` continues the newest run after a stop, without rebuilding.
6. Collects every screen it captured into `<run>/ui-review/` for the UI and consistency pass.

The agent then classifies every red (crash, defect, stale flow, environment), repairs stale flows and reruns them, reviews every screen against the design doc and `uiRules`, and publishes the branded report.

GREENLIGHT means zero crashes, zero defects, zero UI blockers, and a fresh result for every flow. Anything else is NO-GO with each blocker named. A screen that passes its test but looks broken is a UI blocker, not a pass.

Keep test runs out of product analytics. Before the first regression, make the app skip analytics on a simulator or emulator, and have the backend skip test accounts. The doctor warns when the app uses analytics without such a switch.

## Config keys

`.maestro/qa-review.config.json`, committed, never secrets. Start from `templates/qa-review.config.json`.

| Key | Needed | What it does |
| --- | --- | --- |
| `project` | yes | Name for `~/.qa-review/<project>/` (credentials, runs) |
| `platform` | yes | `mobile` (iOS simulator), `android`, or `web` |
| `appId` / `url` | yes | Dev or staging bundle id, or web URL. Production is refused |
| `simulator` | iOS | Device name to boot or reuse |
| `buildCmd`, `installCmd` | recommended | Build and install the current code. `installCmd` can target `${QA_REVIEW_UDID}` |
| `seedCmd` | recommended | Resets test data before each run. Its `KEY=VALUE` output lines go into the local `.env` for the flows |
| `excludeFlows` | optional | Globs for throwaway flows kept out of the suite |
| `flowSetup` | optional | `{ "glob": "command" }`: prepares one flow's own data right before it; the output reaches only that flow |
| `scenarios` | optional | `[{ name, cmd, flows }]`: an ordered script the project already has (API steps between flows). Its flows run inside it, not one by one |
| `scenarioEnv` | optional | Environment exported for scenario scripts (target env, API base) |
| `errorCopy` | optional | The app's literal error strings; every screen asserts they are not visible |
| `envKeys` | optional | Credential keys each QA fills in `~/.qa-review/<project>/.env` |
| `designDoc`, `uiRules` | recommended | What the UI and consistency pass checks every screen against |

## Layout

```
SKILL.md          entry point + hard rules
modes/            one file per mode, loaded on demand
scripts/          runner, report builder, summarizer, pruner, prod guard
templates/        manifest, config, screen-walk, _login, flow header
references/       flow conventions, verdicts, product rubric, web driving
```

