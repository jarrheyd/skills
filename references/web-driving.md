# Maestro on web

Maestro drives web apps in its own Chromium. Same YAML, same runner, a few differences from mobile.

## Flow shape

No `appId`. The first step opens the URL:

```yaml
# tags block still applies
url: https://staging.example.com
---
- launchApp
- assertVisible: "Log in"
```

Older Maestro versions use `- openLink: https://staging.example.com` as the first command instead of the `url:` header; check `maestro --version` behavior if launch fails.

## Selectors

- `data-testid` attributes surface as `id:` selectors, same priority rule as mobile: ids first, text second.
- Web pages expose much more text than a mobile screen; text selectors collide more easily. Prefer ids or tighten with regex anchors.
- Hidden/off-viewport elements: use `scrollUntilVisible` before asserting; a below-the-fold element is not "visible".

## Behavior differences

- No simulator boot, no build step: `scout-run.sh` skips both on `platform: web`. The build happens in the project's own deploy/preview pipeline; scout tests the running URL.
- Viewport is Maestro's default desktop size. Responsive/mobile-web checks need a separate pass and are out of scope for the default suite.
- `launchApp` reloads the page and clears the session only when the flow asks (`clearState`). Login sessions otherwise persist across flows in a suite, same fast-path pattern as mobile.
- File pickers, browser dialogs (print, native alerts) and third-party auth popups are unreliable to drive; design flows to avoid them or mark the case BLOCKED with the reason.
- Screenshots are full-viewport PNGs (landscape). The report renders them in browser frames automatically (`platform: web` in scout.config.json).

## Environments

Same production rule as mobile: staging/preview URLs only, enforced by `guard-env.sh` on the `url` value.
