# Changelog

## 0.8.0 — 2026-06-20

`/blueprint` output is easier to navigate. Everything that needs a human now lives
in **one** place — a `## Needs your attention` block at the top of the tasks file
(blocking `❓ NEEDS YOU` forks, each wired `→ blocks: TASK-n`, plus the HITL tasks);
the reference keeps only ranked **non-blocking** `## Assumptions`, so nothing is
duplicated across the two files. A new **`## Task index`** checklist gives an
at-a-glance, trackable map of every task (and is where blocked-on / HITL flags now
live, instead of scattered per-task `Status:` lines). A **foundations-first** rule
stops plans from "starting in mid-air": the first task leaves the project
runnable/green (greenfield skeleton + smoke test, or a brownfield baseline proof),
the test harness lives there and is reused — never buried in a later task — and each
area appears exactly once. Also fixes a latent bug: `verify-spec.py` didn't recognise
the v0.7.0 directory form (`<spec-stem>/tasks.md` + `reference.md`) and falsely failed
it; it now resolves the directory form and adds light checks for the new layout.

## 0.7.0 — 2026-06-20

De-formalized `/blueprint`. Dropped the ADR machinery entirely (no more
`docs/adr/NNNN-*.md` files, detection, or `adr-format.md`) — hard-to-reverse
decisions are now a one-line note in the plan's `## Risks`. Dropped the
`.out-of-scope/` file tree (and `out-of-scope-format.md`) — confirmed scope cuts
are recorded inline under `## Non-goals`. New output rule: when the plan is more
than one file it goes in a **flat directory `<spec-stem>/`** (`tasks.md` +
`reference.md`), no nested subdirs; a trivial spec stays a single `<spec>.md`.
`/verify-done` and `/goal-prep` updated to resolve the directory form. LICENSE
mattpocock attribution corrected (deepen was removed in 0.3.0).

## 0.6.0 — 2026-06-20

New `/ship` skill — an autonomous end-to-end orchestrator. Hand it one freeform task
and it picks the entry point, chains the right skills, runs via `/goal`, and finishes
with `/verify-done`. Autonomy is chosen interactively (guided / autopilot / checkpoint);
hard guardrails (nothing irreversible/unsafe unattended, `/verify-done` non-skippable,
every auto-decision logged) apply in every mode. Claude-only (orchestrates `/goal` +
the Skill tool + the verify-done Workflow).

## 0.5.0 — 2026-06-20

`/verify-done` is now plan-source-agnostic: besides a `/blueprint` plan or `goal.md`,
it accepts a plain native plan-mode / inline plan — the plan prose becomes the intent,
and proofs are derived (or fall back to build/test, else the verdict leans on Tier 2).
Enables a lightweight small-task flow — `native plan mode → implement → verify-done` —
added to the README beside the full flow.

## 0.4.0 — 2026-06-20

`/babysit` moved from a command to a **Claude-only skill** — Claude can now invoke
it itself (still `/babysit`-typeable), with a tightly-scoped description so it only
fires on explicit watch-fix-deploy-loop intent. Its deploy/log adapter is now
platform-agnostic: any `log_cmd` / `deploy_cmd` (coolify or any platform MCP is one
option, nothing hard-coded). No Codex variant (Codex lacks `/loop`); the validator
gained a Claude-only allowlist.

## 0.3.0 — 2026-06-20

Removed `/diagnose` and `/deepen` (outside the core flow, unused). Renamed `/accept`
→ `/verify-done` (clearer intent) and `/extract` → `/extract-links`. `/extract-links`
now defaults to light (one-line inline summaries); pass `--full` for offline content
extraction. README trimmed.

## 0.2.0 — 2026-06-20

Native Codex CLI plugin packaging — `codex plugin marketplace add` + `codex plugin add`
install iron-skills directly (each Codex skill is self-contained, built from the Claude
tree by `ci/build-codex.sh`). README install simplified to one block per runtime.

## 0.1.0 — 2026-06-19

First release under the iron-skills name. Nine skills for AI coding agents
across Claude Code and Codex CLI — cleanup, extract, blueprint, diagnose,
deepen, svgl, goal-prep, autoresearch, accept — plus the `/babysit` command,
the `iron-skills:autoresearch-worker` agent, and a CI validator.
