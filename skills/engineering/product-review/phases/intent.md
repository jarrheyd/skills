# Phase 1: intent

Build the list of what the user expected, confirm it with them, save it. The confirmed intent model is the review contract; nothing gets judged against an unconfirmed expectation.

## 1. Check for a saved model

`~/.product-review/<project>/<feature>.md` already covering this feature: load it, ask one question ("expectations still current, or did anything change?"), update if needed, skip to phase 2. Re-reviews must not re-grill from zero.

## 2. Gather what exists

Pull every source the user names or that the target points to, in this order of authority:

1. The ticket or spec (Jira/Wrike/doc): acceptance criteria, user story
2. The design (Figma link via the Figma MCP: export the relevant frames as expected-state images for the report)
3. The PR description and linked issues (`gh pr view`)
4. Chat asks the user points at (the message where they asked for the feature)

Quote each source's claims into a draft list of expectations. Note the source next to each.

## 3. Draft the intent model

Each expectation: one sentence, observable on a screen or in behavior, numbered. "The invite button sits on the circle page and opens the share sheet" is an expectation; "good UX for inviting" is not, split it until each line is checkable.

Mark every gap and conflict:
- Sources disagree (ticket says X, Figma shows Y)
- A source is silent on something the feature obviously touches (empty state, error case, what happens after success)
- The user asked for something in chat that no document captured

## 4. Grill the user

Interrogate until the marks are resolved, grill-me style: one question at a time, each with a recommended answer, concrete options over open questions. Only the gaps and conflicts; do not re-ask what a source already answers and the user has not contradicted. Typical questions:

- "Ticket says the discount shows at checkout, the Figma shows it on the cart too. Which did you expect?"
- "Nothing says what an empty circle looks like. What did you want there?"
- "Was the animation part of the ask, or a bonus if it happens?"

Record each answer in the model with `confirmed <date>`.

## 5. Save

Write the model to `~/.product-review/<project>/<feature>.md` using `references/intent-model.md`. Tell the user it is saved and local-only. Proceed to phase 2.
