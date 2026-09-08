---
"jarrheyd-skills": patch
---

qa-review opens the report from the runner. scout-run.sh now calls a new open-report.sh at the end of every run, so a finished run always puts report.html on screen instead of relying on the agent to remember the step. SCOUT_NO_OPEN=1 or CI keeps it closed, SCOUT_OPEN_CMD overrides the opener.
