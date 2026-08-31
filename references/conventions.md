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
- Never capture a screen with a visible password. Shoot after submit.

## Error detection

- After every screen: `assertNotVisible` with the app's LITERAL error-state copy (grep the error components for the exact strings). Asserting a title is visible is not enough; titles render even when the content below them failed.
- Keep `errorCopy` in `scout.config.json` as the single list, and reuse it in every flow.

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
