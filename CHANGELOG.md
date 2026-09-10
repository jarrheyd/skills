# Changelog

## 2.1.0

### Minor Changes

- [`f9da7ec`](https://github.com/jarrheyd/skills/commit/f9da7ec575ad4cbd52d9e1c7150465945a0882ef) Thanks [@jarrheyd](https://github.com/jarrheyd)! - deslop learns from the 2026 Economist study on spotting AI writing. The copy hook now blocks "not only X but also Y" when both halves sit in one sentence, alongside the "not X but Y" family it already caught. The dictionary records the study's real finding: the modern tells are what AI leaves out, so a note explains that em dashes are no longer a reliable AI fingerprint (only Claude overuses them) and stay blocked as house style, not as evidence, and what-humans-do.md gains two counter-patterns, the punctuation people reach for that AI skips (commas, semicolons, parentheses, a short sentence after a long one) and quoting a real named person. "maximise" and its long-word cousins join the density-flagged list.

- [`045cf6c`](https://github.com/jarrheyd/skills/commit/045cf6c3a019e6fd70831ca9072ed8c11e6238a2) Thanks [@jarrheyd](https://github.com/jarrheyd)! - deslop now catches the absence tells, the things AI leaves out per the 2026 Economist study, in the review path. A new scripts/flat_prose.py reads flowing prose over ~150 words (lists, code, tables and headings stripped first) and prints one plain nudge when several signals agree the prose is flat: long even sentences, no semicolons, no parenthetical asides. It never blocks (exit 0 always) and never prints numbers, so it stays out of the zero-tolerance write hooks where a bullet list or commit message would trip it. The slop-detector agent runs it in its density pass, and SKILL.md documents it as review-only.

## 2.0.0

### Major Changes

- [`564809d`](https://github.com/jarrheyd/skills/commit/564809dc541deb04e4b8241442eb58ae2af83486) Thanks [@jarrheyd](https://github.com/jarrheyd)! - qa-review drops the scout name. The runner is now qa-review-run.sh, the config is qa-review.config.json, control variables take the QA*REVIEW* prefix, and evidence lives in ~/.qa-review. No fallback to the old names: a project onboarded earlier must migrate all four, and MIGRATING.md has the commands. The scout alias is gone from the skill description.

### Minor Changes

- [`37219a5`](https://github.com/jarrheyd/skills/commit/37219a52e8e2a07fa47a8e4419ab79f45389b795) Thanks [@jarrheyd](https://github.com/jarrheyd)! - qa-review carries the previous run forward. A flow that did not run this time now shows its last screenshots instead of an empty card, and counts toward green only while that evidence still describes the build under test and is under 7 days old. Each run fingerprints what was installed (the simulator or device binary, or the commit for web), so evidence survives SKIP_BUILD reruns but expires the moment the binary changes. Expired evidence still shows, dimmed, with the reason and its original date. The header now counts verified, carried, needing a rerun and never run separately, so a partial run cannot read as a full pass. Fixes the off-by-one that made the existing carry-forward pick a report two runs back, which pruning had usually deleted, so nothing was ever carried.

### Patch Changes

- [`938742c`](https://github.com/jarrheyd/skills/commit/938742cad177d76121ec9c7284fa706f3b2aeb51) Thanks [@jarrheyd](https://github.com/jarrheyd)! - qa-review opens the report from the runner. scout-run.sh now calls a new open-report.sh at the end of every run, so a finished run always puts report.html on screen instead of relying on the agent to remember the step. SCOUT_NO_OPEN=1 or CI keeps it closed, SCOUT_OPEN_CMD overrides the opener.

## 1.1.0

### Minor Changes

- [`a4ba1b7`](https://github.com/jarrheyd/skills/commit/a4ba1b7b78b5a427b2fbfa1bcca98c291afc86c7) Thanks [@jarrheyd](https://github.com/jarrheyd)! - deslop catches hook-and-reveal rhythms: elliptical setups, suspense-then-answer, unneeded justifiers, revelation hooks, big-reveal frames, overhype, "will revolutionize", "fast-changing world", "dive into", opposing shutdowns, philosophical reductions, "no X, no Y, just Z", three adjectives in a row, the law of threes, uniform sentence length, and emoji bullets.

### Patch Changes

- [`2e8e106`](https://github.com/jarrheyd/skills/commit/2e8e10604c99124dacf19286536a5c9548034ac9) Thanks [@jarrheyd](https://github.com/jarrheyd)! - scout-run runs flows one invocation each by default (Maestro aborts a multi-flow run on an unresolved addMedia path with nothing executed) with a portable perl-alarm timeout, and guard-env accepts app-scheme deep links (kapwa://...) since they open the already-approved installed build.

## 1.0.0

### Major Changes

- [`0d53333`](https://github.com/jarrheyd/skills/commit/0d53333a09a73c15442c67e1756d337bf1bbf842) Thanks [@jarrheyd](https://github.com/jarrheyd)! - First release as one repo and one plugin. deslop, qa-review and product-review move in from their own repos with history. deslop's hook now catches every pattern its docs list and its docs pass their own gate; qa-review's summary and report agree after a retry and the production guard matches hostname labels instead of substrings; product-review validates `review.json` and ships a recorded example.
