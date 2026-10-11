# Crosscheck verdicts

One verdict per test case, with the evidence bar each requires. Written into `crosscheck.json` as `{ "source": "<sheet name>", "cases": [{ "id", "title", "verdict", "note", "evidence": "<screenshot path>" }], "scriptReview": ["..."] }`.

## PASS

The steps reproduce as written and the expected result matches on screen. Evidence: the screenshot of the end state. The note stays empty unless something was bounded.

## FAIL

The app misbehaves: a step cannot be performed, the result contradicts the expectation, or an error state renders. Evidence: screenshot of the breaking step plus which step number broke and what happened instead. This is an app bug; the note is written so a developer can act on it without rerunning.

## SCRIPT WRONG

The app behaves correctly but the test script is outdated or incorrect: renamed buttons, moved screens, changed copy, wrong expected result. Evidence: screenshot of the actual correct behavior. The note gives the fix in paste-ready form: current script text, what it should say.

## NOT WIRED

The feature, screen, or element the case references does not exist in this build: a dead-end button, a missing screen, an unimplemented branch. This is a product signal, not a QA failure. Evidence: screenshot of where the case dead-ends. The note says what is missing and where the journey stops.

## BLOCKED

The case could not be reached: missing credentials or role, environment down, an unmet precondition (needs seeded data, needs a second account), or an upstream case failed. Evidence: none required; the note names the blocker precisely so it can be cleared and the case rerun. BLOCKED is never used to soften a reproducible FAIL.

## Script review section

After the verdicts, review the script itself: missing unhappy paths and edge cases (per screen touched), ambiguous steps a new tester could not follow, untestable expectations ("works correctly"), duplicate or contradictory cases, missing preconditions. Each finding follows the current / should-be / paste-ready form so the QA can apply it directly.
