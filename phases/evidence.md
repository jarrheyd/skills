# Phase 2: evidence

Collect proof of what was actually built. Visual first; code fills in what pixels cannot show.

## 1. Map the change

By target type:
- PR: `gh pr diff` + `gh pr view`. List the screens/areas the diff touches.
- Merged range: `git diff <base>..<head>` same treatment.
- Deployed app only: no diff; the intent model's expectations name the screens to visit.

From the map, list the screens the review must see. Also note, from code, things pixels cannot show: handlers that go nowhere, features behind flags, expectations whose code simply is not there.

## 2. Get the pixels

In order of cheapness:

1. qa-review evidence: newest run under `~/.scout/<project>/runs/` whose screenshots cover the mapped screens and post-date the change. Free, already captured.
2. Drive the changed screens: web via the browser (navigate, screenshot per screen and per state the intent model names); mobile via Maestro or the simulator tools (install the current build, walk to each screen, capture). Capture the states the expectations name: filled, empty, error, after-success.
3. No runnable app reachable: code-only mode. Say so up front, and every verdict that would need pixels becomes CAN'T TELL with "needs a build/URL" as the note.

Save captures under `~/.product-review/<project>/reviews/<timestamp>/shots/`, named by screen.

## 3. Pair with expectations

For each intent item, attach: the actual screenshot (or the code location when the expectation is behavioral), and when a Figma frame was exported in phase 1, the expected image alongside it. Items with no evidence found yet go back to step 2 once; still nothing reachable, they are CAN'T TELL.

Token discipline: look at each screenshot once, when judging its expectation. The report embeds everything for the human; do not re-open images to describe them.
