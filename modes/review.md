# scout review

Review or author a QA test script WITHOUT driving the app. Desk mode: no runner, no simulator, no screenshots.

## Reviewing an existing script

1. Ingest and normalize exactly as crosscheck mode step 1.
2. If the project has a repo available, ground the review in code: real screen names, real fields, real branches. Say when you could not (a pure desk review is weaker; offer crosscheck as the follow-up).
3. Review per `references/verdicts.md`'s script-review list: coverage (happy, unhappy, edge per screen or feature the script touches), executability (could a new tester follow each step verbatim; is each expected result observable and specific), structure (ids, preconditions, duplicates, ordering, data requirements).
4. Deliver findings in current / should-be / paste-ready form, most severe first. Coverage gaps come as fully written new cases, not as "add more edge cases".

## Authoring a new script

1. From the repo (preferred) or the user's feature description, map screens, actions, and branches.
2. Write cases in the team's existing format when a sample script exists (match its columns); otherwise: `ID | Title | Preconditions | Steps | Expected result`, one behavior per case, happy paths first, then unhappy and edge per screen.
3. Number IDs by area so crosscheck runs can address them stably.
4. Offer the natural next step: convert the script's critical cases into committed flows (setup or crosscheck mode) so the script stops being paper.
