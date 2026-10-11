# Phase 4: deliver

Default is the report; `--pr` and `--ticket` add the other two. All three draw from `review.json`. Everything passes the deslop gate and the plain-language contract before the user sees it.

## The report (always)

```
node scripts/build-review.mjs --review <reviewDir>/review.json --out <reviewDir>/report.html
```

Then prune to the last 2 review folders (delete older `reviews/*` dirs) and open the report. Chat summary on top: the overall call first, then the conversation agenda items, one line each.

Present the expectations as a numbered test-case list, so the report reads as a checklist a product manager can sign off from: each expectation is one row with an ID, the expectation in plain words (the expected result), what was built (the actual, with its evidence), and the verdict (MATCHES / DRIFTED / MISSING / EXTRA / CAN'T TELL). A DRIFTED or MISSING row names what is off and the fix conversation it needs.

End the report with a production-readiness line the same way qa-review does: READY or NOT READY for this feature, then the count of open MISSING and DRIFTED expectations on the critical path. The two skills compose: a feature is production-ready when product-review is ALIGNED (intent is met) and qa-review is GREENLIGHT (the flows run without crash or defect). Say which of the two is still open when the answer is NOT READY, so the reader knows whether the gap is intent or execution.

## PR comments (--pr, or when the user asks)

One draft comment per DRIFTED / MISSING / EXTRA item, anchored to the relevant file when the diff shows it, otherwise a single top-level comment. Each comment: what was expected (with its source), what is there instead, and a question rather than an order ("was moving this to settings deliberate?"). Show all drafts in chat. Post with `gh pr comment` / `gh api` ONLY after the user says go, and confirm what was posted.

## Tickets (--ticket, or when the user asks)

One draft ticket per item the user picks (default: every MISSING). The user's ticket format, when they have one; otherwise: plain title, no adjectives, refer to other tickets by key; body with User story, Context (quoting the intent source), Acceptance criteria, Open questions. Show drafts in chat; create in Jira/Wrike only on go, in the user's own voice (first person).

## Closing

End with: where the report lives, what was posted or created (exactly), what remains draft, and any CAN'T TELL items with what would unlock them.
