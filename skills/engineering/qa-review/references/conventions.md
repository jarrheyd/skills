# Flow-writing conventions

Distilled from production Maestro suites that gate real releases. Follow these for every flow you write or edit.

## Selectors

- `id:` (a component testID / data-testid) first, visible text second, coordinates never. Text breaks on copy edits and localization; ids do not.
- When a screen lacks testIDs, add them to the app code as part of setup (a testID is a one-line, zero-risk change) rather than writing a fragile text selector. Note each added id in the setup summary.
- Regex text matches (`".*(Thank you|Send to).*"`) only for genuinely branching outcomes.

## Structure

- `_`-prefixed files are reusable partials (`_login.yaml`, `_open-settings.yaml`), invoked with `runFlow:`, never run on their own. The runner skips them by name.
- Every flow starts with a comment block: what it guards, the bug class it would catch, and the exact run command. That comment is the flow's documentation.
- `tags:` drive run selection (`critical`, `happy`, `all`, `smoke`). The manifest's `mode` field is report metadata; keep the two in sync.

## Screenshots

- Explicit `takeScreenshot: 01-name` at the moments that matter, numbered so the report orders them. Explicit captures beat Maestro's auto-captures: they are the journey's real moments, on purpose, in order.
- Content before camera: every `takeScreenshot` is preceded by an `assertVisible` (or `extendedWaitUntil`) on REAL content of that screen - a post body, a name, a card title. Never shoot right after a tap or navigation: that frame is a skeleton loader, and skeletons in the report read as broken screens. Capture a loader only when the loading state itself is what the flow verifies, and name it so (`03-loading-state`).
- A flow with zero `takeScreenshot` steps has no evidence of its own: the report falls back to Maestro's auto step-captures, which fire mid-load and mostly show skeletons. Every flow that lands in a report gets at least one explicit capture per screen it claims to verify.
- Never capture a screen with a visible password. Shoot after submit.

## Error detection

- After every screen: `assertNotVisible` with the app's LITERAL error-state copy (grep the error components for the exact strings). Asserting a title is visible is not enough; titles render even when the content below them failed.
- Keep `errorCopy` in `qa-review.config.json` as the single list, and reuse it in every flow.

## Resilience without lying

- Idempotent conditionals for shared accounts: `runFlow: {when: {visible: ...}, commands: [...]}` so a flow no-ops instead of failing when state differs (an already-answered prompt, an already-dismissed dialog).
- Bounded repeats (`repeat: {times: N}`) around state resolvers; never unbounded loops.
- `extendedWaitUntil` with explicit timeouts instead of sleeps.
- `optional: true` only for taps that legitimately may not apply (a dialog that sometimes shows). Never mark a journey-critical tap optional to make a red flow green.
- Fail loud: a flow that swallows its own failure hides real bugs behind a green gate. If a check is bounded or sampled, say so in its comment.

## Auth and state gotchas (learned the hard way)

- A subflow's env default OVERRIDES the caller's `-e` value on Maestro 2.8; never set env defaults in partials.
- `clearState` does not clear the iOS Keychain; a session survives it and the app silently resumes the previous account. Account switches need `clearKeychain: true` plus walking the logout out through the UI.
- Auth sessions persist across launches: only the first flow of a suite pays the full login walk; later flows relaunch straight in. Design `_login.yaml` to resolve from any screen it lands on.
- System prompts (paste permission, open-in-app confirmations) can steal focus mid-type; bounded dismiss-refocus-retype passes handle them.
- Flows on shared accounts must leave state as they found it, or the manifest notes the seeding they need.

## Environments

- Dev/staging only, deterministic auth (fixed test OTP or plain test account). Never point a flow at production; `guard-env.sh` enforces this.
- Non-idempotent flows (real signup) stay out of the default gate and document their reset procedure.

## Traps that break full regressions (learned on Kapwa, Sep 2026)

- `- back` only works on Android. On iOS it silently does nothing, and the next step fails on the wrong screen. Tap the screen's own back button by id instead.
- Fixed names collide on the next run: duplicate detection, "already exists", or a list with many copies. Give created things a unique name per run: `- evalScript: ${output.name = 'Kid ' + Date.now()}`, then `inputText: ${output.name}`, and assert with a loose regex.
- A pressable card that wraps text and buttons becomes one accessibility element on iOS. Its children disappear from the tree, so text and button selectors inside it fail, and VoiceOver users cannot reach the buttons either. The fix belongs in the app (`accessible={false}` on the wrapper), not in the flow.
- Apps that keep a sentence's last two words together (a non-breaking space) break exact text matches. Match sentences loosely: `'.*First steps across the living.room.*'`, or give the text a plain accessibility label in the app.
- `scrollUntilVisible` wants the whole element on screen by default. A tall card never qualifies; add `centerElement: true` or target a smaller child.
- A flow that needs data only one script creates (a harness that runs API steps between flows) belongs in config `scenarios` or `flowSetup`, never in the one-by-one suite with `${VAR}` left unset. The doctor lists these as fixture gaps.
- The simulator can drop its network mid-run (an offline banner in the screenshot). Classify it as ENV and let the retry rerun it; never rewrite a flow for it.
- A flow that changes shared test data (archives the seeded Page, renames the fixture circle) and then fails halfway leaves it changed for every flow after it; one red becomes ten. Give such a flow its own data (a `flowSetup` that creates it), or make its first step put the data back into the expected state. When many flows fail on the same fixture, look for the earlier flow that broke it before repairing any of them.
