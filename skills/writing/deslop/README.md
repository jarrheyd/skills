# deslop

Started as its own repo at [jarrheyd/deslop](https://github.com/jarrheyd/deslop); that repo is archived and this folder is the live one.

A quality gate for AI-generated tells. It catches the words, phrases, structures, and visual defaults that read as machine-made, and blocks them before they ship, whoever or whatever wrote them.

It only subtracts. A clean draft with no voice is still lifeless; bring your own voice or brand model for that, and let deslop strip what the model leaves behind.

## What it does

Three checkers and a skill:

1. Copy checker (`hooks/copy_slop_hook.py`): reads prose and the string literals of source files, blocks AI copy tells.
2. Design checker (`hooks/design_slop_hook.py`): reads HTML, CSS, JSX, Vue and Svelte, blocks AI-default visual tells.
3. Artifact checker (`hooks/artifact_slop_hook.py`): runs both on artifacts and on Google Docs, Slides and Sheets created through a Drive connector, which never touch the local filesystem.
4. The skill (`SKILL.md`, `references/`, `agents/`): the manual review, with the pattern catalogs, a slop-detector agent, and a copy-humanizer agent.

The checkers are plain Python. They read a file and exit `0` (clean) or `2` (slop found), so they work as an editor hook, a git pre-commit hook, a CI step, or a call from any agent. Every hit blocks; there is no warn tier. Bypass a run with `DISABLE_ANTI_SLOP_HOOK=1`, or exempt paths that repeat by design with `DESLOP_SKIP_PATHS=_archive/,build/`.

The family list of what each checker blocks is in [SKILL.md](./SKILL.md); the literal catalog with fixes is [references/copy-slop-dictionary.md](./references/copy-slop-dictionary.md) and [references/design-slop-patterns.md](./references/design-slop-patterns.md).

## Install

As part of the `jarrheyd-skills` plugin, which wires all three hooks for you:

```bash
claude plugin marketplace add jarrheyd/skills
claude plugin install jarrheyd-skills@jarrheyd
```

Or as editable files through skills.sh, then wire the hooks yourself:

```bash
npx skills@latest add jarrheyd/skills --skill=deslop
```

```json
"PreToolUse": [
  {
    "matcher": "Write|Edit|MultiEdit",
    "hooks": [
      { "type": "command", "command": "python3 ~/.claude/skills/deslop/hooks/copy_slop_hook.py", "timeout": 5 },
      { "type": "command", "command": "python3 ~/.claude/skills/deslop/hooks/design_slop_hook.py", "timeout": 5 }
    ]
  },
  {
    "matcher": "Artifact|mcp__.*__create_file|mcp__.*__update_file",
    "hooks": [
      { "type": "command", "command": "python3 ~/.claude/skills/deslop/hooks/artifact_slop_hook.py", "timeout": 10 }
    ]
  }
]
```

Restart Claude Code; hooks load at session start.

## Run it anywhere else

The checkers read Claude Code's hook JSON on stdin, so feeding them a file is one line:

```bash
python3 -c 'import json,sys; print(json.dumps({"tool_name":"Write","tool_input":{"file_path":"draft.md","content":open("draft.md").read()}}))' \
  | python3 ~/.claude/skills/deslop/hooks/copy_slop_hook.py
```

Exit `2` means slop found, with the reasons on stderr. Wrap that in a git `pre-commit` hook, a CI step, or any agent that can run a shell.

## Customize

Add phrases to `BANNED_PHRASES`, words to `TIER1_WORDS` and `TIER2_WORDS`, and visual tells to `TELLS` in the hooks. The tests in `tests/deslop/` at the repo root pin every advertised pattern; add a case when you add a pattern.

## Layout

```
SKILL.md        the gate, the review, the rules
hooks/          copy, design, and artifact checkers
references/     full pattern catalogs (copy, design, image, social, video, website) and what humans do instead
agents/         slop-detector and copy-humanizer
```
