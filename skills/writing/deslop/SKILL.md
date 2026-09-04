---
name: deslop
description: Quality gate that blocks AI-generated tells before they ship. Runs automatically as a hook on every file write (copy tells in prose, visual tells in HTML/CSS/JSX, both again on artifacts and Drive docs), and manually as a review with a slop-detector and a copy-humanizer agent. Use when copy, a doc, a deck, a landing page, or UI reads as machine-made, or before anything goes out.
version: 1.0.0
user-invocable: true
argument-hint: "[file or pasted content]"
license: MIT
---

# deslop

Catches the words, phrases, structures, and visual defaults that read as machine-written, and blocks them before they ship. It removes; it does not add voice. Pair it with a brand or voice model for that.

## How it runs

Two hooks run on every Write, Edit and MultiEdit, one on artifacts. Every hit blocks; there is no warn tier.

- `hooks/copy_slop_hook.py` reads prose files (`.md`, `.mdx`, `.txt`, `.html`) and the string literals of `.ts`, `.tsx`, `.js`, `.jsx`, `.py`.
- `hooks/design_slop_hook.py` reads `.html`, `.css`, `.scss`, `.tsx`, `.jsx`, `.vue`, `.svelte`.
- `hooks/artifact_slop_hook.py` pulls the body out of an `Artifact` publish or a Drive connector `create_file` / `update_file` and runs both hooks on it. Those writes never touch the local filesystem, so without it they skip the gate.

Bypass a session with `DISABLE_ANTI_SLOP_HOOK=1`. Exempt paths that repeat by design (ledgers, generated output, a vault's state files) with `DESLOP_SKIP_PATHS=_archive/,build/`. Hooks load at session start; a hook added mid-session protects the next session.

Manual: `/deslop` or "run a slop check on this". For a full review use `agents/slop-detector.md`; for a rewrite use `agents/copy-humanizer.md`.

## What the copy hook blocks

Every pattern is a regex in `copy_slop_hook.py`; the literal list, with fixes, is `references/copy-slop-dictionary.md`. By family:

- Throat-clearing openers and filler transitions at the start of a line.
- The not-just-X reframe and its cousins: negation ladders, either-or reductions, rhetorical-question pile-ups.
- Aspirational verbs (unlocking, harnessing, elevating, seamless anything, the revolution verb in every tense).
- Sycophancy, manufactured-candor openers, TikTok aphorisms, chatbot outros.
- Vague attribution (unnamed studies, experts, critics), puffery about legacies and pivotal moments, dead metaphors about needles, levers, and missing pieces.
- Weak copulas, wordy forms, empty "-ing" tails, false ranges, AI disclaimers, abstract jargon nouns.
- Tool remnants: citation tokens and tracking parameters leaked from the generating tool.
- Typography: em dashes (including HTML entities), curly quotes, middot separators, Title Case headings, bold as decoration, a period-terminated bold fragment used as a paragraph title.
- Explainer headings that gloss the artifact instead of naming the subject.
- Restatement: two adjacent sentences or bullets sharing 90 percent of their content words. Parallel lists with different values pass.
- Hyphenated-compound titles, three adjectives in a row, and the law of threes (three one-word sentences, or a sentence that closes on three single-word items).
- Hook-and-reveal rhythms: the elliptical setup (a two-word question as a drumroll, then the answer), the suspense-then-answer, the unneeded justifier before a point, the revelation hook (the thing nobody supposedly says), the big-reveal frame (what a thing supposedly is underneath), and overhype (claims of changing everything or starting a revolution).
- False choices: the opposing shutdown (you do not need X, you need Y), the philosophical reduction (X is not Y, it is Z), and the no-X-no-Y-just-Z slogan.
- Rhythm: a paragraph of four or more sentences all the same length; emoji used as bullets or line openers.
- Density per 500 words: the tier-one AI vocabulary at more than one, the tier-two set at more than two.

## What the design hook blocks

AI purple and indigo hexes, the `#667eea` to `#764ba2` gradient, four or more gradients in one file, gradient text, backdrop blur, `border-left: 3-8px solid` accent cards, the `rgba(0,0,0,0.1)` shadow, hairline borders under 0.08 alpha, decorative blur over 20px, `filter: drop-shadow`, Inter / Geist / Space Grotesk in a font stack, Lucide icons, fake terminal-window props, `border-bottom` on headings, decorative `<hr>`.

Judgment-only visual tells (bento grids, three feature cards, fake testimonials, slide eyebrows, explainer captions, pills and status dots, corner labels) live in `references/design-slop-patterns.md` for the review agent.

## Tells learned from draft-versus-sent comparisons

Patterns caught by comparing AI drafts with what a person actually sent in the same thread. They outrank the generic lists when writing in someone's voice or for their review.

1. Em dashes are banned outright, not at a density. The inline separator is a plain hyphen.
2. Over-committing. A draft said "locked" where the sender wrote "proposing". Never commit the author harder than the verified facts: cover what is agreed, ask the clarifying question, never blanket-approve money or scope.
3. Sectioned essays where numbered questions suffice. Real pushback is two or three numbered questions. Headers, when an email truly needs them, are bold sentence case.
4. Compression that drops substance. The unit of cutting is the word, never the point. Half the words, all the points; a cut that removes a point is a loss.
5. Promise language versus act language. "I'll loop in the team" is a promise; "I have informed the team" is an act. Act first, then reference the act.
6. Doom warnings and public assignments in client chat. Open questions and offers, not directives naming who must do what in front of the client.
7. Report verbosity. For a busy reader: fragments over grammar, no preamble, the outcome first. Repeating the ask back is padding.
8. Duplicate artifacts. Revising by creating a second file and leaving the first is a slop workflow. Revise in place.
9. Fake completion language. "Done", "created", "sent" without a tool having run. No tool response, it did not happen.
10. Bold-lead paragraphs. A bold fragment as a pseudo-title, then body prose in the same paragraph. Drop the bold; write the sentence.
11. Middots as connective tissue. Use a word, a comma, or a line break.
12. Slide furniture. Page-number dots, upper-right kickers, per-slide section titles. Let the headline carry the point.
13. Over-titling. A label that repeats the headline, a footer descriptor repeated on every frame, a credit line stated twice.
14. Bar lines under headings, in CSS or as the rule a heading border becomes in a converted Google Doc. Weight and whitespace mark the section.
15. Explainer furniture. A heading that glosses the artifact instead of naming the subject, and a footer caption that re-explains the slide above it.
16. Unranked points in an argument. An inventory (a sweep, a ledger, a roll-up) is exhaustive and flat by design. A thesis document (memo, proposal, decision doc) that reads flat has not found its argument: surface the three points that carry the decision, demote the rest.

## Review gate after every implementation

Before presenting a feature, a document, a design, copy, or UI:

1. Sweep the user-facing surfaces: copy, docs, UI choices, generated designs, commit-adjacent prose.
2. Apply the five questions below, the tells above, and the relevant reference file.
3. Cut to roughly half the words while keeping every point, silently. Present only the cut version; never show a before-and-after or mention the cut.
4. Client-facing, published, or written in someone's voice: run the slop-detector agent.
5. Fix what it finds, then present. Never present with a "might be sloppy" caveat.

## The five questions

1. Would AI generate this by default? If yes, question every element.
2. Could this belong to any brand? If yes, it is not specific enough.
3. Is there a human fingerprint: a reference only a person would make, an imperfect choice, a voice?
4. Is this decorating or communicating? Remove decoration.
5. Would someone who knows the brand recognize this without the logo?

## Operating rules

- Specific beats generic. Real names, real numbers, real failures, real tools.
- Intentional beats default. If "why this?" is answered by "that is how it is usually done", it is slop.
- Rough edges signal a person. Asymmetry, an unexpected exact word, a fragment. Do not sand every edge.
- Vary rhythm. Short sentence, then one that takes its time, then short again.
- Earn every element. Delete any paragraph, visual, or section whose removal loses nothing.
- Show receipts: real data, real screenshots, real process.
- Removing slop is half the job. A clean draft with no voice is its own tell; add stance and specificity, never new claims.

## Files

| File | Purpose |
| --- | --- |
| `hooks/copy_slop_hook.py` | Copy gate |
| `hooks/design_slop_hook.py` | Visual gate |
| `hooks/artifact_slop_hook.py` | Artifact and Drive connector gate |
| `references/copy-slop-dictionary.md` | Full copy catalog, including judgment tells the hook cannot regex |
| `references/design-slop-patterns.md` | Visual and slide tells |
| `references/what-humans-do.md` | What to do instead |
| `references/image-slop-tells.md`, `social-slop-patterns.md`, `video-slop-tells.md`, `website-slop-formula.md` | Secondary catalogs by medium |
| `agents/slop-detector.md` | Audit agent: score, violations, top fixes |
| `agents/copy-humanizer.md` | Rewrite agent: strip tells, then add voice |
