---
name: ship
description: >
  Autonomous end-to-end orchestrator: hand it ONE freeform task and it picks the
  right skills, chains them, and drives the work to a verified finish — choosing
  the entry point itself (native plan mode / cleanup / extract-links / blueprint /
  goal-prep + /goal) and always ending with /verify-done. The autonomy level is
  chosen INTERACTIVELY at the start (guided / autopilot / checkpoint). Use ONLY
  when you want a well-scoped, RECOVERABLE task done start-to-finish with minimal
  hand-holding — not for exploratory or high-stakes work you want to review step by
  step (run the skills directly for that). Claude Code only. Triggers: "/ship",
  "ship it", "do the whole thing", "from start to finish", "handle it end to end",
  "autonomously", "сделай всё сам", "доведи до конца сам".
when_to_use: >
  The user hands a complete task and wants it driven to a verified finish without
  micromanaging each skill, AND a wrong step is recoverable (git history, tests,
  easy rollback). NOT when they want to inspect/approve each stage (use the skills
  directly), and NOT for irreversible or high-stakes changes. Claude Code only — it
  orchestrates /goal, the Skill tool, and the /verify-done Workflow.
---

# /ship — autonomous end-to-end orchestrator

One prompt in, verified result out. `/ship` reads your task, **picks where to
start and which skills to chain**, runs them at the autonomy level you choose, and
finishes with `/verify-done` so "done" means *actually* done — not "looks done".

> **⚠️ Experimental.** This is the newest skill and is **not yet battle-tested** —
> the rest of iron-skills is proven in daily use; `/ship` is not yet. Prefer
> `guided` or `checkpoint` autonomy, and review what it decides before trusting it
> unattended on anything that matters.

> **Claude Code only.** It drives the native `/goal` loop, invokes other skills via
> the Skill tool, and runs the `/verify-done` Workflow — Codex's orchestration
> primitives differ, so there's no Codex variant.

> **Letter = spirit.** The goal is *your task, finished and verified, with the
> fewest interruptions that still keep it correct*. Never trade a correct result
> for "didn't ask" — when a choice is irreversible or genuinely ambiguous, that's
> exactly what the upfront batch (or a stop) is for.

> **Orchestrator, not a new engine.** `/ship` composes existing skills + `/goal` +
> `/verify-done`. It adds routing + an autonomy policy, nothing more. Heavy work
> runs inside `/goal` and sub-agents so the main session stays light.

## When NOT to use

- **Irreversible / high-stakes** (prod data migration, payment cutover, anything
  you can't roll back) — run the gated path by hand (`/blueprint` with proofs).
- **Exploratory work** where you want to see and approve each step — call the
  skills directly.
- **Just watching a live service** — that's `/babysit`, not `/ship`.

## Phase 1 — Choose autonomy (INTERACTIVE — always first)

Ask the operator **once**, via `AskUserQuestion`, how hands-off to be:

| mode | behaviour |
|---|---|
| **guided** (recommended) | Ask ONE upfront batch of questions on the genuine forks (scope, target outcome, may-I-deploy), then run to the end **without interrupting**. Every auto-decision is logged and shown in the final report. |
| **autopilot** | **Zero questions.** Decide every fork yourself with sensible defaults; run straight through. Still STOP only for the hard guardrails below. Report at the end. |
| **checkpoint** | Pause for a quick approve at each phase boundary (notes cleaned → plan ready → before execute → before deploy). Most control, least hands-off. |

Hard guardrails apply in **every** mode (autonomy never overrides them):
- Never do something irreversible or security-sensitive unattended → STOP and ask.
- Never deploy a low-confidence or unverifiable change.
- `/verify-done` at the end is **non-skippable**.

## Phase 2 — Classify the task & route

From the prompt (and a quick repo glance), pick the **minimal** chain — don't run
skills the task doesn't need:

| the input is… | start at… |
|---|---|
| a raw, messy notes/chat dump with info to preserve | `/cleanup` → (then re-classify) |
| notes whose **links** carry the real content | `/extract-links` (or `--full`) first |
| a spec / feature description needing a real plan | `/blueprint` (structured, proof-driven) |
| a small, clear change | native **plan mode** (skip blueprint) |
| "optimize/〈metric〉, keep what helps" | `/autoresearch` |
| an already-written plan / `goal.md` | straight to execution |

Then **execute**: for anything non-trivial, build the charter with `/goal-prep` and
run the native **`/goal`** loop; for a small change, implement directly. Always end
at **`/verify-done`** (Phase 4).

Record the chosen chain + why in a short decisions log (shown at the end).

## Phase 3 — Run the chain at the chosen autonomy

Drive each step in order. When you invoke a chained skill, **pass the autonomy
directive** so it behaves consistently:
- **guided / autopilot:** the sub-skill must **not** stop to ask — resolve its own
  gates (blueprint's scope-cut audit, extract-links' link triage, etc.)
  using the upfront answers + sensible defaults, and **log each decision** instead
  of prompting. (In *guided* you already gathered the real forks up front; in
  *autopilot* you decide them.)
- **checkpoint:** let the natural phase boundaries surface a brief approve.
- On a step failure, **fix and continue** (delegate a bounded fix to a sub-agent so
  the loop stays light); escalate only if blocked or a guardrail trips.

Keep the main session lean: push heavy execution into `/goal` and one-shot work
into sub-agents — don't investigate inline across the whole task.

## Phase 4 — Verify (mandatory)

Run **`/verify-done`** against the original task as the intent (a `/blueprint`
plan, a `goal.md`, or the prompt itself if the task was small/unstructured).
- **DONE** → report success.
- **NOT-DONE** → in guided/autopilot, attempt the gaps once more (bounded), then
  re-verify; if still NOT-DONE, stop and report honestly. Never paper over a
  NOT-DONE with a confident "shipped".

## Phase 5 — Report

One compact summary:
- **Result:** DONE / NOT-DONE + one line.
- **Chain run:** the skills/steps in order.
- **Decisions made for you:** every fork auto-resolved (so nothing was silently
  chosen) — the value of "didn't interrupt you" is honesty about what it picked.
- **Gaps / NOT covered:** straight from `/verify-done`.
- **Follow-ups:** anything needing a human.

## How to do it wrong vs right

❌ Skip `/verify-done` because the steps "all passed" → ships unverified work.
✅ Always end on `/verify-done`; "done" requires it.

❌ Autopilot silently narrows scope and builds the wrong thing.
✅ Decide, **log it**, and surface every scope call in the final report.

❌ Run the full cleanup→extract→blueprint chain for a one-line fix.
✅ Route to the minimal chain — small change → plan mode → implement → verify.

❌ Deploy an irreversible change because the mode was "autopilot".
✅ Guardrails beat autonomy — irreversible/unsafe always stops and asks.

## Self-check before reporting

- Did I pick the **minimal** chain, not the whole pipeline by reflex?
- Did `/verify-done` actually run, and is the verdict honest (no false DONE)?
- Is every auto-resolved fork listed in the report (nothing silently decided)?
- Did I respect the hard guardrails regardless of the autonomy mode?
- Did heavy work stay in `/goal` / sub-agents, not bloat the main session?
