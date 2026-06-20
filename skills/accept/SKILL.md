---
name: accept
description: >
  Plan-aware final ACCEPTANCE gate: given a /blueprint plan (or goal.md
  charter) + the built code, adversarially verify the result actually
  works against the ORIGINAL intent — re-run every `Done when:` proof
  (Tier 1), generate + run independent user-scenarios the plan may have
  missed (Tier 2), then an advisory maintainability pass (Tier 3). Read-only
  GATE, not a fixer — emits DONE / NOT-DONE + a gap list. Heavy verification
  runs in a Workflow's sub-agents, so the main session gets only the verdict.
  Triggers: "accept", "/accept", "acceptance gate", "is this actually done",
  "verify the whole plan", "приёмка", "проверь что готово".
when_to_use: >
  Execution of a plan/goal is finished (or at a milestone) and you want one
  honest verdict on whether the END RESULT is really done — not just whether
  individual task checkboxes were ticked. NOT for a quick single-change check
  (use /verify) or diff-level bug hunting (use /code-review). Run it at the
  END, not per stage (per-stage Done-when checks belong in the execution loop).
allowed-tools: [Bash, Glob, Grep, Read, Agent, Workflow, AskUserQuestion]
---

# /accept

The end gate of the loop: `cleanup → extract → blueprint → goal-prep → /goal → **/accept**`.
It answers "does it actually work, including what the plan didn't think of?" — not "are the boxes ticked?".

> **Letter = spirit.** If a rule blocks you from reaching the goal it was written
> for, the rule is wrong, not the goal. Here the goal is an *honest* verdict —
> never a false DONE, never a FAIL for something that just couldn't be verified.

> **Gate, not fixer.** `/accept` has no `Edit`/`Write`. It verifies and reports;
> fixing goes back to `/goal` (autonomous) or `/simplify` (quality).

## Usage

```
/accept [<plan-or-spec path>] [--deep] [--block-on-quality]
```

- No path → locate the most recent `/blueprint` tasks file (`<spec>.md`) or `goal.md` charter; ask via `AskUserQuestion` if ambiguous.
- `--deep` → Tier 2 generates scenarios across all requirements + adversarial inputs (default is **light**: top high/med-risk only).
- `--block-on-quality` → high-severity Tier 3 findings flip the verdict to NOT-DONE (default: Tier 3 is **advisory**, never blocks).

## Weaknesses and when NOT to use

- **Needs a runnable environment.** If the `Done when:` proofs / scenarios can't run (no server, missing deps), they come back **UNKNOWN** → verdict NOT-DONE "could not verify". That's honest, not a failure of the change — but it means `/accept` can't bless work it can't exercise.
- **Only as good as the original intent it's handed.** Tier 2 grounds scenarios in the ORIGINAL intent (the reference file / pre-blueprint notes). Garbage intent → shallow scenarios.
- **Not a bug hunter or a linter.** Correctness bugs → `/code-review`; per-change behaviour → `/verify`; maintainability auto-fixes → `/simplify`. `/accept` is whole-plan *acceptance*.
- **Workflow tool may be unavailable** (plan-gated). Then it falls back to a sequential prose `Agent` fan-out — same verdict shape, just slower.

## What it does

1. **Resolve inputs** (this is the thin part — keep it cheap):
   - **Plan / tasks:** the `/blueprint` tasks file `<spec>.md` (primary) or a `goal.md` charter. Parse its `Done when:` lines into `doneWhenProofs = [{id, title, cmd}]`. Grab `buildCmd`/`testCmd`/`regressionCmd` from the repo if obvious (else null).
   - **Original intent:** the sibling `<spec>.reference.md` (blueprint Part D) or the pre-blueprint notes — NOT the task list. If you can't tell which file holds the real intent, ask once via `AskUserQuestion`.
   - **Sandbox:** prefer a throwaway git worktree (`ToolSearch` for `EnterWorktree`; use it if present), else a temp dir, else `none`. Scenarios/proofs run there so the repo isn't mutated.
   - **Knobs:** `--deep`, `--block-on-quality`. **Load** the text BETWEEN the `BEGIN_PROMPT` and `END_PROMPT` sentinels in `roles/quality-review.md` into `qualityPrompt` (skip the provenance header above `BEGIN_PROMPT` and the sentinel lines themselves — they're meta, not instructions).
2. **Run the gate** — invoke the workflow (heavy work stays in its sub-agents; only the verdict returns):
   ```
   Workflow({ scriptPath: "workflows/accept.workflow.js", args: {
     doneWhenProofs, buildCmd, testCmd, regressionCmd, coverageCmd,
     intentNotes, deep, blockOnQuality, qualityPrompt, sandboxKind, sandboxDir } })
   ```
   **Fallback** (Workflow unavailable / `scriptPath` doesn't resolve): run the same three tiers as a sequential `Agent(subagent_type="general-purpose")` fan-out — identical schemas, just not parallel. (If `scriptPath` fails, pass the script via `script:` inline.)
3. **Report** the short verdict + three honest buckets. Hand findings back to `/goal` or `/simplify`. Do not fix anything yourself.

## The three tiers (in the workflow)

- **Tier 1 — Conformance:** re-run every `Done when:` proof + build/test/regression in the sandbox → `PASS|FAIL|UNKNOWN`.
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

- **Input:** a `/blueprint` plan (`<spec>.md` tasks + `<spec>.reference.md` intent) or a `goal-prep` `goal.md` charter. `goal-prep` writes "hand finished work to `/accept`" into the charter; this is that hand-off.
- **Per-stage vs end:** the lightweight per-stage `Done when:` check lives in the execution loop (seeded by goal-prep); `/accept` is the heavy, holistic END gate. Don't run the full gate per stage.
- **Downstream of a NOT-DONE:** confirmed failures → back to `/goal` or manual; quality findings → `/simplify`.
- **Not** `/verify` (single change), **not** `/code-review` (diff bugs), **not** `/blueprint` Phase 7.6 (reviews the *plan* before build; `/accept` reviews the *result* after).

## Self-check before reporting

- Did every `Done when:` proof actually run, or is it honestly UNKNOWN (not silently PASS)?
- Are all Tier-2 scenarios grounded in the original intent (none invented)?
- Is the verdict NOT-DONE whenever behaviour is unverified (UNKNOWN), never a hopeful DONE?
- Did I stay a gate — zero edits to the codebase?
