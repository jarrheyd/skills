# scout setup

Bootstrap a project for scout. Code first: the app's source tells you the screens, routes, and selectors; ask the user only what code cannot answer. End state: a committed `.maestro/` with config, manifest, and green starter flows.

No codebase access (a tester with only a URL or a build)? Use `--blackbox`: skip steps 3 and parts of 5, follow the "Blackbox setup" section at the end instead. Everything else (prerequisites, config, .env, run-until-green) is identical.

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

## Blackbox setup (--blackbox: no codebase access)

For when the person has only a running app: a staging URL (web) or an installable build like a TestFlight/apk/.app (mobile). Maestro never needed source to drive; only the exploration changes.

With no repo to commit into, the `.maestro/` folder (config, manifest, flows) lives in `~/.scout/<project>/workspace/` instead; scout-run.sh takes it via `--repo ~/.scout/<project>/workspace`. If the person later gets repo access, move the folder in and commit it.

Discovery, in place of code exploration:

- Web: crawl from the entry URL. Visit each screen, note its heading, its links/buttons, and where they lead; the crawl becomes the screen map and the manifest categories. Stay inside the target host; skip logout and destructive-looking actions during discovery.
- Mobile: install the build, walk it manually with a discovery flow (tap through tabs and menus, `takeScreenshot` each screen). `maestro hierarchy` dumps the accessibility tree per screen; harvest ids from it when the app ships accessibility identifiers, text otherwise.
- If a QA test script exists, ingest it first (crosscheck mode step 1): it already names the screens, steps, and expected results, and is a better map than a blind crawl.

Selector rules shift one notch: accessibility ids first when the hierarchy exposes them, visible text second, and every text selector gets a comment naming the screen so rot is easy to fix. Error detection falls back to generic strings ("Something went wrong", "Error", "Unable to", the platform's crash dialog) plus a screenshot after every screen; say in the manifest intro that error assertions are generic.

Label the output honestly: set `"blackbox": true` in scout.config.json, and prefix the manifest intro with "Built without codebase access". Gap analysis in audit mode then compares against the test script or the crawl map only, and the report must say so; never present blackbox coverage as code-grounded.
