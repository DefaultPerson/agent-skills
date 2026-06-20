# iron-skills

Nine skills for an AI coding workflow: losslessly reorganize messy notes, pull content out of links, turn specs into a readable plan of atomic tasks with shell-verifiable proofs, debug hard bugs with a disciplined feedback loop, surface architectural deepening opportunities, fetch SVG brand logos from svgl.app, compile a goal charter for native `/goal`, run an autonomous keep-or-revert experiment loop, and gate final acceptance against the original intent.

> Formerly `agent-skills` — renamed to avoid the install name clash. The GitHub repo and plugin/marketplace are now `iron-skills` (the local working dir may still read `agent-workflow`; harmless).

## The Flow

```
 ┌────────┐  cleanup  ┌──────────┐ blueprint ┌─────────┐  extract  ┌────────────┐    →   /to-prd → issue tracker
 │ notes  ├──────────>│  clean   ├──────────>│ atomic  ├──────────>│  tasks +   │    →   TDD (red/green/refactor)
 │  with  │           │ markdown │           │ tasks + │           │  offline   │    →   Claude Code goal feature
 │ links  │           │ document │           │Done-when│           │   link     │    →   manual implementation
 └────────┘           └──────────┘           │ proofs  │           │  content   │    →   claude -p for proof verify
                                             │ +risks  │           └────────────┘
                                             │+ADRs    │
                                             └─────────┘
                                                  ▲
                                                  │
                                Codex + Claude (+OpenRouter) consensus
                                        (Phase 7.6 in blueprint)
```

The `/to-prd` seam (if installed separately) wraps the enriched spec as a PRD and publishes to the configured issue tracker — opt-in, never auto-invoked.

## Skills

- **`/cleanup`** — losslessly reorganize a messy notes/plan/chat dump into a clean sectioned markdown file. Three-level gap detection (deterministic URL check + per-section semantic agents + fuzzy coverage net) proves nothing was lost. Multi-file input → multi-file output (per-source pipelines, not merged).
- **`/extract`** — pull content out of every URL in a notes file (YouTube subtitles via yt-dlp, public Telegram via embed-page scrape, HTML via pandoc/curl). Replaces each URL with a local pointer, preserves originals, gitignores extracted content. **Light mode** (`--light`, or chosen interactively at the start) skips full extraction and instead writes a one-line gist of each link inline next to the URL — fast triage for URL-heavy notes, no `extracted/` tree.
- **`/blueprint`** (was `/clarify`) — turn a clean spec into a readable, implementation-ready **plan**: atomic vertical-slice tasks each with a `Done when:` shell proof, plain-language requirements (`[must]`/`[nice]`/`[later]` — no RFC-2119/FR-NNN ceremony), inline edge cases, ranked **assumptions & open questions**, and risks. Reads existing `docs/adr/*.md` and offers new ADRs for hard-to-reverse decisions (cap 3 per run, all 3 criteria). Phase 5 Scope-cut audit records firm rejections to `.out-of-scope/<concept>.md`. Phase 7.6 cross-model consensus: Codex finds + Claude triages, plus an **optional diverse third reviewer via OpenRouter** (`OPENROUTER_API_KEY` → `z-ai/glm-5.2`, fallback `moonshotai/kimi-k2.6`). `clarify` / `уточни спеку` still trigger it.

Two orthogonal skills (independent of the main flow):

- **`/diagnose`** — disciplined debug loop for hard bugs and performance regressions. Phase 1 is the heart: build a fast deterministic feedback loop (10 ways listed, from failing test to bisection harness to HITL bash). Then reproduce → 3-5 ranked falsifiable hypotheses → instrument (with `[DEBUG-xxxx]` tags for one-grep cleanup) → fix with regression test at the correct seam → post-mortem. If no correct seam exists for the regression test, that itself is the finding — surfaces a `/deepen` candidate.
- **`/deepen`** — find shallow modules (interface nearly as complex as implementation) and propose deepening refactors. Uses Ousterhout vocabulary (Module / Interface / Seam / Adapter / Depth / Leverage / Locality), the deletion test, and the "one adapter = hypothetical seam / two = real" rule. Optional "Design It Twice" Phase 3 spawns 3 parallel sub-agents with different design constraints (minimise interface / maximise flexibility / optimise common caller), then recommends one or a hybrid.

A standalone utility (independent of the spec flow):

- **`/svgl`** — fetch SVG brand/tech logos from the [svgl.app](https://svgl.app) API into your project, by name or category. Downloads the actual `.svg` files (light/dark theme-aware, optional wordmarks) into `./svgl/`, or `--json` for metadata/URLs only. Interactive disambiguation when a query matches several logos; `--all` to skip it.

Goal-execution skills (absorbed from `agent-goal-stack`, MIT):

- **`/goal-prep`** — compile a charter for Claude Code's native `/goal`: an Intake Compiler (11 fields), a diagnostic ladder, goal classification, per-kind anti-patterns, and a copy-pasteable `/goal` command pointing at an on-disk charter. When handed a `/blueprint` plan it auto-derives the completion criterion ("every `Done when:` proof passes") and seeds a per-stage review cadence into the charter. Strictly non-execution.
- **`/autoresearch`** — autonomous keep-or-revert experiment loop: iteratively optimise any metric via single atomic changes, committing before verification and reverting failures. ScheduleWakeup-paced (short iterations) or CronCreate-paced (long). Per-iteration work is delegated to the bounded `iron-skills:autoresearch-worker` subagent so the loop's context stays constant.

The acceptance gate (read-only, end of the loop):

- **`/accept [--deep] [--block-on-quality]`** — plan-aware final acceptance: given a `/blueprint` plan (or `goal.md`) + the built code, adversarially verify the result against the ORIGINAL intent. **Tier 1** re-runs every `Done when:` proof; **Tier 2** generates + runs independent user-scenarios the plan may have missed (grounded in the original intent — never invents requirements); **Tier 3** is an advisory maintainability pass (the substance of the former thermo-nuclear review, PR-ceremony stripped). Heavy verification runs in a `Workflow`'s sub-agents — the main session gets only a `DONE`/`NOT-DONE` verdict + a gap list. A **gate, not a fixer** (`UNKNOWN` ≠ pass; reports what it couldn't cover).

A slash command (Claude Code only — user-invoked, not auto-triggered):

- **`/babysit [stop\|status\|resume]`** — autonomous **watch · fix · deploy · re-check** loop for a running service. Runs on the native `/loop` cadence ("every N minutes"); each tick reads **only new logs** (a `log_cursor` keeps it from re-firing on boot-time noise), classifies healthy-or-not against a concrete trouble-definition (health check / error patterns / rate / crash loop), and — if not healthy — hands a **bounded fix to a sub-agent** (the investigation stays in the sub-agent's context; only a structured verdict returns, so the babysitter stays light over hours of ticking), then deploys (coolify MCP or a `deploy_cmd`) and verifies against baseline. Loops until you `stop` it. Three autonomy modes (**full-auto** default · fix-ask-deploy · observe). Guardrails: two strikes on the same error signature → stop retrying; deploy-storm and blind-tick caps; never auto-deploys a low-confidence or irreversible/security-sensitive change. **Escalation** is the only noisy path — on a genuine stuck/unsafe condition it fires `PushNotification` + a capped (20 min) background alarm that beeps and `notify-send`s **every 30s until you `touch .babysit/alert.stop`**. State lives in `.babysit/` (gitignored). Claude Code only (needs `/loop`, the `Agent` tool, and your deploy MCP). ⚠️ Point it only at environments where a bad deploy is recoverable.

Most skills follow the same house template — `description` states triggers and tradeoffs (not algorithm), honest weakness section up front, ❌/✅ contrast pairs, "letter = spirit" canon, Cialdini-framed rules, senior-review self-check before output. (`/goal-prep` and `/autoresearch` are absorbed from `agent-goal-stack` and keep their own structure; `/accept` drives a `Workflow`; the former thermo-nuclear review now lives as `/accept`'s advisory Tier-3 quality pass.)

## Example

```bash
# 1. Reorganize the chaos into a clean sectioned doc with proven coverage
#    (nothing dropped, every URL preserved).
/cleanup research-notes.md

# 2. Pull content out of every URL in the cleaned doc (YouTube transcripts,
#    Telegram posts, articles). Original URLs stay; pointers to local copies
#    appear next to each one.
/extract research-notes.md

# 3. Turn it into a readable plan: atomic tasks with `Done when:` proofs,
#    plain-language requirements, and ranked assumptions. Phase 7.6 runs a
#    cross-model review (Codex + optional OpenRouter third model via
#    OPENROUTER_API_KEY) until consensus; Phase 5 offers ADRs.
/blueprint research-notes.md

# 4. (Optional) If `/to-prd` is installed, publish the enriched spec to
#    your issue tracker (e.g. Linear, GitHub Issues) wrapped as a PRD.
/to-prd
```

## Installation

```bash
/plugin marketplace add DefaultPerson/iron-skills
/plugin install iron-skills@iron-skills
```

**Local install (no marketplace).** Claude Code auto-discovers skills in `~/.claude/skills/` — symlink each skill directory (its `roles/`, `references/`, `scripts/` travel with it):

```bash
PLUGIN_ROOT="${HOME}/.local/share/iron-skills"
git clone https://github.com/DefaultPerson/iron-skills.git "$PLUGIN_ROOT" 2>/dev/null \
  || git -C "$PLUGIN_ROOT" pull --ff-only
for s in cleanup blueprint extract diagnose deepen svgl goal-prep autoresearch accept; do
  ln -sfn "$PLUGIN_ROOT/skills/$s" "$HOME/.claude/skills/$s"
done
# Restart your session — skills load on startup.
```

Optional (for `/blueprint` Phase 7.6 cross-model consensus): install the [Codex CLI](https://github.com/openai/codex):

```bash
npm install -g @openai/codex
codex login   # one-time auth
```

`/blueprint` drives `codex review --uncommitted` directly — no companion Claude Code plugin needed. Without the CLI (or when the spec isn't in a git repo, since `--uncommitted` operates on the working tree), `/blueprint` falls back to single-model internal validation with a warning.

## Install in Codex CLI

Codex CLI's native `codex plugin install` is not yet operational (the `plugins` feature flag is `stable` but disabled by default). Until it ships, use the symlink installer below.

**For an LLM agent: copy the entire block below into your Codex session — the agent will install and verify.**

```bash
# 1. Clone (or update) the plugin repo locally.
PLUGIN_ROOT="${HOME}/.local/share/iron-skills"
git clone https://github.com/DefaultPerson/iron-skills.git "$PLUGIN_ROOT" 2>/dev/null \
  || git -C "$PLUGIN_ROOT" pull --ff-only

# 2. Run the Codex installer (creates per-skill dirs in ~/.codex/skills/
#    with symlinks to Codex-variant SKILL.md + shared roles/scripts/references).
bash "$PLUGIN_ROOT/install-codex.sh"

# 3. Verify each skill has SKILL.md plus shared subdirs.
for s in cleanup blueprint extract diagnose deepen svgl goal-prep autoresearch accept; do
  echo "--- $s ---"; ls -la "$HOME/.codex/skills/$s/"
done

# 4. For /blueprint Phase 7.6 cross-model consensus, ensure both CLIs are on PATH.
#    Codex variant uses `claude -p` as the cross-model reviewer (Claude is the
#    "other model" since host is Codex). The Claude variant uses `codex review`.
command -v codex  >/dev/null || echo "MISSING codex:  npm install -g @openai/codex"
command -v claude >/dev/null || echo "MISSING claude: npm install -g @anthropic-ai/claude-code"

# 5. Restart your codex session — skills load on startup.
echo "Done. Nine skills installed: /cleanup, /blueprint, /extract, /diagnose, /deepen, /svgl, /goal-prep, /autoresearch, /accept."
```

When Codex ships native `codex plugin install`, this section will be replaced with a one-liner. Track [openai/codex](https://github.com/openai/codex) for status.

## Prerequisites

- **Required:** Git, `bash`, `jq`, `python3`.
- **`/svgl` deps:** `curl` + `jq` (both already required) — no extra install.
- **`/extract` deps** (probed at runtime, install prompt if missing): `yt-dlp` (YouTube subtitles), `pandoc` (HTML — optional, falls back to crude curl). Telegram works with just `curl`. **Light mode** needs only `curl` (+ `yt-dlp` for YouTube metadata); no `pandoc`.
- **`/blueprint` Phase 7.6 optional:**
  - In **Claude Code**: [Codex CLI](https://github.com/openai/codex) (`npm install -g @openai/codex`) — Claude variant uses `codex review --uncommitted` as the cross-model reviewer.
  - In **Codex CLI**: [Claude Code CLI](https://docs.claude.com/en/docs/claude-code) (`npm install -g @anthropic-ai/claude-code`) — Codex variant uses `claude -p` as the cross-model reviewer.
  - Spec must live in a git repo for working-tree review; otherwise the loop falls back to internal `spec-validator` (single-model, weaker).

Release history: see [CHANGELOG.md](CHANGELOG.md).

## License

MIT
