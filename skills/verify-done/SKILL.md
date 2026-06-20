---
name: verify-done
description: >
  Plan-aware final ACCEPTANCE gate: given any plan (a /blueprint plan, a
  goal.md charter, OR a plain native plan-mode / inline plan) + the built
  code, adversarially verify the result actually works against the ORIGINAL
  intent — re-run every `Done when:` proof
  (Tier 1), generate + run independent user-scenarios the plan may have
  missed (Tier 2), then an advisory maintainability pass (Tier 3). Read-only
  GATE, not a fixer — emits DONE / NOT-DONE + a gap list. Heavy verification
  runs in a Workflow's sub-agents, so the main session gets only the verdict.
  Triggers: "/verify-done", "verify done", "accept", "acceptance gate",
  "is this actually done", "verify the whole plan", "приёмка", "проверь что готово".
when_to_use: >
  Execution of a plan/goal is finished (or at a milestone) and you want one
  honest verdict on whether the END RESULT is really done — not just whether
  individual task checkboxes were ticked. NOT for a quick single-change check
  (use /verify) or diff-level bug hunting (use /code-review). Run it at the
  END, not per stage (per-stage Done-when checks belong in the execution loop).
allowed-tools: [Bash, Glob, Grep, Read, Agent, Workflow, AskUserQuestion]
---

# /verify-done

The end gate of the loop: `cleanup → extract-links → blueprint → goal-prep → /goal → **/verify-done**`.
It answers "does it actually work, including what the plan didn't think of?" — not "are the boxes ticked?".

> **Letter = spirit.** If a rule blocks you from reaching the goal it was written
> for, the rule is wrong, not the goal. Here the goal is an *honest* verdict —
> never a false DONE, never a FAIL for something that just couldn't be verified.

> **Gate, not fixer.** `/verify-done` has no `Edit`/`Write`. It verifies and reports;
> fixing goes back to `/goal` (autonomous) or `/simplify` (quality).

## Usage

```
/verify-done [<plan-or-spec path>] [--deep] [--block-on-quality]
```

- No path → locate the most recent `/blueprint` tasks file (`<spec>.md`) or `goal.md` charter; **or** use an approved native plan-mode plan / an inline plan / "the diff + what it was meant to do" straight from the conversation. Ask via `AskUserQuestion` only if the intent is genuinely unclear.
- `--deep` → Tier 2 generates scenarios across all requirements + adversarial inputs (default is **light**: top high/med-risk only).
- `--block-on-quality` → high-severity Tier 3 findings flip the verdict to NOT-DONE (default: Tier 3 is **advisory**, never blocks).

## Weaknesses and when NOT to use

- **Needs a runnable environment.** If the `Done when:` proofs / scenarios can't run (no server, missing deps), they come back **UNKNOWN** → verdict NOT-DONE "could not verify". That's honest, not a failure of the change — but it means `/verify-done` can't bless work it can't exercise.
- **Only as good as the original intent it's handed.** Tier 2 grounds scenarios in the ORIGINAL intent (the reference file / plan / notes). Garbage intent → shallow scenarios.
- **Unstructured plan = softer verdict.** With no `Done when:` proofs (a plan-mode/inline plan), verification is **scenario-driven** rather than proof-driven — great for small tasks, weaker for critical ones. For high-stakes work, write proofs (`/blueprint`).
- **Not a bug hunter or a linter.** Correctness bugs → `/code-review`; per-change behaviour → `/verify`; maintainability auto-fixes → `/simplify`. `/verify-done` is whole-plan *acceptance*.
- **Workflow tool may be unavailable** (plan-gated). Then it falls back to a sequential prose `Agent` fan-out — same verdict shape, just slower.

## What it does

1. **Resolve inputs** (thin part — keep it cheap). `/verify-done` is **plan-source-agnostic** — use whichever you have:
   - **Structured (best, proof-driven):** a `/blueprint` tasks file `<spec>.md` → parse `Done when:` lines into `doneWhenProofs = [{id, title, cmd}]`; intent = sibling `<spec>.reference.md`. Or a `goal.md` charter (proofs from its audit table, intent from its stated outcome).
   - **Unstructured (plan-mode / inline / just-the-diff, scenario-driven):** an approved native plan-mode plan, an inline description, or "here's the change + what it was supposed to do." No `Done when:` lines exist, so: (a) **derive** a few concrete shell proofs from what the plan promises (an endpoint/CLI/behaviour it claims → a command that exercises it) into `doneWhenProofs`; (b) the plan prose **is** the intent → pass it verbatim as `intentNotes`. ⚠️ A plan-mode plan lives only in the conversation — the Workflow's sub-agents can't see it, so YOU read it from context and pass it in `intentNotes` (and any derived proofs).
   - **Always:** grab `buildCmd`/`testCmd`/`regressionCmd` from the repo if obvious (else null). If nothing identifies the real intent, ask once via `AskUserQuestion`.
   - **Sandbox:** prefer a throwaway git worktree (`ToolSearch` for `EnterWorktree`; use it if present), else a temp dir, else `none`. Scenarios/proofs run there so the repo isn't mutated.
   - **Knobs:** `--deep`, `--block-on-quality`. **Load** the text BETWEEN the `BEGIN_PROMPT` and `END_PROMPT` sentinels in `roles/quality-review.md` into `qualityPrompt` (skip the provenance header above `BEGIN_PROMPT` and the sentinel lines themselves — they're meta, not instructions).
2. **Run the gate** — invoke the workflow (heavy work stays in its sub-agents; only the verdict returns):
   ```
   Workflow({ scriptPath: "workflows/verify-done.workflow.js", args: {
     doneWhenProofs, buildCmd, testCmd, regressionCmd, coverageCmd,
     intentNotes, deep, blockOnQuality, qualityPrompt, sandboxKind, sandboxDir } })
   ```
   **Fallback** (Workflow unavailable / `scriptPath` doesn't resolve): run the same three tiers as a sequential `Agent(subagent_type="general-purpose")` fan-out — identical schemas, just not parallel. (If `scriptPath` fails, pass the script via `script:` inline.)
3. **Report** the short verdict + three honest buckets. Hand findings back to `/goal` or `/simplify`. Do not fix anything yourself.

## The three tiers (in the workflow)

- **Tier 1 — Conformance:** re-run every `Done when:` proof (explicit or derived) + build/test/regression in the sandbox → `PASS|FAIL|UNKNOWN`. With an unstructured plan and nothing derivable, Tier 1 falls back to build/test only; if those don't exist either it's empty → the verdict leans on Tier 2 (report it — softer than proof-driven).
- **Tier 2 — Independent scenarios:** one agent reads the **original intent** and generates risk-ranked user-case/edge/adversarial scenarios (light by default, `--deep` widens); the runnable ones execute in the sandbox. Catches what the plan's own proofs didn't.
- **Tier 3 — Quality (advisory):** runs LAST and only if behaviour works; `roles/quality-review.md` (thermo substance) emits structured maintainability findings. Advisory unless `--block-on-quality`.

## Honesty rails (non-negotiable)

1. **UNKNOWN ≠ pass/fail.** Can't run it → UNKNOWN with a reason. No runnable env → all UNKNOWN → NOT-DONE "could not verify" — never a false DONE, never a FAIL.
2. **Don't invent requirements.** Every Tier-2 scenario carries `groundedIn` (a quote from the original intent). A "system doesn't do X" where X was never asked → UNKNOWN + "confirm with human", not an auto-FAIL. Ungrounded candidates are discarded and **counted**.
3. **No silent truncation.** The `notCovered` list always reports what wasn't run/covered (UNKNOWNs, unrunnable scenarios).

## Output

```
VERDICT: DONE | NOT-DONE  — <reason>
  Tier 1 (conformance): N/M PASS, K UNKNOWN
  Tier 2 (scenarios):   generated G (D discarded), ran R; confirmed gaps: …
  Tier 3 (quality):     F findings (advisory|blocking) — listed
  NOT covered (check manually): …
```

**DONE ⟺** Tier 1 fully PASS **and** Tier 2 has no confirmed (high-confidence, grounded) gap **and** (quality not blocking, unless `--block-on-quality`). Otherwise NOT-DONE with the three buckets: confirmed failures / UNKNOWN-to-check / suspected-out-of-scope.

## Connections

- **Input:** a `/blueprint` plan (`<spec>.md` tasks + `<spec>.reference.md` intent), a `goal-prep` `goal.md` charter, or — for **small tasks** — a native plan-mode / inline plan straight from the conversation (`native plan mode → implement → /verify-done`). `goal-prep` writes "hand finished work to `/verify-done`" into the charter; this is that hand-off.
- **Per-stage vs end:** the lightweight per-stage `Done when:` check lives in the execution loop (seeded by goal-prep); `/verify-done` is the heavy, holistic END gate. Don't run the full gate per stage.
- **Downstream of a NOT-DONE:** confirmed failures → back to `/goal` or manual; quality findings → `/simplify`.
- **Not** `/verify` (single change), **not** `/code-review` (diff bugs), **not** `/blueprint` Phase 7.6 (reviews the *plan* before build; `/verify-done` reviews the *result* after).

## Self-check before reporting

- Did every `Done when:` proof actually run, or is it honestly UNKNOWN (not silently PASS)?
- Are all Tier-2 scenarios grounded in the original intent (none invented)?
- Is the verdict NOT-DONE whenever behaviour is unverified (UNKNOWN), never a hopeful DONE?
- Did I stay a gate — zero edits to the codebase?
