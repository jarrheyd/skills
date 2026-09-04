# qa-review

An e2e audit skill for AI coding agents. Plug it into any web or mobile project and it walks the app the way a user would, keeps screenshot evidence on your machine, and builds one skimmable HTML report you can greenlight a release from.

Maestro does the driving (iOS simulator, Android emulator, or Chrome for web). Plain scripts assemble the report, so the agent spends almost no tokens on evidence and the whole thing works with any model that can run shell commands.

## What it does

- `qa-review setup`: reads a project's code, generates flows + a screen-walk + a journey manifest, runs them until green, commits only the YAML. `--blackbox` works from just a staging URL or an installable build when you have no codebase access
- `qa-review run [tag]`: runs flows, builds the report
- `qa-review crosscheck <sheet>`: verifies a QA test-script spreadsheet case by case against the live app (PASS / FAIL / SCRIPT WRONG / NOT WIRED / BLOCKED) and reviews the script itself
- `qa-review audit [--changed] [--product]`: the pre-deploy gate: full run, coverage gap analysis, optional UX pass, ends in GREENLIGHT or NO-GO
- `qa-review review <script>`: reviews or writes a QA test script without driving the app

## Where things go

- Committed to your repo: `.maestro/flows/*.yaml`, `journeys.manifest.json`, `scout.config.json`. A few KB; the flows are team assets.
- Your machine only: `~/.scout/<project>/` with your `.env` (test credentials, you fill it) and `runs/` (screenshots, JUnit, `report.html`). The last 2 runs are kept, older ones auto-pruned.
- Never: screenshots or reports in the repo, credentials anywhere but your `.env`, runs against production (the guard refuses any target whose hostname labels or bundle-id segments carry no dev/staging/test marker, and checks every flow's own `url:` too).

Note: `buildCmd` and `installCmd` in the committed `scout.config.json` are executed by the runner. Treat that file like a build script: review changes to it in code review.

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

Claude Code picks it up as `/qa-review`. Saying "scout" still triggers it: that was the original name, and the internal names stay put so projects onboarded under it keep working (`scout.config.json`, `scout-run.sh`, `SCOUT_*` env vars, the `~/.scout/` evidence root). For other agents, point them at `SKILL.md`; everything is plain markdown and scripts.

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
# answer the env questions, fill ~/.scout/<project>/.env with test creds
> /qa-review audit
# open the report, greenlight or not
```

## Layout

```
SKILL.md          entry point + hard rules
modes/            one file per mode, loaded on demand
scripts/          runner, report builder, summarizer, pruner, prod guard
templates/        manifest, config, screen-walk, _login, flow header
references/       flow conventions, verdicts, product rubric, web driving
```

