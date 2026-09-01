# qa-review

An e2e audit skill for AI coding agents. Plug it into any web or mobile project and it walks the app the way a user would, keeps screenshot evidence on your machine, and builds one skimmable HTML report you can greenlight a release from.

Maestro does the driving (simulator for mobile, Chrome for web). Plain scripts assemble the report, so the agent spends almost no tokens on evidence and the whole thing works with any model that can run shell commands.

## What it does

- `scout setup`: reads a project's code, generates flows + a screen-walk + a journey manifest, runs them until green, commits only the YAML. `--blackbox` works from just a staging URL or an installable build when you have no codebase access
- `scout run [tag]`: runs flows, builds the report
- `scout crosscheck <sheet>`: verifies a QA test-script spreadsheet case by case against the live app (PASS / FAIL / SCRIPT WRONG / NOT WIRED / BLOCKED) and reviews the script itself
- `scout audit [--changed] [--product]`: the pre-deploy gate: full run, coverage gap analysis, optional UX pass, ends in GREENLIGHT or NO-GO
- `scout review <script>`: reviews or writes a QA test script without driving the app

## Where things go

- Committed to your repo: `.maestro/flows/*.yaml`, `journeys.manifest.json`, `scout.config.json`. A few KB; the flows are team assets.
- Your machine only: `~/.scout/<project>/` with your `.env` (test credentials, you fill it) and `runs/` (screenshots, JUnit, `report.html`). The last 2 runs are kept, older ones auto-pruned.
- Never: screenshots or reports in the repo, credentials anywhere but your `.env`, runs against production (the guard refuses non-dev-looking targets).

## Install

```bash
git clone https://github.com/jarrheyd/qa-review ~/.claude/skills/qa-review
```

Claude Code picks it up as `/qa-review` (the original name was scout; the internal names `scout.config.json`, `scout-run.sh`, `SCOUT_*` env vars, and the `~/.scout/` evidence root are kept so projects onboarded under the old name keep working). For other agents, point them at `SKILL.md`; everything is plain markdown and scripts.

Prerequisites:

```bash
curl -fsSL "https://get.maestro.mobile.dev" | bash   # maestro, adds ~/.maestro/bin
brew install --cask temurin                           # Java runtime (macOS)
```

Mobile projects also need Xcode with a simulator (or an Android emulator).

## Quickstart

```bash
cd your-app
claude
> /scout setup
# answer the env questions, fill ~/.scout/<project>/.env with test creds
> /scout audit
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

## License

MIT
