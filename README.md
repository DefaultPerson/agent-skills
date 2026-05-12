# agent-skills

Three focused skills for the pre-implementation half of an AI coding workflow: pull content out of links, losslessly reorganize messy notes, decompose specs into atomic tasks with verifiable acceptance criteria. Pairs with [mattpocock/skills](https://github.com/mattpocock/skills) for the implementation side.

## The Flow

```
 ┌────────┐  extract  ┌────────────┐  cleanup  ┌──────────┐  clarify  ┌─────────┐    →   mattpocock:tdd
 │ notes  ├──────────>│ notes with ├──────────>│  clean   ├──────────>│ atomic  │    →   Claude Code goal feature
 │  with  │           │  offline   │           │ markdown │           │ tasks + │    →   manual implementation
 │ links  │           │  content   │           │ document │           │ AC with │    →   claude -p for AC verify
 └────────┘           └────────────┘           └──────────┘           │  proof  │
                                                                     │commands │
                                                                     └─────────┘
                                                                          ▲
                                                                          │
                                                              Codex+Claude consensus
                                                                (Phase 7.6 in clarify)
```

## Skills

- **`/extract`** — pull content out of every URL in a notes file (YouTube subtitles via yt-dlp, public Telegram via embed-page scrape, HTML via pandoc/curl). Replaces each URL with a local pointer, preserves originals, gitignores extracted content.
- **`/cleanup`** — losslessly reorganize a messy notes/plan/chat dump into a clean sectioned markdown file. Three-level gap detection (deterministic URL check + per-section semantic agents + fuzzy coverage net) proves nothing was lost. Multi-file input → multi-file output (per-source pipelines, not merged).
- **`/clarify`** — turn a clean spec into an implementation-ready document: atomic tasks with Given/When/Then acceptance criteria, shell-runnable proof commands, contracts (FR-NNN with MUST/SHOULD/MAY), edge cases, risks. Cross-model consensus loop with Codex (optional) catches issues single-model self-review misses.

Each skill follows the same template — `description` states triggers and tradeoffs (not algorithm), honest weakness section up front, ❌/✅ contrast pairs, "letter = spirit" canon, Cialdini-framed rules, senior-review self-check before output. Conventions are in `references/skill-template.md` and `references/principles.md`.

## Example

```bash
# 1. Pull content out of every URL in the note (YouTube transcripts,
#    Telegram posts, articles). Original note keeps the URLs; pointers
#    to local copies appear next to each one.
/extract research-notes.md

# 2. Reorganize the chaos into a clean sectioned doc with proven
#    coverage (nothing dropped, every URL preserved or explicitly errored).
/cleanup research-notes.md

# 3. Decompose into atomic tasks with verifiable AC. Phase 7.6 invokes
#    codex:adversarial-review (from openai/codex-plugin-cc, if installed)
#    against the uncommitted spec edit and iterates up to 3 rounds until
#    consensus.
/clarify research-notes.md

# 4. Hand the resulting spec to whichever builder you prefer:
#    - mattpocock:tdd (test-first implementation, see Companion below)
#    - Claude Code goal feature (measurable success criteria)
#    - manual coding
#    - claude -p in fresh context to verify AC after implementation
```

## Companion plugin: mattpocock/skills

`agent-skills` deliberately doesn't ship implementation/verification skills — those exist in [mattpocock/skills](https://github.com/mattpocock/skills) and pair naturally with our spec output.

```bash
/plugin install mattpocock/skills
```

Recommended pairings:

- **`mattpocock:tdd`** — test-driven implementation using AC from `/clarify` output as the test surface.
- **`mattpocock:grill-me`** — interview-style elicitation when `/clarify` Phase 2 questions aren't enough.
- **`mattpocock:to-prd`** — alternative spec format when you want product-manager-style PRD instead of test-first AC.
- **`mattpocock:caveman`** — token-saver for long sessions.
- **`mattpocock:git-guardrails-claude-code`** — git operation safety rails.

## Installation

```bash
/plugin marketplace add DefaultPerson/agent-skills
/plugin install agent-skills@agent-skills
```

Optional (for `/clarify` Phase 7.6 cross-model consensus): install the [Codex CLI](https://github.com/openai/codex) and the [Codex plugin for Claude Code](https://github.com/openai/codex-plugin-cc):

```bash
/plugin marketplace add openai/codex-plugin-cc
/plugin install codex@openai-codex
```

The plugin provides the `codex:adversarial-review` skill that clarify drives during its consensus loop. Without the plugin (or when the spec isn't in a git repo, since adversarial-review operates on the working tree), `/clarify` falls back to single-model internal validation with a warning.

## Prerequisites

- **Required:** Git, `bash`, `jq`, `python3`.
- **`/extract` deps** (probed at runtime, install prompt if missing): `yt-dlp` (YouTube subtitles), `pandoc` (HTML — optional, falls back to crude curl). Telegram works with just `curl`.
- **`/clarify` Phase 7.6 optional:** [Codex CLI](https://github.com/openai/codex) + [codex-plugin-cc](https://github.com/openai/codex-plugin-cc) (provides `codex:adversarial-review`). Spec must live in a git repo for working-tree review; otherwise the loop falls back to internal validation.

## v2.0.0 breaking changes

If migrating from v1.x: this release **removes** the orchestration skills.

- **Skills removed:** `/execute`, `/verify`, `/autoresearch`, `/ralph-loop`, `/cancel-ralph`. Use `mattpocock:tdd` for implementation; use `claude -p` in fresh context for independent AC verification on a clarify-produced spec. `autoresearch` moved to a separate repository (see TODO when published).
- **`/clarify` slimmed:** spec generation core preserved (AC format, proof commands, contracts), but execute-orchestration parts gone (`[P]` parallel markers, Stages, Execution Order section, dependency graphs for parallel workers, worker prompt templates). Output is now suitable for human/`tdd`/goal-feature consumption, NOT autonomous orchestration.
- **`skills-codex/` and `.codex-plugin/` removed:** the remaining skills (`cleanup`, `clarify`, `extract`) are tool-agnostic at the Bash level. If you need a Codex CLI variant in the future, it'll be regenerated via a sync script.
- **Hooks removed:** the `ralph-stop.py` Stop hook is gone with `ralph-loop`. Orphaned `.claude/ralph-loop.local.md` state files from prior versions are safe to delete: `rm -f .claude/ralph-loop.local.md`.

If you were relying on autonomous spec→implementation execution, switch to `mattpocock:tdd` or wait for a v2.x add-on if community demand returns the feature.

## License

MIT
