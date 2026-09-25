# Wiring qa-review into an agent's loop

Drop this into a project's `CLAUDE.md` (or `AGENTS.md`) so the coding agent runs the QA gate at the right moments without being told each time. It is a recipe, not enforcement; the agent still reads the run summary and reports.

## CLAUDE.md snippet

```
## QA gate (qa-review)
- After a change set that touches the app UI, run `qa-review smoke`. Read only the run summary; fix any red before moving on.
- Before marking a feature done, run `qa-review functional` (change-scoped). It publishes the branded proof and stamps the certified commit. Do not call a feature done on a red proof.
- Before a release, run `qa-review regression`. Ship only on a GREENLIGHT verdict.
- Never silence a red to pass. A defect is a blocker; a stale flow is repaired and rerun.
```

## Optional hook

A PostToolUse hook can nudge the agent after a batch of edits. Keep it a reminder, not a blocking gate, so it never wedges the session. Example shape (adjust to the host's hook format):

```
{
  "PostToolUse": [
    {
      "matcher": "Edit|Write",
      "hint": "If this finished a UI change set, run `qa-review smoke` before continuing."
    }
  ]
}
```

## Notes

- The gate needs `.maestro/qa-review.config.json` in the repo. First time on a repo, run `qa-review setup` (or `regression` seeds it).
- Token cost stays low: the scripts drive the app and build the report; the agent reads only `run-summary.json`.
- The proof wears the app's own brand automatically, no per-project theming.
