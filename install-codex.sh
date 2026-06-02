#!/usr/bin/env bash
# install-codex.sh — install Codex variants of agent-skills via symlinks
#
# Creates per-skill directories in ~/.codex/skills/ with:
#   - SKILL.md → symlink to <repo>/skills-codex/<name>/SKILL.md
#   - roles/scripts/references/ → symlinks to <repo>/skills/<name>/<subdir>/ (shared)
#
# Idempotent: safe to re-run after `git pull` to refresh symlinks.
set -euo pipefail

PLUGIN_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEST_ROOT="$HOME/.codex/skills"

for skill in cleanup clarify extract diagnose deepen svgl; do
  src_codex="$PLUGIN_ROOT/skills-codex/$skill/SKILL.md"
  src_claude_dir="$PLUGIN_ROOT/skills/$skill"
  dst="$DEST_ROOT/$skill"

  if [ ! -f "$src_codex" ]; then
    echo "skip: $skill — no Codex variant at $src_codex" >&2
    continue
  fi

  mkdir -p "$dst"

  # 1. Codex-variant SKILL.md
  ln -sfn "$src_codex" "$dst/SKILL.md"

  # 2. Shared subdirs (roles/scripts/references) — symlink to Claude variant tree
  for sub in roles scripts references; do
    src_sub="$src_claude_dir/$sub"
    if [ -d "$src_sub" ]; then
      ln -sfn "$src_sub" "$dst/$sub"
    fi
  done

  echo "installed: $dst"
done

echo
echo "Done. Restart your codex session — skills load on startup."
echo
echo "Optional dependencies for /clarify Phase 7.6 cross-model consensus:"
command -v claude >/dev/null 2>&1 && echo "  claude CLI: $(command -v claude)" \
                                  || echo "  claude CLI: MISSING — install with: npm install -g @anthropic-ai/claude-code"
command -v codex  >/dev/null 2>&1 && echo "  codex CLI:  $(command -v codex)" \
                                  || echo "  codex CLI:  MISSING — install with: npm install -g @openai/codex"
