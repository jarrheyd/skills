---
name: product-review
description: Design/product alignment review. Checks whether what was built (a PR, merged code, or the deployed app) matches what the product owner actually expected, in direction not code quality. Use when the user wants to review a PR or feature against their expectations, check if implementation matches the design or spec, verify the direction of what shipped, or says "product review", "is this what I asked for", "review this against the Figma/ticket".
version: 1.0.0
user-invocable: true
argument-hint: "[PR/branch/URL] [--report|--pr|--ticket]"
license: MIT
---

# product-review

Answers one question: is what got built the thing the product owner wanted? Not whether the code is clean (that is /code-review's job) and not whether the flows pass (that is qa-review's job). This skill compares implementation against intent and hands back a conversation agenda, not a gate.

The audience is product managers and designers. Every word the skill emits, in findings, comments, tickets, and the report, is plain language: short sentences, no unglossed technical terms, concrete over abstract. If a smart non-engineer would not get a sentence in one pass, rewrite it. The full contract: `references/plain-language.md`.

## Phases (run in order)

| Phase | File | Output |
| --- | --- | --- |
| 1. Intent | `phases/intent.md` | A confirmed intent model: numbered, observable expectations |
| 2. Evidence | `phases/evidence.md` | Screenshots (preferred) + change map of what was actually built |
| 3. Verdict | `phases/verdict.md` | One verdict per expectation, one overall direction call |
| 4. Deliver | `phases/deliver.md` | The report (default), draft PR comments, or ticket drafts |

## Hard rules

1. Plain language everywhere, per `references/plain-language.md`. This outranks brevity.
2. Never infer unwritten intent. When sources conflict or are silent, ask the user (grill-me style) and record the answer in the intent model. An expectation that was never confirmed cannot produce a DRIFTED or MISSING verdict.
3. Every verdict cites its evidence: a screenshot, or a named place in the code. No citation, no finding.
4. Alignment and code quality never mix. If code quality problems surface, one line pointing to /code-review, nothing more.
5. Show before sending: PR comments and tickets are drafts until the user says go. The report is local HTML; nothing is published anywhere by default.
6. Intent models live in `~/.product-review/<project>/` and never leave the machine. They hold the user's candid expectations.
7. Honest bounds: evidence gathered without a runnable app is labeled code-only; screens the review could not reach are CAN'T TELL, never guessed.

## Verdicts

MATCHES / DRIFTED / MISSING / EXTRA / CAN'T TELL per expectation; ALIGNED or NEEDS A CONVERSATION overall. Definitions and evidence bar: `phases/verdict.md`.

## Where things live

- `~/.product-review/<project>/<feature>.md`: saved intent models (template: `references/intent-model.md`)
- `~/.product-review/<project>/reviews/<timestamp>/`: evidence, `review.json`, `report.html` (last 2 kept)
- Nothing is written into the target repo.

## Relationship to sibling skills

- qa-review (alias scout): drives the app, proves flows work. product-review borrows its freshest screenshots as free evidence.
- /code-review: code correctness and quality. Out of scope here.
- grill-me: the interrogation engine phase 1 uses on the user.
- deslop: gate every emitted draft through its rules as usual.
