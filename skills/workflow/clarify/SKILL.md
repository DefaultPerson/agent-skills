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

Step 2 (questioner pattern) and the Phase 7.6 consensus loop (with fallback validator) — templates live in `roles/`:

- `roles/questioner.md` — format contract for AskUserQuestion in step 2 (not a subagent — a format spec)
- `roles/codex-reviewer.md` — focus brief passed to `codex:adversarial-review` (from [openai/codex-plugin-cc](https://github.com/openai/codex-plugin-cc)). NOT a full prompt — that command owns the adversarial role and JSON output schema.
- `roles/claude-self-assessor.md` — Phase 7.6 Claude self-assessment in a fresh subprocess (`claude -p`), categorizes Codex findings as ACCEPT / REJECT_PETTY / NEEDS_USER
- `roles/spec-validator.md` — fallback used inside Phase 7.6 when codex-plugin-cc is not installed

Substitutions:

| Variable | Source |
|---|---|
| `{spec_path}` | the spec file after step 6 (write) |
| `{round}` | round counter in Phase 7.6 (1, 2, 3) |
| `{spec_path}.bak` | original spec (pre-enrichment) for coverage check |
| `{spec_path}.critique.<round>.json` | Codex JSON output per round |
| `{focus_brief}` | text content of `roles/codex-reviewer.md` (passed verbatim as USER_FOCUS) |

Invocations:
- **Codex adversarial review:** `Skill(skill="codex:adversarial-review", args="--wait --scope working-tree \"{focus_brief}\"")`. Output is structured JSON with findings (file, line_start, line_end, confidence, recommendation). Working-tree scope reads the uncommitted spec edit directly.
- **Claude self-assessment:** Bash subprocess `claude -p` with the prompt from `roles/claude-self-assessor.md` plus the Codex JSON pasted in.
- **Fallback validator (no codex):** `Agent(subagent_type="Explore", prompt=substitute("roles/spec-validator.md", vars))`.

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

The loop drives `codex:adversarial-review` against the uncommitted spec edit, then has Claude (in a fresh `claude -p` subprocess) categorize the findings. Two independent passes per round — Codex finds, Claude triages.

```
MAX_ROUNDS = consensus_rounds_flag (default 3, 0 disables)
round = 0
focus_brief = read("roles/codex-reviewer.md")  # the focus block, not the whole file

if not codex_plugin_installed:
  log WARNING "codex-plugin-cc not installed; falling back to single-model validation"
  result = Agent(subagent_type="Explore",
                 prompt=substitute("roles/spec-validator.md",
                                   {spec_path, spec_path_bak}))
  → CONSENSUS or NEEDS_FIX (single round only)
  goto Step 9 (approval gate)

# Ensure spec is in working tree so adversarial-review can see it.
# (Step 6 already wrote <spec>; do NOT commit yet — uncommitted edit is
# exactly what working-tree scope is for.)

while round < MAX_ROUNDS:
  round += 1

  # 1. Codex adversarial review via Claude Code skill invocation
  findings_json = Skill(
    skill="codex:adversarial-review",
    args=f"--wait --scope working-tree \"{focus_brief}\""
  )
  save → <spec>.critique.<round>.json

  # 2. Claude self-assessment in a fresh subprocess
  assessment = bash: claude -p < (
    read("roles/claude-self-assessor.md")
    + "\n\nSpec file: " + spec_path
    + "\n\nCodex findings:\n" + findings_json
  )

  # 3. Exit on consensus
  if findings_json.summary == "approve" and assessment.verdict == AGREE_PASS:
    → CONSENSUS, exit loop

  # 4. Process findings via assessment categorization
  for each finding in findings_json.findings:
    cat = assessment.categorization[finding.id]
    if cat == ACCEPT: apply finding.recommendation to spec
    elif cat == REJECT_PETTY: log to <spec>.critique.<round>.rejected.md
    elif cat == NEEDS_USER: queue for AskUserQuestion

  if NEEDS_USER queue not empty:
    AskUserQuestion with the issues + both views
    apply user decisions

  # 5. Oscillation detection
  if hash(findings_json.findings) == hash_round_minus_2:
    → ESCALATE to user: "the models are stuck — your call"
    break

if round == MAX_ROUNDS and not CONSENSUS:
  ESCALATE to user: "(A) approve as-is, (B) abort, (C) one more round"
```

Failure modes:
- **codex-plugin-cc not installed** → fallback to `roles/spec-validator.md` (single-model), workflow continues with a warning.
- **Spec not in a git repository** → `codex:adversarial-review --scope working-tree` requires git. If the spec lives outside any repo, also fall back to spec-validator.
- **Models gang up on user intent** → `roles/codex-reviewer.md` focus brief explicitly forbids proposing removal of unusual requirements. `roles/claude-self-assessor.md` mirrors the rule when categorizing.
- **Petty disagreements** → Codex shouldn't emit them (its `finding_bar` excludes style). If any leak through → REJECT_PETTY category, logged with reasoning, not applied.
- **Oscillation** → hash comparison between rounds N and N-2, escalation.

Output schema reminder (from codex-plugin-cc's adversarial-review prompt):
```json
{
  "summary": "needs-attention | approve",
  "findings": [
    {
      "file": "<spec.md path>",
      "line_start": <int>,
      "line_end": <int>,
      "confidence": <0..1>,
      "recommendation": "<concrete change>"
    }
  ]
}
```

## Outputs

- `<spec>.bak` — original before enrichment
- `<spec>` — overwritten with enriched version
- `<spec>.critique.1.json`, `<spec>.critique.2.json`, ... — Codex adversarial-review findings per round (if the consensus loop ran)
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
- **Cross-model dependency:** Phase 7.6 uses `codex:adversarial-review` from [openai/codex-plugin-cc](https://github.com/openai/codex-plugin-cc) if installed and the spec is in a git repo. Without it — graceful fallback to `roles/spec-validator.md`.

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
