# Changelog

## 2.0.3

### Fixed

- **`/clarify` Phase 7.6 invocation of Codex adversarial review.** Previous versions called `Skill(skill="codex:adversarial-review", ...)`, which the Skill tool silently refuses because the slash command has `disable-model-invocation: true` in its frontmatter — it's a user-only command. Symptom: clarify reported "codex-plugin-cc not installed" and fell back to single-model validation, even when the plugin was installed and `/codex:adversarial-review` worked perfectly when the user typed it manually. Fix: detect the plugin by filesystem probe (`ls ~/.claude/plugins/cache/openai-codex/codex/*/scripts/codex-companion.mjs`) and invoke the underlying node script directly via Bash (`node <path> adversarial-review --wait --scope working-tree "<focus_brief>"`). The script itself has no model-invocation restriction. SKILL.md weakness/failure-mode sections updated to explicitly call out this trap so future maintainers don't reintroduce it.

## 2.0.2

### Changed

- **`/clarify` step 10 — backup disposition.** After approval, the skill now asks via AskUserQuestion whether to delete `<spec>.bak`. Default = delete (rollback is still possible via `git checkout HEAD -- <spec>` against the `pre-clarify: <name>` snapshot from step 6). Escape hatch = keep, for diff-compare or extra safety. Prevents `.bak` files from silently accumulating in the workspace and polluting `git status`.

## 2.0.1

Hardening pass on the v2.0 trio. No breaking API; behaviour changes only inside `/extract` output layout and `/clarify` consensus-loop hygiene.

### Changed

- **`/extract` output is now one shared `extracted/` parent per directory.** Previously each note produced its own sibling `<note>.extracted/`, so processing N notes in a directory left N folders cluttering it. New layout: `<note-dir>/extracted/<note-basename>/<slug>/...` — N notes consolidate under one `extracted/` umbrella. `.gitignore` pattern simplified from `*.extracted/` to `extracted/`.
- **`/extract` URL triage step (new Phase 2).** Heuristic-classifies bare hosts, `docs.*` subdomains and path roots, GitHub repo roots, package-registry landings, and anchor-only URLs as `reference`. A single AskUserQuestion surfaces them with three options (skip all / extract all / pick which); default is skip. Stops noise URLs (API docs, citation links, tool homepages) from polluting the output. Final report enumerates four states: `extracted` / `error` / `skipped(reference)` / `skipped(user)`.
- **`/clarify` Phase 7.6 no longer writes `<spec>.critique.<N>.json` or `<spec>.critique.<N>.rejected.md`.** Codex findings and round-by-round breakdowns live in memory during the loop and are printed to stdout at round boundaries. On consensus failure or oscillation, the full round log is dumped to stdout before user escalation. The two `.bak` and `<spec>` files are the only on-disk artifacts now.
- **`/clarify` clarified that Phase 7.6 depends on `codex-plugin-cc` (the Claude Code skill), not the bare `codex` CLI.** The CLI is a transitive dependency of the plugin, not the entry point this skill uses. Fallback to `roles/spec-validator.md` triggers when the plugin is missing (not when the CLI is).
- **`/clarify` Connections section no longer recommends downstream skills.** Removed the `mattpocock:tdd / Claude Code goal feature / manual implementation / claude -p verify` bullet list; downstream choices belong to the user, not the skill. The "Does not call other skills automatically" sentence remains.

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
  - **URL triage** — heuristic-classifies bare hosts, `docs.*`, GitHub repo roots, package-registry landings, and anchor-only URLs as `reference`; surfaces them in a single AskUserQuestion before extraction begins. Default = skip all references; escape hatches: extract all, or pick which. Stops noise URLs (API docs, citation links, tool homepages) from polluting `extracted/`.
  - Annotates each successful URL in the source note with a local pointer; preserves originals; gitignores the `extracted/` output (one shared parent per directory, per-note subfolder inside — multi-file runs in the same dir consolidate, not proliferate).
