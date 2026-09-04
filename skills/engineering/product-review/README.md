# product-review

A design/product alignment review skill for AI coding agents. Point it at a PR, a merged branch, or a deployed app and it checks whether what was built matches what YOU expected, direction over code quality, and hands back a conversation agenda with screenshot evidence.

It fills the gap between e2e testing (does it work?) and code review (is it built right?): is it the right thing?

## How it works

1. Intent: gathers the ticket, the Figma, the PR description, and your chat asks, then interviews you to resolve gaps and conflicts. The confirmed expectations are saved locally and reused on re-reviews.
2. Evidence: maps what changed, then collects screenshots of the changed screens (reusing qa-review run evidence when the project has it). Code fills in what pixels cannot show, like buttons that go nowhere.
3. Verdict: each expectation gets MATCHES, DRIFTED, MISSING, EXTRA, or CAN'T TELL, each citing a picture or a place in the code. Overall: ALIGNED, or NEEDS A CONVERSATION with the items to discuss. There is no reject gate; the output is an agenda.
4. Deliver: a local HTML report (default), draft PR comments (posted only when you say go), or draft tickets in your format.

Everything it writes is plain language. The audience is product managers and designers; no unglossed technical terms, ever.

## Install

```bash
git clone https://github.com/jarrheyd/product-review ~/.claude/skills/product-review
```

Claude Code picks it up as `/product-review`. Works with any agent that can run shell commands; everything is markdown and plain scripts.

Pairs well with [qa-review](https://github.com/jarrheyd/qa-review) (shares its screenshot evidence) and a grill-style questioning skill for the intent interview, but neither is required.

## Where things go

- `~/.product-review/<project>/<feature>.md`: your confirmed expectations, local only, never committed anywhere
- `~/.product-review/<project>/reviews/<timestamp>/`: screenshots, verdicts, `report.html` (last 2 kept)
- Your repo: untouched

## Layout

```
SKILL.md        entry point + hard rules
phases/         intent, evidence, verdict, deliver
scripts/        build-review.mjs (the report builder)
references/     intent model template, plain-language contract
```

## License

MIT
