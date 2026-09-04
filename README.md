# jarrheyd/skills

Agent skills I use every day, shipped as one Claude Code plugin and as editable files for any Agent-Skills harness.

- **[deslop](./skills/writing/deslop/SKILL.md)** (started at [jarrheyd/deslop](https://github.com/jarrheyd/deslop), now archived): a quality gate for AI-generated tells. Three hooks block AI copy tells, AI-default visual tells, and both again on artifacts and Drive docs, before they ship. Plus a manual review with a detector and a humanizer agent.
- **[qa-review](./skills/engineering/qa-review/SKILL.md)**: Maestro e2e audits for web and mobile. Walks the app like a user, keeps screenshot evidence on your machine, and ends in one HTML report you greenlight a release from. Also cross-checks a QA test script against the live app.
- **[product-review](./skills/engineering/product-review/SKILL.md)**: is what got built the thing that was asked for? Builds an intent model from the ticket, the design, and you, then judges the PR or the deployed app against it, in plain language, with pictures.

## Install

Claude Code, as a plugin (managed, read-only, updates with the repo):

```bash
claude plugin marketplace add jarrheyd/skills
claude plugin install jarrheyd-skills@jarrheyd
```

Any other agent, or editable files, through [skills.sh](https://skills.sh):

```bash
npx skills@latest add jarrheyd/skills
```

Pick one route. Installing both leaves you with every skill twice. skills.sh users who want the deslop hooks wire them by hand; the snippet is in [deslop's README](./skills/writing/deslop/README.md#install).

## Prerequisites

- deslop: Python 3.
- qa-review: [Maestro](https://maestro.mobile.dev) and a Java runtime; Xcode with a simulator for iOS, `adb` for Android, Chrome for web.
- product-review: `gh` for pull requests. Figma, Jira and Wrike access are optional and only improve the intent phase.

## Layout

```
skills/writing/deslop            the gate
skills/engineering/qa-review     e2e audits
skills/engineering/product-review  built vs intended
hooks/hooks.json                 the deslop hooks the plugin wires
tests/                           node:test + unittest, run with npm test
.claude-plugin/                  plugin and marketplace manifests
```

## Contributing

`npm test` runs everything. Every documented hook pattern has a test; add one when you add a pattern. Every Markdown file in the repo must pass the deslop copy hook (the test suite checks this). Changes ship through [changesets](https://github.com/changesets/changesets): `npx changeset`, then a release PR bumps the version.

## License

MIT
