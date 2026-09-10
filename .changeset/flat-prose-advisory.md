---
"jarrheyd-skills": minor
---

deslop now catches the absence tells, the things AI leaves out per the 2026 Economist study, in the review path. A new scripts/flat_prose.py reads flowing prose over ~150 words (lists, code, tables and headings stripped first) and prints one plain nudge when several signals agree the prose is flat: long even sentences, no semicolons, no parenthetical asides. It never blocks (exit 0 always) and never prints numbers, so it stays out of the zero-tolerance write hooks where a bullet list or commit message would trip it. The slop-detector agent runs it in its density pass, and SKILL.md documents it as review-only.
