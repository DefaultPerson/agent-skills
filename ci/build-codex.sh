#!/usr/bin/env bash
# build-codex.sh — make each Codex skill self-contained for native packaging.
#
# `codex plugin add` copies the whole plugin into its cache and STRIPS symlinks,
# so a Codex skill cannot borrow its references/scripts/templates/roles from the
# Claude tree at runtime — it must carry real copies. This script syncs those
# shared asset subdirs from the Claude tree (skills/<name>/, the source of truth)
# into the Codex tree (skills-codex/<name>/).
#
# `workflows/` is intentionally NOT copied — Codex has no Workflow tool.
# Only asset subdirs are touched; the Codex-variant SKILL.md is never modified.
# Idempotent: re-run after editing any shared asset. CI (ci/validate.py) asserts
# the copies stay byte-identical to their source.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ASSETS="references scripts templates roles"

for d in "$ROOT"/skills-codex/*/; do
  name="$(basename "$d")"
  src="$ROOT/skills/$name"
  for sub in $ASSETS; do
    rm -rf "${d%/}/$sub"
    if [ -d "$src/$sub" ]; then
      cp -R "$src/$sub" "${d%/}/$sub"
    fi
  done
done

# Drop Python bytecode caches that may ride along from the source tree.
find "$ROOT/skills-codex" -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

echo "Codex assets synced: skills/ → skills-codex/ ($ASSETS; workflows/ skipped)."
