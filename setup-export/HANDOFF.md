# Handoff for her Claude Code

You are installing a copy of Jarrhey's Claude Code setup on her machine. This folder mirrors `~/.claude`, so copy `CLAUDE.md`, `settings.json`, `statusline-command.sh`, `hooks/`, and `skills/` into the same places under her `~/.claude`, merging into her existing files instead of overwriting them. Every `<ADD YOUR OWN>` needs her value, and any step marked "her call" waits for her answer.

## Summary

1. Global rules make Claude grill a feature before planning, loop until it is verified, audit any UI, and pass every output through the deslop gate.
2. Hooks catch the usual agent mistakes before they land: risky deletes, wide disk scans, idle-billing deploys, AI-labeled comments, wrapped Gmail links, duplicate tickets, and chats that stop with steps still open.
3. Skills add UI craft (impeccable, Emil Kowalski's motion set, apple-design), throwaway prototypes, design-system enforcement, document review, and a duplicate-ticket ledger on top of the jarrheyd-skills plugin.

## Already in the repo

She has jarrheyd-skills 2.0.0 (installed 10 Sep 2026). The repo is now at 2.2.2, plus changes merged to main on 6 Nov that are not versioned yet. Update the plugin from its marketplace (`/plugin`, then update jarrheyd-skills), then check the version in `~/.claude/plugins/installed_plugins.json`.

What changed since 2.0.0:

| Version | What changed |
|---|---|
| 2.1.0 | deslop: blocks a comma in a short display heading, staccato two-beat headings, and the not-only/but-also frame. Gates email drafts, ticket comments, and chat sends (the wiring for those lives in `settings.json` here, since the plugin only wires file writes). Adds `scripts/flat_prose.py` as a review-only check and seven deck tells for the review agent. product-review: a screenshot on every flow, and a READY or NOT READY rollup. qa-review: a numbered test-case matrix and a failure class on every red (CRASH, DEFECT, FLOW-ROT, ENV). |
| 2.2.0 | New skill: retro (reads session transcripts and fixes the setup behind each correction). deslop: checks prose typed through browser tools and blocks UI copy that explains itself, bold section labels on three or more blocks, and even-length sentence runs. qa-review: a web repo can set `"runner": "playwright"`. |
| 2.2.1 | deslop catches short fragment runs and more tells. Regression runs reinstall the Playwright browser first. |
| 2.2.2 | deslop adds a document check script, `hooks/bash_doc_gate.py` (gates docs written through Bash), and shape-tell detection. retro drops "continue" retries after API errors. |
| main, unreleased | deslop splits into shared checks (on by default) and one author's house rules, which run only when `$DESLOP_DATA/house-rules.md` exists or `DESLOP_HOUSE=1`. Adds a guide for building a voice from the person's own writing. The design hook flags a near-black background with a big italic serif, and gradient counts skip functional CSS. |

`settings.json` here calls `bash_doc_gate.py`, which only exists from 2.2.2, so update the plugin before merging settings.

## Connected apps

| Name | Comes from | Type | Status on my machine | What it's for | She has it? |
|---|---|---|---|---|---|
| Gmail | Anthropic (claude.ai) | connector | needs sign-in | Read mail and make drafts. | yes |
| Google Calendar | Anthropic (claude.ai) | connector | needs sign-in | Read and create events. | yes |
| Google Drive | Anthropic (claude.ai) | connector | needs sign-in | Find, read, and create Drive files. | yes |
| Google Docs | Anthropic (claude.ai) | connector | needs sign-in | Read and edit Docs. | yes |
| Google Sheets | Anthropic (claude.ai) | connector | needs sign-in | Read and edit Sheets. | yes |
| Google Slides | Anthropic (claude.ai) | connector | needs sign-in | Read and edit decks. | yes |
| Atlassian Rovo (Jira and Confluence) | Atlassian | connector | needs sign-in | Tickets, comments, and Confluence pages. | yes |
| Claude Docs | Anthropic | connector | working | Shared docs people comment on. | yes |
| Microsoft 365 | Microsoft | connector | not active | Outlook and Teams for Microsoft-side work. | yes |
| Tactiq | Tactiq | connector | not active | Meeting transcripts. | yes |
| Circleback | Circleback | connector | not active | Meeting notes. | yes |
| Webflow | Webflow | connector | not active | Website CMS edits. | yes |
| Slack | Slack | connector | needs sign-in | Slack messages. | no |
| Notion | Notion | connector | needs sign-in | Notion pages. | no |
| Linear | Linear | connector | needs sign-in | Linear issues. | no |
| Asana | Asana | connector | needs sign-in | Asana tasks. | no |
| Box | Box | connector | needs sign-in | Box files. | no |
| Canva | Canva | connector | needs sign-in | Canva designs. | no |
| HubSpot | HubSpot | connector | needs sign-in | CRM records. | no |
| Intercom | Intercom | connector | needs sign-in | Support conversations. | no |
| monday.com | monday.com | connector | needs sign-in | monday boards. | no |
| Figma | Figma | MCP server (remote) | working | Read and write Figma files. | yes |
| Gmail (local) | gmail-mcp-server (npm) | MCP server | working | Gmail search, read, and drafts outside claude.ai. | no |
| Google Drive (local) | @isaacphi/mcp-gdrive | MCP server | working | Drive search and Sheets cell reads and writes. | no |
| Google Calendar (local) | @cocal/google-calendar-mcp | MCP server | working | Calendar across several Google accounts. | no |
| HubSpot (local) | @hubspot/mcp-server | MCP server | working | CRM reads and writes with a private app token. | no |
| Discord | barryyip0625/mcp-discord | MCP server | working | Read and post in Discord channels. | no |
| Google Chat (read-only) | Jarrhey's own | MCP server | working | Read Google Chat spaces. | no |
| Beeper (read-only) | Jarrhey's own, on Beeper Desktop | MCP server | working | Read WhatsApp, Telegram, and Viber chats in one place. | no |
| Outlook personal | Jarrhey's own | MCP server | working | Read a personal Outlook inbox. | no |
| Pocket | Pocket AI, through mcp-remote | MCP server | working | Recordings and transcripts from the Pocket device. | no |
| Jira, second site | mcp-atlassian (sooperset) | MCP server | working | A second Jira site for client work. | no |
| Chrome DevTools | Google (chrome-devtools-mcp) | MCP server | working | Drive his own Chrome on a debug port. | no |
| Playwright | Microsoft (@playwright/mcp) | MCP server | working | Headless browser checks. | no |
| Claude in Chrome | Anthropic | browser extension | working | Act in the logged-in Chrome. | no |
| Gemini | @rlabs-inc/gemini-mcp | MCP server | not working | Gemini calls for video and image review. | no |
| internal tool, not shared | internal | MCP server | needs sign-in | internal tool, not shared | no |
| one client connector | client | connector | needs sign-in | client work, not shared | no |
| jarrheyd-skills | Jarrhey | plugin (he links it from the repo) | working | deslop, qa-review, product-review, retro. | yes |
| swift-lsp | Anthropic | plugin | working | Swift language server for iOS code. | no |
| cloudflare | Cloudflare | plugin | needs sign-in | Cloudflare skills (turned off) and MCP. | no |
| frontend-design | Anthropic | plugin | not active | On in one personal repo only. | no |
| rm guard | Jarrhey | hook | working | Stops risky deletes and whole-disk searches. | no |
| deslop on sends and browser typing | Jarrhey (plugin scripts) | hook | working | Runs deslop on drafts, sends, comments, and Bash-written docs. | no |
| write-ledger | Jarrhey | hook | working | Blocks duplicate tickets and comments. | no |
| unwrap links | Jarrhey | hook | working | Blocks Gmail redirect links in drafts. | no |
| no AI comment label | Jarrhey | hook | working | Blocks comments that read like machine notes. | no |
| skill gate | Jarrhey | hook | working | Makes a write wait until its skill is loaded. | no |
| cloud cost guard | Jarrhey | hook | working | Blocks Cloud Run setups that bill while idle. | no |
| reply draft images | Jarrhey | hook | working | Strips copied signature images from Gmail reply drafts. | no |
| picker dismissed | Jarrhey | hook | working | Keeps a dismissed question open. | no |
| open steps | Jarrhey | hook | working | Stops a turn that offers steps it should just do. | no |
| auto allow | Jarrhey | hook | working | Answers permission prompts except sends, deletes, and pushes to main. | no |
| internal hooks (18) | Jarrhey | hook | working | internal tool, not shared | no |
| status line | Jarrhey | script | working | Shows the billing org, folder, model, and context use. | no |
| skill sync | Jarrhey | scheduled task | working | Weekly push of his skills repo when it has edits. | no |
| laptop cleanup jobs | Jarrhey | scheduled task | working | Reclaim disk and memory, reap stray processes. | no |
| cloud billing and cost scans | Jarrhey | scheduled task | working | Daily and weekly idle-spend checks on Google Cloud. | no |
| assistant and project routines | Jarrhey | scheduled task | working | Hourly inbox brief and per-project sweeps, tied to his notes and clients. | no |
| local MCP proxies | mcp-proxy (sparfenyuk) via launchd | script | working | Runs each local MCP server once and shares it across chats. | no |

## Items

| Name | What it does | Where it goes | Needs | Paths only on my machine | She sets up |
|---|---|---|---|---|---|
| `CLAUDE.md` | Global rules: grill first, plan, loop until verified, UI audit, deslop, least code, reporting budget, live threads, no AI attribution. | `~/.claude/CLAUDE.md` (merge) | nothing | none | Her voice notes path. |
| `settings.json` env | Autocompact at 40%, MCP timeout 90s, agent teams on, deslop skip path, `DESLOP_HOOKS`. | `~/.claude/settings.json` (merge) | nothing | none | `DESLOP_HOOKS` = her plugin's `skills/writing/deslop/hooks` folder. Find it with `ls -d ~/.claude/plugins/cache/*/jarrheyd-skills/*/skills/writing/deslop/hooks`. |
| `settings.json` permissions | `bypassPermissions` default; allows connector drafts, Drive file writes, Jira and Confluence writes, worktrees, and memory edits. | same file | nothing | none | Her call on `bypassPermissions`. |
| `settings.json` model block | Opus, high effort, thinking always on, output style "Proactive". | same file | nothing | none | Drop `outputStyle` if she has no style by that name. |
| `settings.json` skillOverrides | Turns off the Cloudflare plugin's skills and animation-vocabulary. | same file | nothing | none | none |
| `settings.json` hooks | Wires every hook below. | same file | python3 | none (all `~/.claude/...`) | none |
| `settings.json` statusLine | Runs `sh ~/.claude/statusline-command.sh`. | same file | jq | none | none |
| `settings.json` plugins | Enables swift-lsp and cloudflare, adds the cloudflare/skills marketplace. | same file | Xcode for swift-lsp | none | Her call; both are optional. |
| `settings.json` autoMode | Extra allow and soft-deny rules for auto mode. | same file | nothing | none | `environment`: her org, cloud, repos, and protected branches. |
| `settings.json` UI | Fullscreen TUI, hold-to-talk voice, auto theme, remote control at startup, notifications. | same file | nothing | none | none |
| `statusline-command.sh` | Colors the billing org so a personal-token chat is obvious. | `~/.claude/statusline-command.sh` | jq | none | Her org names in the `case` block. |
| `hooks/rm_guard.py` | PreToolUse Bash. Denies `rm` with a variable or glob path and `find` over `/` or `~`, with the rewrite to use. | `~/.claude/hooks/` | python3 | none | Off: `RM_GUARD_OFF=1`. Test: `python3 rm_guard.py --test`. |
| deslop on sends | PreToolUse on MCP draft, send, comment, and ticket tools, and on Claude in Chrome typing. Runs the plugin's `copy_slop_hook.py`. | settings only | plugin 2.2.2 or later | none | `DESLOP_HOOKS`. |
| deslop Bash doc gate | PreToolUse Bash. Runs the plugin's `bash_doc_gate.py` on docs written through the shell. | settings only | plugin 2.2.2 or later | none | `DESLOP_HOOKS`. |
| `hooks/unwrap_links_hook.py` | PreToolUse on drafts and sends. Blocks `google.com/url?q=` links and gives the real link. | `~/.claude/hooks/` | python3 | none | none |
| `hooks/no_ai_comment_label.py` | PreToolUse on Bash and every MCP tool. Blocks a comment that opens with "Claude:", talks to the owner instead of the reader, or opens with a status label. | `~/.claude/hooks/` | python3 | none | Post anyway: `VOICE_OK=1` in the command. |
| `hooks/skill_gate_hook.py` + `skill_routes.json` | PreToolUse writes. A logo file waits for logo-design, a UI file for impeccable, motion code for apple-design. | `~/.claude/hooks/` | python3, those three skills | none | Remove a route for a skill she does not install. Off: `DISABLE_SKILL_GATE=1`. |
| `hooks/cloud_cost_hook.py` | PreToolUse Bash and writes. Blocks `gcloud run deploy` without `--min-instances=0`, revision minimums above 0, tags never removed, and browser tests before lint. | `~/.claude/hooks/` | python3 | none | Off: `COST_GUARD_OFF=1`; one-off: `COST_OK=<reason>`. Test: `--test`. |
| write-ledger hooks | PreToolUse and PostToolUse on ticket creates and comments. Shadow mode logs would-be duplicates; `LEDGER_ENFORCE=1` blocks them. | `~/.claude/skills/write-ledger/` | python3 | none | Ledger folder defaults to `~/.claude/write-ledger`. Test: `python3 test_write_ledger.py`. |
| `hooks/reply_draft_images_hook.py` | PostToolUse on `create_draft`. Tells Claude to resave a Gmail reply so copied signature images drop off. | `~/.claude/hooks/` | python3 | none | none |
| `hooks/picker_dismissed_hook.py` | PostToolUse AskUserQuestion. A dismissed picker stays an open question. | `~/.claude/hooks/` | python3 | none | none |
| `hooks/open_steps_stop_hook.py` | Stop. A turn that ends on "want me to" while its todo list has open steps goes back once to do them. | `~/.claude/hooks/` | python3 | none | none |
| `hooks/auto_allow.py` | PermissionRequest. Allows prompts except questions, sends, posts, deletes, force pushes, pushes to main, and sudo. Logs to `~/.cache/claude-hooks/auto-allow.log`. | `~/.claude/hooks/` | python3 | none | Her call. Off: `AUTO_ALLOW_OFF=1`. |
| `hooks/hooklog.py` | Optional fire log the hooks import; writes `~/.local/state/claude-hooks/hook-log.jsonl`. | `~/.claude/hooks/` | python3 | none | none |
| `skills/prototype` | Throwaway prototype: a terminal app for logic questions or several UI variations on one route. | `~/.claude/skills/prototype` | nothing | none | none |
| `skills/design-system` | Design director and auditor for app UI against a project's `DESIGN-SYSTEM.md`, with audit scripts. Its `hooks/hooks.json` is not wired on his machine. | `~/.claude/skills/design-system` | bash for the scripts | none | A brand references source, if she keeps one. |
| `skills/document-review` | Integrity review for SOWs, proposals, contracts, minutes, and decks before they leave the company. | `~/.claude/skills/document-review` | nothing | none | none |
| `skills/write-ledger` | Duplicate-ticket gate described above, plus `backfill.py` to seed it. | `~/.claude/skills/write-ledger` | python3 | none | Run the backfill before turning enforce on. |
| grill-me | Interview about a plan until every branch is settled. | `~/.claude/skills/grill-me` | nothing | n/a, not copied | Install from Matt Pocock's skills repo. |
| impeccable (4.0.2) | Frontend design, critique, and audit. | `~/.claude/skills/impeccable` | node for its scripts | n/a, not copied | Install from Paul Bakaus's impeccable repo. |
| Emil Kowalski set | emil-design-eng, emil-prototype, review-animations, improve-animations, find-animation-opportunities, animation-vocabulary, pick-ui-library. | `~/.claude/skills/<name>` | nothing | copied in `skills/` | Copy each folder. |
| apple-design | Apple-style motion, gestures, and type for the web. | `~/.claude/skills/apple-design` | nothing | copied in `skills/` | Copy the folder. |
| logo-design | Logo work from brief to production files, with a reference library. | `~/.claude/skills/logo-design` | python3 for its scripts | copied in `skills/` | Copy the folder. |
| Figma MCP | `{"type": "http", "url": "https://mcp.figma.com/mcp"}` in `mcpServers` of `~/.claude.json`. | `~/.claude.json` | Figma login | none | She has it already. |
| Chrome DevTools MCP | `chrome-devtools-mcp --browserUrl http://127.0.0.1:9223` against a Chrome started with a debug port. | `~/.claude.json` | the CLI, Chrome | yes, a Homebrew binary path | Optional. |
| Local MCP proxies | Each local server runs once under launchd through `mcp-proxy` on a localhost port; chats connect over HTTP. Configs hold tokens, so none are copied. | not shared | uv, mcp-proxy, node | yes | Only if she wants the local servers. |
| agents (12) | Content, briefing, and meeting agents tied to his own notes and channels. | not shared | n/a | yes | none |
| brand-system, marketing skills | Brand and marketing directors that read a private brand repo and his notes. | not shared | n/a | yes | none |
| internal hooks (18) and one plugin folder | internal tool, not shared | not shared | n/a | yes | none |
| scheduled tasks and launchd jobs | Tied to his notes, his Google Cloud org, and client projects. | not shared | n/a | yes | none |

## Install order

1. Update jarrheyd-skills to the newest version. Settings below call `bash_doc_gate.py`, which only exists from 2.2.2.
2. Copy every folder in `skills/` to `~/.claude/skills/` (the Emil Kowalski set, apple-design, and logo-design are in there), then install grill-me and impeccable. The skill gate and the global rules both call them.
3. Copy `skills/` here into `~/.claude/skills/`. Run `python3 ~/.claude/skills/write-ledger/test_write_ledger.py`.
4. Copy `hooks/` here into `~/.claude/hooks/`. Run `python3 ~/.claude/hooks/rm_guard.py --test` and `python3 ~/.claude/hooks/cloud_cost_hook.py --test`.
5. Copy `statusline-command.sh` to `~/.claude/` and fill in her org names. Needs `jq`.
6. Merge `settings.json` into hers key by key. Set `DESLOP_HOOKS`. Ask her about `bypassPermissions`, `auto_allow.py`, and the two plugins.
7. Merge `CLAUDE.md` into her `~/.claude/CLAUDE.md` and set her voice notes path.
8. Optional: add the Chrome DevTools MCP.
9. Restart Claude Code, open `/hooks` to confirm the wiring, then write a test file with an em dash to see deslop block it.

## Watch out for

- The plugin already wires `copy_slop_hook.py` and `design_slop_hook.py` on Write and Edit, and `artifact_slop_hook.py` on artifacts. This `settings.json` leaves those out on purpose. Adding them again runs every check twice. Jarrhey wires them in settings only because he links the repo instead of installing the plugin.
- Settings `env` values should reach hook commands, so `$DESLOP_HOOKS` expands. If `/hooks` shows the deslop hooks failing with "can't open file", replace `$DESLOP_HOOKS` with the full path.
- `bypassPermissions` plus `auto_allow.py` means almost nothing prompts. Sends, deletes, force pushes, and pushes to main still prompt.
- The skill gate blocks every `.tsx`, `.css`, or `.html` write until impeccable loads in that chat. If she skips a skill, remove its route from `skill_routes.json`, or the gate blocks writes for good.
- `no_ai_comment_label.py` runs on every Bash and MCP call. A comment that says "your call" or starts with "Claude:" gets blocked.
- `rm_guard.py` denies `rm $VAR/*` and `find ~`. Claude gets the rewrite in the deny message.
- If her settings already have Stop, PermissionRequest, or PreToolUse Bash hooks, keep both lists; each matcher entry runs on its own.
- Skill names that can clash: `prototype`, `design-system`, `document-review`, `grill-me`, and `impeccable`. If she has one with the same name, keep hers or rename one folder.
- The cloudflare plugin is enabled with its skills turned off. Its MCP still asks for a Cloudflare sign-in.
- The design-system skill's `hooks/hooks.json` only runs if that folder is installed as a plugin. As a plain skill it does nothing.
- Since the 6 Nov deslop split, house rules (American spelling, Title Case headings, named banned words) run only with `$DESLOP_DATA/house-rules.md` or `DESLOP_HOUSE=1`. Without that file she gets the shared checks only.

## Left out on purpose

- Deslop house rules, brand-system, marketing, and the global agents: they read Jarrhey's private notes and brands. She gets the shared checks.
- `bypassPermissions` and `auto_allow.py`: keep her permission prompts on until she is used to the hooks. Turn them on later if the prompts slow her down.
- `outputStyle` "Proactive" is built into Claude Code. No file is needed.
