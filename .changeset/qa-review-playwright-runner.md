---
'jarrheyd-skills': minor
---

qa-review: a web repo can set `"runner": "playwright"`. The runner then calls the repo's Playwright suite instead of Maestro, and `scripts/playwright-reporter.mjs` files one result per spec plus the screenshots so the same report builds from it. Config and manifest can sit at the repo root.
