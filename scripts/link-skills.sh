#!/usr/bin/env bash
# Dev-only: symlink every skill under skills/*/ into ~/.claude/skills so a
# git pull keeps the local install current. Not an installer; end users use
# the plugin or skills.sh (see README.md).
set -euo pipefail
REPO="$(cd "$(dirname "$0")/.." && pwd)"
DEST="${1:-$HOME/.claude/skills}"
mkdir -p "$DEST"
while IFS= read -r -d '' skill_md; do
  src="$(dirname "$skill_md")"
  name="$(basename "$src")"
  target="$DEST/$name"
  if [ -e "$target" ] && [ ! -L "$target" ]; then
    echo "skip $name: $target is a real directory, remove it first" >&2
    continue
  fi
  ln -sfn "$src" "$target"
  echo "linked $name -> $src"
done < <(find "$REPO/skills" -mindepth 3 -maxdepth 3 -name SKILL.md -print0)
