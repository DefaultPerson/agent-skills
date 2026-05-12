# agent-skills

Three focused skills for the pre-implementation half of an AI coding workflow: losslessly reorganize messy notes, pull content out of links, decompose specs into atomic tasks with verifiable acceptance criteria.

## The Flow

```
 ┌────────┐  cleanup  ┌──────────┐  clarify  ┌─────────┐  extract  ┌────────────┐    →   mattpocock:tdd
 │ notes  ├──────────>│  clean   ├──────────>│ atomic  ├──────────>│  tasks +   │    →   Claude Code goal feature
 │  with  │           │ markdown │           │ tasks + │           │  offline   │    →   manual implementation
 │ links  │           │ document │           │ AC with │           │   link     │    →   claude -p for AC verify
 └────────┘           └──────────┘           │  proof  │           │  content   │
                                             │commands │           └────────────┘
                                             └─────────┘
                                                  ▲
                                                  │
                                      Codex+Claude consensus
                                        (Phase 7.6 in clarify)
```

## Skills

- **`/cleanup`** — losslessly reorganize a messy notes/plan/chat dump into a clean sectioned markdown file. Three-level gap detection (deterministic URL check + per-section semantic agents + fuzzy coverage net) proves nothing was lost. Multi-file input → multi-file output (per-source pipelines, not merged).
- **`/extract`** — pull content out of every URL in a notes file (YouTube subtitles via yt-dlp, public Telegram via embed-page scrape, HTML via pandoc/curl). Replaces each URL with a local pointer, preserves originals, gitignores extracted content.
- **`/clarify`** — turn a clean spec into an implementation-ready document: atomic tasks with Given/When/Then acceptance criteria, shell-runnable proof commands, contracts (FR-NNN with MUST/SHOULD/MAY), edge cases, risks. Cross-model consensus loop with Codex (optional) catches issues single-model self-review misses.

Each skill follows the same template — `description` states triggers and tradeoffs (not algorithm), honest weakness section up front, ❌/✅ contrast pairs, "letter = spirit" canon, Cialdini-framed rules, senior-review self-check before output.

## Example

```bash
# 1. Reorganize the chaos into a clean sectioned doc with proven coverage
#    (nothing dropped, every URL preserved).
/cleanup research-notes.md

# 2. Pull content out of every URL in the cleaned doc (YouTube transcripts,
#    Telegram posts, articles). Original URLs stay; pointers to local copies
#    appear next to each one.
/extract research-notes.md

# 3. Decompose into atomic tasks with verifiable AC. Phase 7.6 invokes
#    codex:adversarial-review (from openai/codex-plugin-cc, if installed)
#    against the uncommitted spec edit and iterates up to 3 rounds until
#    consensus.
/clarify research-notes.md
```

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

Release history: see [CHANGELOG.md](CHANGELOG.md).

## License

MIT
