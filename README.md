# iron-skills

Battle-tested skills for AI coding agents — Claude Code and Codex CLI. Only the ones I actually use, kept lean.

> Formerly `agent-skills` (renamed to dodge the reserved install name). Repo, plugin, and marketplace are all `iron-skills`.

## Flow

Full — messy input to shipped + verified:

```
cleanup → extract-links → blueprint → goal-prep → /goal → verify-done
```

Small task — skip the heavy prep:

```
native plan mode → implement → verify-done
```

The steps chain, but each works on its own — run one or the whole line. `verify-done` takes a `/blueprint` plan, a `goal.md`, or just a plan-mode/inline plan.

## Skills

- **`/cleanup`** — reorganize a messy notes/chat dump into clean sectioned markdown, losslessly. Three-level gap detection proves nothing was dropped.
- **`/extract-links`** — annotate every URL in a note with its content. **Default light:** a one-line gist inline next to each URL. `--full` pulls full content (YouTube subtitles, Telegram posts, articles) into a local `extracted/` tree.
- **`/blueprint`** — turn a spec into a readable plan of atomic tasks, each with a `Done when:` shell proof. Plain-language requirements, ranked assumptions, optional ADRs, and an optional cross-model review (Codex + Claude, plus an OpenRouter third reviewer).
- **`/goal-prep`** — compile a charter for Claude Code's native `/goal`: completion criteria, anti-patterns, and a ready-to-paste `/goal` command. Writes the charter; never executes.
- **`/autoresearch`** — autonomous keep-or-revert loop: optimize a metric with single atomic changes, committing before verifying and reverting failures. Per-iteration work runs in a bounded sub-agent so context stays flat.
- **`/verify-done`** — final acceptance gate (was `/accept`): re-runs every `Done when:` proof, generates independent scenarios the plan missed, then an advisory quality pass. Read-only — returns `DONE`/`NOT-DONE` + a gap list; heavy work runs in a Workflow's sub-agents.
- **`/svgl`** — fetch SVG brand/tech logos from [svgl.app](https://svgl.app) into your project, by name or category.

Plus **`/babysit`** (Claude Code only) — autonomous watch · fix · deploy · re-check loop for a running service; escalates with sound + desktop notification only when genuinely stuck.

## Install

Native plugin install — paste the line for your runtime, then restart the session:

```bash
# Claude Code
claude plugin marketplace add DefaultPerson/iron-skills && claude plugin install iron-skills@iron-skills

# Codex CLI
codex plugin marketplace add https://github.com/DefaultPerson/iron-skills && codex plugin add iron-skills@iron-skills
```

No-marketplace fallback: `git clone` the repo, then symlink `skills/*` into `~/.claude/skills/` (Claude Code) or run `bash install-codex.sh` (Codex).

## Prerequisites

`git`, `bash`, `jq`, `python3`. `/extract-links` probes for `yt-dlp` (YouTube) and `pandoc` (HTML, optional) at runtime. `/blueprint`'s cross-model review is optional — it calls the *other* CLI (Codex when running in Claude Code, Claude when running in Codex) plus an optional `OPENROUTER_API_KEY` third reviewer; without them it falls back to single-model validation.

Release history: see [CHANGELOG.md](CHANGELOG.md).
