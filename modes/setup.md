# scout setup

Bootstrap a project for scout. Code first: the app's source tells you the screens, routes, and selectors; ask the user only what code cannot answer. End state: a committed `.maestro/` with config, manifest, and green starter flows.

## 1. Prerequisites

Check and report, fix what you can:

- `maestro` on PATH (`~/.maestro/bin`). Missing: `curl -fsSL "https://get.maestro.mobile.dev" | bash`
- Java runtime (`java -version`). Missing on macOS: `brew install --cask temurin` (needs the user or brew permission)
- Mobile: Xcode + at least one available simulator (`xcrun simctl list devices available`). Web: nothing extra.

## 2. Detect the platform

React Native / Expo / iOS / Android project: `platform: mobile`. Next/React/Vue/anything served over HTTP: `platform: web`. Monorepos with both: ask which surface to cover first; one config per surface.

## 3. Explore the code

Map, without asking the user:

- Screens/routes: navigators, route tables, page directories
- Existing testIDs / data-testids (grep `testID=` / `data-testid=`)
- The error-state components and their LITERAL user-facing copy (this feeds `errorCopy` and every `assertNotVisible`)
- The login screen's inputs and their ids
- Any existing e2e setup to reuse rather than duplicate

## 4. Ask the user (one short round)

Only: target env URL or appId + how to build/install (or an existing build to reuse), which test account keys exist, and the 3 to 5 journeys that matter most if they have an opinion. Then:

- Write `.maestro/scout.config.json` from `templates/scout.config.json`
- Create `~/.scout/<project>/.env` with PLACEHOLDER lines for each key in `envKeys` (`SCOUT_USER=fill-me`); tell the user to fill it. Never ask for the values in chat.

## 5. Generate

From the templates, adapted to the real code:

- `journeys.manifest.json`: every mapped screen area as a category; the top journeys as entries; everything you could not build yet as `planned: true` so the report shows the full plan
- `flows/screen-walk.yaml`: visit every top-level screen, the real `errorCopy` strings after each, numbered screenshots
- `flows/_login.yaml`: the project's actual login inputs and post-login anchor
- One flow per top journey, following `references/conventions.md`
- Screens missing testIDs: add them to the app code (one-line changes), list them in your summary

## 6. Run until green

`scripts/scout-run.sh --repo <repo>` (guard-env runs inside it). Read `run-summary.json`. For each failure open ONLY that flow's last screenshot, fix the selector or flow, rerun just that flow (`--flows`). Loop until green or genuinely blocked (unfilled .env, env down); blocked is reported, not worked around.

## 7. Finish

Commit `.maestro/` (flows, manifest, config, plus any testIDs added to app code) with the user's normal commit conventions. Open `report.html`. Summarize: flows built, flows planned, testIDs added, what the user still owes (creds, approvals).
