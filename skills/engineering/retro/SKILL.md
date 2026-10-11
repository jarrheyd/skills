---
name: retro
description: Reads Claude session transcripts, finds where the person corrected the agent, repeated themselves, interrupted, or where a tool kept failing, and fixes the environment so it does not happen again. Fixes land in skills, hooks, agent files, routine prompts, memory and steering files, each one backed up and logged. Use when the user says "retro", "learn from this session", "why do I keep correcting you", or when a weekly routine reviews the week's sessions.
version: 1.0.0
user-invocable: true
argument-hint: "[session-id | --since 7d]"
license: MIT
---

# retro

A retro reads what happened in a session and changes the setup around the agent, so the next session does not need the same correction. It leaves the work product alone, since the person already fixed that when they corrected you.

It applies the fixes itself. Proposals get misread as finished work, so anything this skill can do safely it does, and anything it cannot do goes to the person as one question with a recommended answer.

## Inputs

- With no argument it reviews the session you are in, through `--latest --cwd <working directory>`.
- With a session id it reviews that session, through `--session <id>`.
- With `--since 7d` (or `12h`, or an ISO date) it reviews every session touched since then, across all projects. Add `--digest` so a whole week fits in one read.

```bash
node scripts/harvest.mjs --latest --cwd "$PWD"
node scripts/harvest.mjs --since 7d --digest --out <scratch>/moments.md
```

Write harvest output to a scratch or local-only folder. It contains the person's own words, so it never goes into a synced folder, a repo or a report.

## What a moment is

The harvest returns one line per moment, with what the agent said and ran just before it.

| Kind | Meaning |
|---|---|
| `reply` | The person typed something after the agent acted. Most are plain next steps and some are corrections. `hint: correction` is a regex guess, so read the text yourself |
| `reply mid-turn` | They cut in while the agent was still working, which usually means it was heading the wrong way |
| `repeat` | They sent the same message again in the same session |
| `interrupt` | They stopped the agent |
| `retry` | "try again" or "continue" after the run died or stalled |
| `tool-fail` | One tool failed three times in a row |
| `denied` | They declined a tool call |

Messages written by automation (scheduled prompts, other sessions, scripts) are already dropped.

## Steps

1. Harvest.
2. Read every moment and keep the ones where the setup let the person down: a correction, a preference stated for the second time, a wrong assumption, a search that took ten tool calls, a tool that failed over and over, a call they declined. A plain next instruction is not a finding.
3. Group what you kept into findings. Each finding quotes at least one moment with its session and time, and a finding you cannot trace to a moment is dropped.
4. For each finding, look for the rule that should have prevented it in memory files, the steering files (`CLAUDE.md`, `AGENTS.md`), the skill or routine that was running, and the hooks. There are three outcomes:
   - No rule exists, so write one in the place the routing table names.
   - A rule exists and was not followed. More prose will not help here, so turn it into a check that runs by itself, such as a hook, a lint, a test or a script step.
   - Two rules disagree, or the rule points at something that no longer exists, so fix or remove the stale one.
5. Route the fix with `references/routing.md`. If the project has a `retro-targets.md` (look in the working directory, then `_meta/`), it names the real files for this setup and wins over the generic table.
6. Apply each fix:
   - Copy the file to the backup folder first (`retro-targets.md` names it; otherwise `.retro-backups/<date>/` next to the file). In a git repo, a commit is the backup.
   - Make the smallest edit that closes the gap, and update an existing rule before adding a new one.
   - Verify it by running the tests, firing the hook on one sample that should fail and one that should pass, or syntax-checking the script. A fix that fails verification is rolled back from the backup and reported as not done.
7. Log one line per change in the retro log (`retro-targets.md` names it; otherwise `RETRO.md` at the repo root) with the date, the file, what changed, the moment behind it and where the backup is.
8. Report in this order:
   - Done, with one line per change and its file.
   - Not done, for anything that failed verification, with the reason.
   - Needs you, asked through the question tool with the recommended option first. These never sit in a list for the person to notice.

## What goes to the person instead of being applied

- Deleting data, files, branches or worktrees.
- Anything that needs a password, token or login.
- A choice between two things they said that conflict, when the transcript does not show which one is current.
- Spending money, or sending anything to another person.

Everything outside that list gets applied.

## Limits that keep the setup healthy

- Steering files load into every session, so a rule goes there only when it applies to every session. A fact about one project goes in memory or in that project's files.
- Each finding gets one fix, so a whole file is never rewritten because one line was wrong.
- If the same finding shows up for the third week, the earlier fixes did not work. Say so and change the kind of fix, from prose to a check.
- A week of sessions can hold a thousand moments, so read the digest session by session and note findings as you go. Past roughly 300KB, hand each project's sessions to a subagent with steps 2 to 4 and merge their findings before applying anything, so two fixes never hit the same file blind.
- When the retro runs unattended, apply and log as usual and end on the question for the person, which waits for them.
