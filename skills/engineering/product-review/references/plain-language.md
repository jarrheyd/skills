# Plain-language contract

The skill's audience is product managers and designers. Many are not technical. Every finding, comment, ticket, and report line follows this, and it outranks brevity: a sentence can be short and still cryptic.

## Rules

- Short sentences, one idea each.
- Plain words. No unglossed jargon or acronyms: not "the handler is stubbed", not "behind a feature flag", not "the payload", not "RBAC". If a technical term is truly needed, say it plainly or gloss it once: "the button is switched off for everyone right now (a feature flag)".
- Concrete over abstract: "tapping Save does nothing" not "the mutation is not wired"; "the discount never shows on the cart screen" not "the cart lacks the discount integration".
- Lead with the point; cut hedge phrases. "So we only handle one role" not "there is no mixed-role case to design for".
- Name screens and buttons by what the user sees on them, not by component or file names. File names appear only in the evidence citation, in parentheses, at the end.
- Questions over accusations in anything the builder will read: "was moving this to settings deliberate?" not "this violates the spec".

## The test

Read each line back as if aloud to a smart colleague who has never opened a code editor. If they would need a second pass or a follow-up question, rewrite. When a finding cannot be said plainly, the finding is not yet understood; go look again.
