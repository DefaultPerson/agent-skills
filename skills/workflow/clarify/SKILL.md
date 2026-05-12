---
name: clarify
description: >
  Use when you have a clean spec/notes file that needs to be made
  implementation-ready: decomposed into atomic tasks with verifiable
  acceptance criteria (Given/When/Then + shell proof commands),
  constraints, edge cases, and risk surface. Output is suitable for
  human implementation, mattpocock:tdd, or Claude Code goal feature.
  Tradeoff: slow and thorough — overkill for tasks under 1 hour. For
  freeform PRD use mattpocock:to-prd instead. Triggers: "clarify",
  "/clarify", "уточни спеку", "enrich spec", "обогати спеку",
  "decompose spec".
when_to_use: >
  The input is a cleaned-up markdown spec/notes file (probably after
  /cleanup) that captures the WHAT but not the HOW. You want to turn it
  into atomic tasks with shell-verifiable AC before handing to a builder
  (human, mattpocock:tdd, or goal feature). Do NOT use for raw chat
  exports (run /cleanup first), for already-decomposed specs, or for
  product-management-style PRDs (mattpocock:to-prd is better suited).
allowed-tools: [Bash, Glob, Grep, Read, Edit, Write, Agent, AskUserQuestion, WebSearch, WebFetch]
---

# Clarify

Turn a clean spec into an implementation-ready document with atomic tasks, verifiable acceptance criteria, contracts, edge cases, and risks.

> **Letter = spirit.** If a rule blocks you from reaching the goal it was
> written for, the rule is wrong, not the goal. Don't look for a wording
> loophole — ask what the rule is protecting, and protect that.

## Usage

```
/clarify <spec.md> [--consensus-rounds N]
```

`--consensus-rounds` defaults to 3. Set it to 0 to skip the cross-model consensus loop (Phase 7.6) — only internal validation runs.

## Weaknesses and when NOT to use

- **Slow and thorough — overkill for hour-long tasks.** Decomposition + AC + edge cases + 3 consensus rounds (if codex is available) take 10-15 minutes. For smaller tasks, write the AC by hand.
- **Does not work on raw chat exports or unstructured notes.** The input spec must already be sectioned with `## ` (after `/cleanup`). Otherwise — abort.
- **Not suited for product-style PRDs.** This skill forces test-first AC with proof commands; for product-management PRDs use `mattpocock:to-prd` (freeform success metrics).
- **Phase 7.6 consensus loop requires the codex CLI.** Without it — fallback to internal validation (a single model reviewing its own output, weaker).
- **Not for autonomous orchestration.** The output has no `[P]` markers, Stages, or dependency graphs — the execute pipeline was removed from this repo in v2.0. Output is for `mattpocock:tdd` or manual work.

## How to do it wrong vs right

### AC format

❌ **Wrong:** `AC-1.1: API returns correct response`
- "Correct" — who decides?
- No proof command
- Boolean (works / doesn't) — no UNKNOWN

✅ **Right:** `AC-1.1: GET /api/users returns 200, JSON with {id,name,email}, <200ms`
- Concrete numbers and fields
- Proof: `curl -w '%{time_total}' localhost:8080/api/users | jq '.[].id'`
- Tristate: PASS / FAIL / UNKNOWN (when the server isn't running)

### Task scope

❌ **Wrong:** `TASK-1: Implement authentication system`
- Touches many files
- Multiple purposes mixed
- Cannot be verified with a single command

✅ **Right:** `TASK-1: Create User model in src/models/user.py with email/password fields`
- 1 file, clear boundaries
- Atomic — one testable deliverable
- AC: `python -c "from src.models.user import User; User(email='a@b', password='x')"` runs without errors

### Cross-model consensus disagreement

❌ **Wrong:** Codex returns NEEDS_IMPROVEMENT with an issue "requirement X looks unusual, suggest removing it". I apply it — I remove it.
- The user added the requirement on purpose.
- Removing it "helped me faster" but stomped the user's intent.

✅ **Right:** Issue type = NEEDS_USER (either Codex flagged it that way itself, or Claude self-assessor reclassified). AskUserQuestion with both views. The user decides.

## Roles

Step 2 (questioner pattern) and the Phase 7.6 consensus loop (with fallback validator) — all templates live in `roles/`:

- `roles/questioner.md` — format contract for AskUserQuestion in step 2 (not a subagent — a format spec)
- `roles/spec-validator.md` — fallback internal validation, used inside Phase 7.6 when codex is unavailable
- `roles/codex-reviewer.md` — Phase 7.6 Codex cross-model review (via `codex:rescue`)
- `roles/claude-self-assessor.md` — Phase 7.6 Claude self-assessment in a fresh subprocess (`claude -p`)

Substitutions:

| Variable | Source |
|---|---|
| `{spec_path}` | the spec file after step 6 (write) |
| `{round}` | round counter in Phase 7.6 (1, 2, 3) |
| `{spec_path}.bak` | original spec (pre-enrichment) for coverage check |
| `{spec_path}.critique.<round-1>.md` | prior critique (for round > 1) |

Spawn codex review: `Agent(subagent_type="codex:rescue", prompt=substitute("roles/codex-reviewer.md", vars))`.
Spawn claude self-assess: bash subprocess `claude -p` with prompt from `roles/claude-self-assessor.md`.
Fallback validator (no codex): `Agent(subagent_type="Explore", prompt=substitute("roles/spec-validator.md", vars))`.

## What the skill does (step by step)

1. **Read and analyze the spec.** Validate (markdown, has `## ` headers, no cleanup markers `[MISSING]`/etc), classify type (product / technical / small), scan the codebase if present, flag `[NEEDS CLARIFICATION]` items.
2. **Ask the user what's unclear** (hard gate). Max 5 questions via AskUserQuestion — format in `roles/questioner.md`. If the spec is already clear — skip.
3. **Decompose into atomic tasks.** Format adapts to type — details in `references/task-format.md`. Main rule: each task touches 1-3 files, AC is Given/When/Then + a shell Proof command (NO `[P]` markers or Stages — execute is gone).
4. **Define contracts** (FR-NNN format, MUST/SHOULD/MAY). Skip if the spec is small or single-component. Details in `references/contracts.md`.
5. **Self-review checklist.** Placeholder scan, internal consistency, scope check, ambiguity check. Fixes — loop back to the relevant phase.
6. **Write the enriched spec.** Back up the original (`<spec>.bak`), write enriched into the original path. Template structures: see `references/task-format.md`.
7. **Mechanical validation.** `python3 scripts/verify-spec.py <spec>`. FAIL → fix and re-run.
8. **Cross-model consensus loop (Phase 7.6).** Codex review + Claude self-assess, iterate until CONSENSUS or max rounds. Details — next section. Can be skipped with `--consensus-rounds 0`.
9. **Approval gate.** Summary report + AskUserQuestion (Approve / Modify / Questions). After approval: `"Spec approved. /clear before continuing."` — no downstream recommendation.

The old "Execution Order" section (Stages, [P] markers, dependency graph for parallel spawn) is GONE in v2.0. It existed for the execute orchestration, which no longer ships.

## Phase 7.6 — Cross-model consensus loop

After steps 6-7 (write enriched spec + verify-spec.py mechanical check), the convergence loop runs. Step 8 in the walkthrough is Phase 7.6.

```
MAX_ROUNDS = consensus_rounds_flag (default 3, 0 disables)
round = 0

if not has_codex():
  log WARNING "codex not installed, falling back to single-model validation"
  run roles/spec-validator.md (fallback)
  → CONSENSUS or NEEDS_FIX (single round only)
  goto Step 9 (approval gate)

while round < MAX_ROUNDS:
  round += 1

  # Codex review
  critique = Agent(subagent_type="codex:rescue",
                   prompt=substitute("roles/codex-reviewer.md",
                                     {spec_path, round}))
  save → <spec>.critique.<round>.md

  # Claude self-assessment in a fresh subprocess
  assessment = bash: claude -p < substitute("roles/claude-self-assessor.md",
                                            {spec_path, round})

  # Exit?
  if critique.verdict == PASS and assessment.verdict == AGREE_PASS:
    → CONSENSUS, exit loop

  # Process issues
  for each issue in critique.issues:
    cat = assessment.categorization[issue.id]
    if cat == ACCEPT: apply suggestion to spec
    elif cat == REJECT_PETTY: log to <spec>.critique.<round>.rejected.md
    elif cat == NEEDS_USER: queue for AskUserQuestion

  if queue not empty:
    AskUserQuestion with the issues
    apply user decisions

  # Oscillation detection
  if hash(critique.issues) == hash_round_minus_2:
    → ESCALATE to user: "the models are stuck — your call"
    break

if round == MAX_ROUNDS and no CONSENSUS:
  ESCALATE to user: "(A) approve as-is, (B) abort, (C) one more round"
```

Failure modes:
- **Codex unavailable** → fallback to `roles/spec-validator.md` (single-model), workflow continues.
- **Models gang up on user intent** → `roles/codex-reviewer.md` explicitly forbids proposing removal of unusual requirements (surface as NEEDS_USER instead). `roles/claude-self-assessor.md` mirrors the rule.
- **Petty disagreements** → REJECT_PETTY category, logged to rejected.md with reasoning, not applied.
- **Oscillation** → hash comparison between rounds N and N-2, escalation.

## Outputs

- `<spec>.bak` — original before enrichment
- `<spec>` — overwritten with enriched version
- `<spec>.critique.1.md`, `<spec>.critique.2.md`, ... — Codex critiques per round (if the consensus loop ran)
- `<spec>.critique.<round>.rejected.md` — petty-issue rejections with reasoning (if any)

Git: `pre-clarify: <name>` (snapshot before) and `clarify: enrich <name>` (after step 6).

## Connections to other skills

- **Input:** typically after `/cleanup` (sectioned markdown without `[MISSING]` markers). A manually written spec is also fine if it's structurally valid.
- **Output:** enriched spec with AC + proof commands, suitable for:
  - mattpocock:tdd (test-first implementation)
  - Claude Code goal feature (for measurable success criteria)
  - manual implementation
  - independent `claude -p` verify for AC checks after implementation
- **Does not call** other skills automatically. After step 9 (approval): `Spec approved. /clear before continuing.` — no recommendation.
- **Cross-model dependency:** Phase 7.6 uses `codex:rescue` if installed. Without it — graceful fallback.

## Rules

### Commonality
The spec is a shared artifact. Downstream work (mattpocock:tdd, goal feature, manual builder) makes decisions from it. If you let a placeholder through, leave a vague AC, or fail to resolve a contradictory FR — the next step works from a holey map. Not "helping faster" — breaking the shared work.

### Prior commitment
In step 5 (self-review) you committed to running placeholder scan + consistency + ambiguity check. In step 7 — `verify-spec.py`. In step 8 — the consensus loop (or fallback). Skipping any step withdraws the basis for the final verdict the user is going to act on.

### Social proof (cross-model rationale)
Phase 7.6 exists because single-model self-review is weaker. Per consensus research (AltimateAI/claude-consensus, ARIS — adversarial cross-model review), an independent second model catches issues the first biases past. If you "skip" Phase 7.6 when codex is present, you remove the only real basis to trust the spec beyond "Claude approved its own output".

## Self-check before delivering the result

Would this spec pass review by a senior engineer who has to build the system from it? Concretely:

- Does every AC have a concrete proof command (not "it works", not "manual check")?
- No placeholders (`TBD`, `...`, `[NEEDS CLARIFICATION]`, `<insert here>`)?
- Is every task atomic — 1-3 files, single purpose, executable by an independent worker without questions to the author?
- Did Phase 7.6 pass (or was it explicitly skipped with reasoning)?
- Coverage: does every Overview item have at least one task? Does every task track back to Overview / FR?
- Backup `<spec>.bak` exists — the user can roll back?

If "no" on any item — redo, don't ship.
