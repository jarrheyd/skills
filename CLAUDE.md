# jarrheyd/skills

Skills live in bucket folders under `skills/`: `engineering/` and `writing/`. Every skill in either bucket is promoted: it must have an entry in `.claude-plugin/plugin.json`'s `skills` array and a line in the top-level `README.md` that links its `SKILL.md`.

Run `claude plugin validate . --strict` after touching either manifest. `npm test` must pass before a commit; it runs the node tests for the report builders and runners, the Python tests for the deslop hooks, and a check that every Markdown file in the repo passes the deslop copy hook with its skip list off.

Prose rules for this repo, enforced by that test: no em dashes anywhere, sentence-case headings, no bold used as a paragraph title, no restatement, and none of the patterns in `skills/writing/deslop/references/copy-slop-dictionary.md`. When a reference file needs to quote a tell, it lives under `references/` (exempt); `SKILL.md`, `README.md`, agents and phases are not exempt.

Releases go through changesets. `package.json` and `.claude-plugin/plugin.json` carry the same version; `scripts/sync-plugin-version.mjs` keeps them aligned and `npm run check-plugin-version` fails CI when they drift.

Maintainer setup: `scripts/link-skills.sh` symlinks each skill into `~/.claude/skills` so a `git pull` keeps the local install current.

Commits carry no AI attribution trailers.
