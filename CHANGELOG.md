# Changelog

## 2.2.1

### Patch Changes

- [`162a35a`](https://github.com/jarrheyd/skills/commit/162a35a9b75026bee58a39aac87f729ccb4e6ddd) Thanks [@jarrheyd](https://github.com/jarrheyd)! - Catch short fragment runs in paragraph and static JSX copy.

- [`7816c0c`](https://github.com/jarrheyd/skills/commit/7816c0c20c45673205dab34830c692ab3d523355) Thanks [@jarrheyd](https://github.com/jarrheyd)! - deslop: the copy hook and slop dictionary catch more tells. retro: harvest reads his replies typed in the valley messenger and works when run through the skills symlink.

- [`73ff0ff`](https://github.com/jarrheyd/skills/commit/73ff0ffdfbd85e394a53815c16282724958a3e29) Thanks [@jarrheyd](https://github.com/jarrheyd)! - Reinstall the Playwright browser before a regression run, and drop valley resume prompts from the retro harvest.

## 2.2.0

### Minor Changes

- [`926b522`](https://github.com/jarrheyd/skills/commit/926b52216dadb36ddb68482c1df83a8b5a5a1dac) Thanks [@jarrheyd](https://github.com/jarrheyd)! - deslop: the copy hook now checks prose typed into a page through a browser tool (a `type` action, a form value, or a batched action), so slide and doc copy entered through Chrome is gated like a file write. Text under eight words and bare links pass.

- [`926b522`](https://github.com/jarrheyd/skills/commit/926b52216dadb36ddb68482c1df83a8b5a5a1dac) Thanks [@jarrheyd](https://github.com/jarrheyd)! - deslop: the copy hook now blocks interface copy that explains itself (a line that tells the reader to click here, that says what a page shows, or a sign-in subtitle listing what is behind it), reading raw JSX text as well as string literals. The review gate and the slop-detector agent gain an interface pass: delete every subtitle, helper line and caption a first-time user can do without.

- [`926b522`](https://github.com/jarrheyd/skills/commit/926b52216dadb36ddb68482c1df83a8b5a5a1dac) Thanks [@jarrheyd](https://github.com/jarrheyd)! - deslop: the copy hook now blocks a bold line used as a section label on three or more blocks, three short sentences in a row of about the same length, and a paragraph that ends on a short abstract closing line.

- [`926b522`](https://github.com/jarrheyd/skills/commit/926b52216dadb36ddb68482c1df83a8b5a5a1dac) Thanks [@jarrheyd](https://github.com/jarrheyd)! - qa-review: a web repo can set `"runner": "playwright"`. The runner then calls the repo's Playwright suite instead of Maestro, and `scripts/playwright-reporter.mjs` files one result per spec plus the screenshots so the same report builds from it. Config and manifest can sit at the repo root.

- [`926b522`](https://github.com/jarrheyd/skills/commit/926b52216dadb36ddb68482c1df83a8b5a5a1dac) Thanks [@jarrheyd](https://github.com/jarrheyd)! - retro: new skill. It harvests the moments in Claude session transcripts where the person corrected the agent, repeated themselves, interrupted, or a tool kept failing, then applies a fix to the setup for each one with a backup and a log line.

## 2.1.0

### Minor Changes

- deslop carries seven deck tells caught by hand during a strategy-deck review that the write-hooks never saw, because the deck lived in Claude Design and Google Slides. They are judgment calls for the review agent rather than regexes: comma two-beat headlines, wordy feature-card grids, staged mockups that do not look like real posts, outcomes headlined as strategy, unverified specifics stated as fact, slide footers and source lines, and tactics that read years out of date.

- deslop blocks a comma in a short display heading. The rule: if a headline needs a comma it is usually two ideas and too long, like "One login, every tool". It is scoped to headings of six words or fewer, so long list-style headings and ordinary doc headings are spared, and it excludes the legitimate cases the hook already allowed: a date ("September 4, 2026"), an "X, or Y?" decision framing, an "X, or ..." explanatory heading ("Circle invites, or how circles grow"), and a schedule gloss ("Migration, in three weeks"). Three of the skills' own doc headings were reworded to comply.

- deslop now gates email drafts, ticket comments and chat sends, not only file writes. Chat gets the tells-only checks, email and comments get the full prose set, and the named banned words block on the first hit. The copy hook also reads string literals in more source types and skips test fixtures.

- deslop blocks a staccato two-beat heading. Splitting a short headline into two terse sentence-fragments ("Four rails. One job each.") is the same AI cadence as the comma it replaces, so shortening a comma-heading that way is not a fix. The rule flags a heading of two or more fragments when each fragment is four words or fewer and the whole heading is eight words or fewer. It leaves single-sentence headings and dotted acronyms (U.S., e.g.) alone. The plain noun phrase is the fix, with the subhead carrying the rest.

- deslop learns from the 2026 Economist study on spotting AI writing. The copy hook now blocks "not only X but also Y" when both halves sit in one sentence, alongside the "not X but Y" family it already caught. The dictionary records the study's real finding: the modern tells are what AI leaves out, so a note explains that em dashes are no longer a reliable AI fingerprint (only Claude overuses them) and stay blocked as house style, not as evidence, and what-humans-do.md gains two counter-patterns, the punctuation people reach for that AI skips (commas, semicolons, parentheses, a short sentence after a long one) and quoting a real named person. "maximise" and its long-word cousins join the density-flagged list.

- deslop now catches the absence tells, the things AI leaves out per the 2026 Economist study, in the review path. A new scripts/flat_prose.py reads flowing prose over ~150 words (lists, code, tables and headings stripped first) and prints one plain nudge when several signals agree the prose is flat: long even sentences, no semicolons, no parenthetical asides. It never blocks (exit 0 always) and never prints numbers, so it stays out of the zero-tolerance write hooks where a bullet list or commit message would trip it. The slop-detector agent runs it in its density pass, and SKILL.md documents it as review-only.

- product-review now shows a screenshot on each flow in the report. The report builder renders an `actuals` array (the several states a flow walks: filled, empty, error, after-success) alongside the single `actual`, labels each item with its `flow` name, and draws a loud placeholder plus prints a warning for any visual item that reached its screen but carries no screenshot, so a flow without its shot is visible instead of silently dropped. The evidence and verdict phases now require a screenshot per reachable flow and document saving all flow shots into the review folder. Only a purely behavioral expectation may lean on `code` alone.

- qa-review and product-review now read like a release-ready regression suite. A new references/regression-report.md defines flows as a numbered test-case matrix (ID, preconditions, steps, expected, actual, status, evidence) and a failure classification every red must carry: CRASH (the app process died or a native error appeared), DEFECT (wrong behavior on the right screen), FLOW-ROT (the screen is correct but a selector or layout changed), or ENV (driver or backend). Two SKILL.md hard rules enforce it: classify every red from the app's process state and a screenshot, never a guess; and keep flows fresh by cross-checking every selector against the current testIDs each audit and resetting shared state between flows that create data, since a stale flow tests nothing while looking green. The audit mode runs the freshness check in gap analysis and ends on a production-readiness line. product-review presents its expectations as the same numbered test-case list and closes with a READY / NOT READY rollup that composes with qa-review: a feature is production-ready when intent is met and the flows run without crash or defect.

## 2.0.0

### Major Changes

- qa-review drops the scout name. The runner is now qa-review-run.sh, the config is qa-review.config.json, control variables take the QA*REVIEW* prefix, and evidence lives in ~/.qa-review. No fallback to the old names: a project onboarded earlier must migrate all four, and MIGRATING.md has the commands. The scout alias is gone from the skill description.

### Minor Changes

- qa-review carries the previous run forward. A flow that did not run this time now shows its last screenshots instead of an empty card, and counts toward green only while that evidence still describes the build under test and is under 7 days old. Each run fingerprints what was installed (the simulator or device binary, or the commit for web), so evidence survives SKIP_BUILD reruns but expires the moment the binary changes. Expired evidence still shows, dimmed, with the reason and its original date. The header now counts verified, carried, needing a rerun and never run separately, so a partial run cannot read as a full pass. Fixes the off-by-one that made the existing carry-forward pick a report two runs back, which pruning had usually deleted, so nothing was ever carried.

### Patch Changes

- qa-review opens the report from the runner. scout-run.sh now calls a new open-report.sh at the end of every run, so a finished run always puts report.html on screen instead of relying on the agent to remember the step. SCOUT_NO_OPEN=1 or CI keeps it closed, SCOUT_OPEN_CMD overrides the opener.

## 1.1.0

### Minor Changes

- deslop catches hook-and-reveal rhythms: elliptical setups, suspense-then-answer, unneeded justifiers, revelation hooks, big-reveal frames, overhype, "will revolutionize", "fast-changing world", "dive into", opposing shutdowns, philosophical reductions, "no X, no Y, just Z", three adjectives in a row, the law of threes, uniform sentence length, and emoji bullets.

### Patch Changes

- scout-run runs flows one invocation each by default (Maestro aborts a multi-flow run on an unresolved addMedia path with nothing executed) with a portable perl-alarm timeout, and guard-env accepts app-scheme deep links (acme://...) since they open the already-approved installed build.

## 1.0.0

### Major Changes

- First release as one repo and one plugin. deslop, qa-review and product-review move in from their own repos with history. deslop's hook now catches every pattern its docs list and its docs pass their own gate; qa-review's summary and report agree after a retry and the production guard matches hostname labels instead of substrings; product-review validates `review.json` and ships a recorded example.
