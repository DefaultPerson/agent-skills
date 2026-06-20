---
name: verify-done
description: >
  Plan-aware final ACCEPTANCE gate: given any plan (a /blueprint plan, a
  goal.md charter, OR a plain plan-mode / inline plan) + the built code,
  adversarially verify the result actually works against the ORIGINAL
  intent — re-run every `Done when:` proof (Tier 1),
  generate + run independent scenarios the plan may have missed (Tier 2),
  then an advisory maintainability pass (Tier 3). Read-only GATE, not a fixer —
  emits DONE / NOT-DONE + a gap list. Triggers: "/verify-done", "verify done",
  "accept", "acceptance gate", "is this actually done", "приёмка".
when_to_use: >
  Execution of a plan/goal is finished (or at a milestone) and you want one
  honest verdict on whether the END RESULT is really done. NOT for a quick
  single-change check or diff-level bug hunting. Run at the END, not per stage.
allowed-tools: [Bash, Glob, Grep, Read]
---

# /verify-done (Codex variant)

The end gate of the loop: `cleanup → extract-links → blueprint → goal-prep → /goal → **/verify-done**`.
Answers "does it actually work, including what the plan didn't think of?" — not "are the boxes ticked?".

This is the **Codex CLI variant**. Behaviourally identical to the Claude variant — but Codex has **no `Workflow` tool**, so the three tiers run **sequentially in-session** (fan-out via `codex exec -` subprocesses where useful) instead of a parallel Workflow. Shared `roles/quality-review.md` is carried with the Codex skill (copied from the Claude tree by `ci/build-codex.sh` for native packaging; symlinked by `install-codex.sh` otherwise).

> **Letter = spirit.** The goal is an *honest* verdict — never a false DONE, never a FAIL for something that just couldn't be verified.
> **Gate, not fixer.** No `Edit`/`Write`: verify and report; fixing goes back to `/goal` or `/simplify`.

## Usage

```
/verify-done [<plan-or-spec path>] [--deep] [--block-on-quality]
```

- No path → locate the most recent `/blueprint` tasks file (`<spec-stem>/tasks.md`, or a single `<spec>.md`) or `goal.md`; **or** use a plain plan-mode / inline plan / "the diff + what it was meant to do" from the conversation. Ask via a numbered TUI prompt only if intent is genuinely unclear.
- `--deep` → Tier 2 across all requirements + adversarial inputs (default **light**).
- `--block-on-quality` → high-severity Tier 3 findings flip to NOT-DONE (default: Tier 3 **advisory**).

## Weaknesses / when NOT to use

- Needs a **runnable env** — unrunnable proofs/scenarios come back **UNKNOWN** → NOT-DONE "could not verify" (honest, not a defect of the change).
- Only as good as the original intent handed to Tier 2.
- **Unstructured plan = softer verdict** — with no `Done when:` proofs (a plan-mode/inline plan) verification is scenario-driven, not proof-driven. Fine for small tasks; for critical work write proofs via `/blueprint`.
- Not a bug hunter (use `/code-review`), not a single-change check (use `/verify`), not maintainability auto-fix (use `/simplify`).

## What it does

1. **Resolve inputs** (**plan-source-agnostic**): EITHER a `/blueprint` plan — `<spec-stem>/tasks.md` (+ `<spec-stem>/reference.md`), or a single `<spec>.md` — (or `goal.md`) → parse `Done when:` lines into proofs, intent = the `reference.md` (or the single file itself); OR an unstructured plan (plan-mode/inline/just-the-diff) → there are no `Done when:` lines, so **derive** a few concrete shell proofs from what the plan promises and use the plan prose itself as the intent (pass it into any `codex exec -` subprocess explicitly — subprocesses don't see your session). Always grab `build/test/regression` from the repo. Plus: a sandbox (throwaway `git worktree` if possible, else temp dir, else `none`); knobs `--deep`/`--block-on-quality`; read `roles/quality-review.md`.
2. **Run the three tiers sequentially:**
   - **Tier 1 — Conformance:** run each `Done when:` proof (explicit or derived) + build/test/regression in the sandbox → `PASS|FAIL|UNKNOWN` per check. With an unstructured plan and nothing derivable, Tier 1 falls back to build/test only; if those are absent too it's empty → verdict leans on Tier 2 (report it).
   - **Tier 2 — Independent scenarios:** from the ORIGINAL intent, generate risk-ranked user-case/edge/adversarial scenarios (light by default; `--deep` widens). Each scenario must be **grounded** in a quote from the intent (drop+count ungrounded). Run the runnable ones in the sandbox; the rest are honest UNKNOWN. Use `codex exec -` subprocesses to parallelize generation/runs if helpful.
   - **Tier 3 — Quality (advisory):** runs LAST and only if behaviour works; feed the prompt body of `roles/quality-review.md` (only the text BETWEEN its `BEGIN_PROMPT`/`END_PROMPT` sentinels — skip the provenance header) to `codex exec -` (or inline) → structured maintainability findings. Advisory unless `--block-on-quality`.
3. **Report** the short verdict + three honest buckets. Hand findings back to `/goal` or `/simplify`; fix nothing.

## Honesty rails (non-negotiable)

1. **UNKNOWN ≠ pass/fail** — can't run it → UNKNOWN with a reason; no runnable env → all UNKNOWN → NOT-DONE "could not verify"; never a false DONE/FAIL.
2. **Don't invent requirements** — Tier-2 scenarios carry `groundedIn`; "doesn't do X" where X was never asked → UNKNOWN + confirm-with-human, not auto-FAIL; ungrounded discarded + counted.
3. **No silent truncation** — always list what wasn't run/covered.

## Output

```
VERDICT: DONE | NOT-DONE — <reason>
  Tier 1: N/M PASS, K UNKNOWN
  Tier 2: generated G (D discarded), ran R; confirmed gaps: …
  Tier 3: F findings (advisory|blocking) — listed
  NOT covered (check manually): …
```

**DONE ⟺** Tier 1 fully PASS **and** Tier 2 no confirmed (high-confidence, grounded) gap **and** quality not blocking (unless `--block-on-quality`); else NOT-DONE + buckets (confirmed failures / UNKNOWN-to-check / suspected-out-of-scope).

## Connections

- **Input:** a `/blueprint` plan (a `<spec-stem>/` directory with `tasks.md` + `reference.md`, or a single `<spec>.md`) or a `goal-prep` charter (which writes "hand finished work to `/verify-done`").
- **Per-stage vs end:** lightweight per-stage `Done when:` lives in execution (seeded by goal-prep); `/verify-done` is the holistic END gate — don't run it per stage.
- **NOT** `/verify` / `/code-review` / `/blueprint` Phase 7.6 (which reviews the *plan*; `/verify-done` reviews the *result*).

## Self-check before reporting

- Every `Done when:` proof actually ran, or honestly UNKNOWN (not silently PASS)?
- All Tier-2 scenarios grounded in the original intent (none invented)?
- Verdict NOT-DONE whenever behaviour is unverified?
- Stayed a gate — zero edits?
