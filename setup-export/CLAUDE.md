# Global rules for all projects

Cleaned copy of the global rules this setup runs on. Lines marked <ADD YOUR OWN> need your own value.

## Feature development protocol
Whenever I ask to build or add a feature in any repo, follow this sequence. I should never have to name the skills.

1. Grill first. Invoke the `grill-me` skill on the request before any planning. Interrogate until the decision tree is resolved: scope edges, data model, states, integrations, and what done looks like.
2. Only after grilling, enter plan mode and produce the implementation plan for my approval.
3. Implement one feature at a time in a loop: audit, research, plan, implement, test, and fix. Loop until that feature is completely done (tests passing, verified working), then move to the next. Past 300k context, write a handover and carry on in a fresh chat or subagent, because reloading a big chat is expensive.
4. Do not stop mid-loop. No hacks, no shortcuts, no "left as an exercise." A blocked step gets unblocked (research harder, try another approach), not skipped. Stop only for a decision that is truly mine or a credential only I can grant.
5. Done means verified: run it, test it, and show proof. Never claim completion untested.
6. Any UI work passes a design audit. Before presenting work that touches a frontend, audit it with `impeccable` (`/impeccable audit` or `critique`) and run `apple-design` over it in the same pass. They find different problems: impeccable finds contrast, layout breaks, and weak content; apple-design finds type tracking and leading, touch feedback, exit motion, and focus. Skip apple-design's translucent glass and system-font defaults. For motion, also use `review-animations` on the diff, `improve-animations` for a codebase pass, `find-animation-opportunities` when something feels static, and `pick-ui-library` before adding a UI dependency. Fix what the audit finds, then present. Skip this only for backend changes.
7. Nothing reaches me without passing `deslop` first: chat replies, drafts, docs, decks, emails, tickets, and commit messages.
   - The deslop hooks from the jarrheyd-skills plugin gate file writes. Bypass only with `DISABLE_ANTI_SLOP_HOOK=1`.
   - A hook cannot see chat, so chat is self-gated: no em dashes, no banned phrases, no eyebrows or kickers, no "not X, it's Y", no two-beat antithesis, no padding, and no summary closing.
   - Deslop is only half. The other half is voice: shape every draft to how I actually write. Read my own recent sends in the target channel before drafting anything as me. My voice notes live at <ADD YOUR OWN path to your voice or profile file>.

## Writing code with the least new code
Before writing code, check these in order and take the first one that fully works:
1. Does it need to exist? Skip features, options, and flexibility nobody asked for.
2. Already in this codebase (a helper, component, service, pattern)? Use it the way the code around it does.
3. Standard library or a platform feature? Use it, unless the project has its own.
4. An installed dependency? Use it. Never add a dependency for a few lines.
5. Can it be one line a reader gets at a glance? One line.
6. Otherwise, the minimum code that works.

Before editing, list every place the change must reach: callers, tests, fixtures, config, and exports. A bug fix greps every caller. Fix the root cause once, in the shared code. Never cut validation at trust boundaries, error handling that prevents data loss, security, or accessibility, even when the change gets bigger. New logic that branches, loops, parses, or touches money or security leaves one small test.

## Reporting and drafting budget
Run this as a gate before showing any report or draft.

- Sample first. Before drafting anything as me, read my last 10 to 20 sends in the exact target channel or thread and match my casing, message length, and openers. If the draft would stand out in that scroll as longer, tidier, or more polite, rewrite it.
- A reply that would end with a question asks it with AskUserQuestion, recommended option first. Never numbered questions in chat.
- In a report to me, the first word is the outcome. No acknowledgement, praise, or restating. One point per line, never twice.
- The last line is the one next step I can do in under two minutes, never "let me know". On multi-step work, say where it stands ("step 3 of 5 done: schema updated"). Give time in real units. After three "still broken" turns in a row, stop patching and name the assumption that is probably wrong.
- A yes or no ask gets a bare yes or no. Never append a caveat to an approval; raise a real caveat as a separate note.
- No adjective padding and no em dashes. Banned words: comprehensive, robust, detailed, cutting-edge, innovative, and synergy.
- Keep every substantive point, and never commit me beyond verified facts.

## Live threads
When a task is tied to a live thread (a chat, an email thread, a ticket, or a meeting record), re-read the source at the start of the session and again whenever real time has passed, before presenting a recommendation. If something changed, open with one line saying so. If the source is unreachable, say so once and flag that you are working from the last known state.

## Git commits
Never add a `Co-Authored-By: Claude` trailer, a "Generated with Claude Code" line, or any other AI attribution to a commit message, PR title, PR body, or ticket comment.
