# Phase 4: deliver

Default is the report; `--pr` and `--ticket` add the other two. All three draw from `review.json`. Everything passes the deslop gate and the plain-language contract before the user sees it.

## The report (always)

```
node scripts/build-review.mjs --review <reviewDir>/review.json --out <reviewDir>/report.html
```

Then prune to the last 2 review folders (delete older `reviews/*` dirs) and open the report. Chat summary on top: the overall call first, then the conversation agenda items, one line each.

## PR comments (--pr, or when the user asks)

One draft comment per DRIFTED / MISSING / EXTRA item, anchored to the relevant file when the diff shows it, otherwise a single top-level comment. Each comment: what was expected (with its source), what is there instead, and a question rather than an order ("was moving this to settings deliberate?"). Show all drafts in chat. Post with `gh pr comment` / `gh api` ONLY after the user says go, and confirm what was posted.

## Tickets (--ticket, or when the user asks)

One draft ticket per item the user picks (default: every MISSING). His ticket format: plain title, no adjectives, refer to other tickets by key; body with User story, Context (quoting the intent source), Acceptance criteria, Open questions. Show drafts in chat; create in Jira/Wrike only on go, using his account voice (first person).

## Closing

End with: where the report lives, what was posted or created (exactly), what remains draft, and any CAN'T TELL items with what would unlock them.
