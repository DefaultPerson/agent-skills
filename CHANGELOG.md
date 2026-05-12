# Changelog

## 2.0.0

Breaking release — removes the orchestration skills, slims `/clarify`, adds `/extract`, fixes `/cleanup` multi-file handling.

### Removed

- **Skills:** `/execute`, `/verify`, `/autoresearch`, `/ralph-loop`, `/cancel-ralph`. For independent AC verification on a clarify-produced spec, use `claude -p` in a fresh context. `autoresearch` moved to a separate repository.
- **`skills-codex/`** and **`.codex-plugin/`** — the remaining skills (`cleanup`, `clarify`, `extract`) are tool-agnostic at the Bash level; no parallel manifest needed.
- **Hooks:** `ralph-stop.py` Stop hook gone with `ralph-loop`. Orphaned `.claude/ralph-loop.local.md` state files from prior versions are safe to delete:
  ```bash
  rm -f .claude/ralph-loop.local.md
  ```

### Changed

- **`/clarify` slimmed:** spec-generation core preserved (AC format, proof commands, contracts, edge cases, risks), but execute-orchestration parts removed — `[P]` parallel markers, Stages, the Execution Order section, dependency graphs, and worker prompt templates. Output is now suitable for human consumption or the Claude Code goal feature, NOT autonomous orchestration.
- **`/clarify` Phase 7.6 added:** cross-model consensus loop driving `codex:adversarial-review` from `openai/codex-plugin-cc` against the uncommitted spec edit, iterating up to 3 rounds (configurable via `--consensus-rounds N`, `0` disables) until both Codex and Claude agree. Falls back to single-model internal validation if the plugin isn't installed or the spec is outside a git repo.
- **`/cleanup` multi-file fix:** N input files → N independent pipelines end-to-end, not one merged file. Per-source backup, per-source gap detection (4a/4b/4c), per-source final verification. The `<50-line skip` for Phase 4b now only triggers in single-file mode. `--merge` flag preserves legacy single-output behavior.
- **Template overhaul:** every SKILL.md now follows a uniform shape — `Use when ...` description format, honest weakness section, ❌/✅ contrast pairs, "letter = spirit" canon, Cialdini-framed rules, senior-review self-check before output. Role prompts moved out of SKILL.md bodies into per-skill `roles/*.md`.

### Added

- **`/extract`** — new skill. Pulls content out of every URL in a notes file:
  - YouTube via `yt-dlp` (subtitles, manual or auto-generated, en+ru)
  - Public Telegram via embed-page scrape (no auth required)
  - Generic HTML via `pandoc` (falls back to crude curl strip if pandoc missing)
  - Interactive prompt for "other" URLs (custom command escape hatch)
  - Annotates each successful URL in the source note with a local pointer; preserves originals; gitignores the `*.extracted/` output.
