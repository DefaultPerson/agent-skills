#!/usr/bin/env bash
# Shared helpers for agent-skills SKILL.md scripts.
# Source from any skill: source "$CLAUDE_PLUGIN_ROOT/bin/common.sh"

# Convert arbitrary string to a safe slug (branch names, dir names, spec slugs).
slug_from() {
  echo "$1" \
    | tr '[:upper:]' '[:lower:]' \
    | sed 's/[^a-z0-9]/-/g' \
    | sed 's/--*/-/g' \
    | sed 's/^-\|-$//g' \
    | cut -c1-50
}

# Detect the repo's primary remote branch (main, master, etc.).
base_branch() {
  git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null \
    | sed 's@^refs/remotes/origin/@@' \
    || echo main
}

# Append a line to .gitignore only if it isn't already there.
gitignore_add() {
  local line="$1"
  local file="${2:-.gitignore}"
  if [ ! -f "$file" ]; then
    : > "$file"
  fi
  grep -qxF "$line" "$file" 2>/dev/null \
    || echo "$line" >> "$file"
}

# One-shot fatal exit with an error line to stderr.
fatal() {
  echo "fatal: $*" >&2
  exit 1
}
