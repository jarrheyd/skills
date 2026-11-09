#!/bin/sh
# Status line: shows which org the chat bills to first, then the folder, the model and context use.
# Added after a night spent on personal tokens while thinking the chat was on the work org.
# Needs jq. Set your own org names in the case block below.
input=$(cat)
cwd=$(echo "$input" | jq -r '.workspace.current_dir // .cwd // ""')
model=$(echo "$input" | jq -r '.model.display_name // ""')
used=$(echo "$input" | jq -r '.context_window.used_percentage // empty')

dir=$(basename "$cwd")

cfg="${CLAUDE_CONFIG_DIR:-$HOME}"
[ "$cfg" = "$HOME/.claude" ] && cfg="$HOME"
org=$(jq -r '.oauthAccount.organizationName // empty' "$cfg/.claude.json" 2>/dev/null)
[ -n "$ANTHROPIC_API_KEY" ] && org="${org:+$org }API"
case "$org" in
  "<ADD YOUR OWN personal org name>"*) oc='\033[1;30;43m' ;;   # yellow
  "<ADD YOUR OWN work org name>"*) oc='\033[1;37;44m' ;;       # blue
  *) oc='\033[1;37;41m'; org="${org:-org?}" ;;                 # red: unknown org
esac

printf "${oc} %s \033[0m  \033[34m%s\033[0m  \033[33m%s\033[0m" "$org" "$dir" "$model"
[ -n "$used" ] && printf "  ctx: %s%%" "$used"
exit 0
