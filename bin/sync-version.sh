#!/usr/bin/env bash
# Sync version across plugin manifests from the canonical VERSION file.
# Usage: bin/sync-version.sh [write|check]
#   write — stamp VERSION into all manifests (default)
#   check — fail if any manifest drifts from VERSION

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VERSION="$(cat "$ROOT/VERSION")"
mode="${1:-write}"

update() {
  local file="$1" path="$2"
  if [ ! -f "$file" ]; then
    echo "skip: $file not present" >&2
    return 0
  fi
  if [ "$mode" = "check" ]; then
    local current
    current="$(jq -r "$path" "$file")"
    if [ "$current" != "$VERSION" ]; then
      echo "drift: $file has $current, VERSION=$VERSION" >&2
      exit 1
    fi
  else
    local tmp
    tmp="$(mktemp)"
    jq "$path = \"$VERSION\"" "$file" > "$tmp" && mv "$tmp" "$file"
    echo "stamped: $file → $VERSION"
  fi
}

update "$ROOT/.claude-plugin/plugin.json" '.version'
update "$ROOT/.claude-plugin/marketplace.json" '.plugins[0].version'

if [ "$mode" = "check" ]; then
  echo "ok: all manifests at $VERSION"
fi
