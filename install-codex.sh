#!/usr/bin/env bash
# install-codex.sh — install Codex variants of iron-skills via symlinks
#
# Creates per-skill directories in ~/.codex/skills/ with:
#   - SKILL.md → symlink to <repo>/skills-codex/<name>/SKILL.md
#   - roles/scripts/references/ → symlinks to <repo>/skills/<name>/<subdir>/ (shared)
#
# Idempotent: safe to re-run after `git pull` to refresh symlinks.
set -euo pipefail

PLUGIN_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEST_ROOT="$HOME/.codex/skills"

SKILLS="cleanup blueprint extract-links svgl autoresearch goal-prep verify-done"
for skill in $SKILLS; do
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
  for sub in roles scripts references templates; do
    src_sub="$src_claude_dir/$sub"
    if [ -d "$src_sub" ]; then
      ln -sfn "$src_sub" "$dst/$sub"
    fi
  done

  echo "installed: $dst"
done

# Prune stale dests this plugin previously installed but no longer ships
# (e.g. a removed skill). Only touches dests whose SKILL.md symlink points
# back into THIS repo — other plugins' Codex skills are left untouched.
if [ -d "$DEST_ROOT" ]; then
  for d in "$DEST_ROOT"/*/; do
    name="$(basename "$d")"
    case " $SKILLS " in *" $name "*) continue ;; esac
    tgt="$(readlink "$d/SKILL.md" 2>/dev/null || true)"
    case "$tgt" in
      "$PLUGIN_ROOT"/*) echo "prune stale: $name"; rm -rf "$d" ;;
    esac
  done
fi

echo
echo "Done. Restart your codex session — skills load on startup."
echo
echo "Optional dependencies for /blueprint Phase 7.6 cross-model consensus:"
command -v claude >/dev/null 2>&1 && echo "  claude CLI: $(command -v claude)" \
                                  || echo "  claude CLI: MISSING — install with: npm install -g @anthropic-ai/claude-code"
command -v codex  >/dev/null 2>&1 && echo "  codex CLI:  $(command -v codex)" \
                                  || echo "  codex CLI:  MISSING — install with: npm install -g @openai/codex"
