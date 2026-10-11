# Where a fix lands

Pick the first row that fits. A project's `retro-targets.md` overrides the right-hand column with real paths.

| What the moment shows | Kind of fix | Where it goes |
|---|---|---|
| A mistake a program could have caught (format, banned word, wrong file touched, duplicate write, missing test run) | Automated check | A hook in the agent settings, a lint rule, a test, or a step in an existing script |
| A rule exists and the agent broke it anyway | Automated check | Same as above. Remove nothing from the prose rule, add the check that enforces it |
| A scheduled routine did the wrong thing or skipped a step | Routine prompt or code | That routine's prompt file, or the script it runs. If the step is mechanical, move it from prompt to code |
| A subagent or crew did the wrong thing | Agent definition | That agent's file, or the crew's instructions |
| The person stated a fact or preference (who someone is, how they like drafts, which tool to use) | Memory | One memory file per fact. Update the existing file when one covers it |
| The agent searched a long time for a file or a fact | Pointer | An index or map file, or one line in the project's steering file that says where it is |
| Two instructions disagree | Reconcile | Edit the stale one. If you cannot tell which is current, ask |
| An instruction points at a file, tool or agent that no longer exists | Repair | Fix the pointer or remove the line |
| The agent lacked access (not logged in, missing permission, server down) | Access | Config or permissions. If it needs a credential, ask |
| A tool failed over and over | Tooling | Fix the wrapper or script, pin the version, or add a retry. Note the workaround in memory only if the tool cannot be fixed |
| The person declined a tool call | Permission or rule | A rule that stops the agent trying it, or an allow rule if they said it was fine and the prompt was noise |
| A run died and the person had to type "try again" | Resilience | Checkpoint the routine so a rerun resumes, split the long step, or move the heavy work to a script |
| A rule that holds in every session and project | Steering file | `CLAUDE.md` or `AGENTS.md`, kept short |

## Mechanical or judgement

Mechanical means a program can decide pass or fail from the text or the files alone. Those get a check. Judgement means a person would have to weigh it. Those get one plain sentence in the place the agent reads at the moment it matters, such as the skill or routine that was running, and not in a file that loads everywhere.

## Signs a fix is wrong

- It restates a rule that already exists in another file.
- It names a moment from one session and bans something that is fine everywhere else.
- It makes a steering file longer without removing anything.
- It cannot be verified.
