---
name: blueprint
description: >
  Use when you have a clean spec/notes file and want a readable,
  implementation-ready PLAN: atomic vertical-slice tasks each with a
  `Done when:` shell proof, plain-language requirements
  ([must]/[nice]/[later]), edge cases, ranked assumptions + open questions,
  and risks. Reads like a plan, not an RFC. Suitable for human
  implementation, mattpocock:tdd, or Claude Code goal feature. Tradeoff:
  slow and thorough — overkill for tasks under 1 hour. For freeform PRD use
  mattpocock:to-prd instead. Triggers: "blueprint", "/blueprint", "plan
  this spec", "составь план", "clarify", "/clarify", "уточни спеку",
  "enrich spec", "decompose spec".
when_to_use: >
  The input is a cleaned-up markdown spec/notes file (probably after
  /cleanup) that captures the WHAT but not the HOW. You want a readable plan
  of atomic tasks with shell-verifiable `Done when:` proofs before handing to
  a builder (human, mattpocock:tdd, or goal feature). Do NOT use for raw chat
  exports (run /cleanup first), for already-decomposed specs, or for
  product-management-style PRDs (mattpocock:to-prd is better suited).
allowed-tools: [Bash, Glob, Grep, Read, Edit, Write]
---

# Blueprint (Codex variant)

Turn a clean spec into a readable, implementation-ready **plan**: atomic vertical-slice tasks each with a `Done when:` shell proof, plain-language requirements, edge cases, ranked assumptions, and risks. The rigor lives in the proofs — not in ceremony.

This is the **Codex CLI variant**. Behaviourally identical to the Claude Code variant — only the user-interaction and cross-model-consensus invocations differ. **Phase 7.6 is symmetric**: this variant uses `claude -p` as the cross-model reviewer (the host is Codex, so Claude is "the other model"), optionally a diverse third model via OpenRouter, and `codex exec` as the same-family fresh-ctx self-assessor. Shared resources (`roles/`, `scripts/`, `references/`) come from the Claude variant tree via install-time symlinks.

> **Letter = spirit.** If a rule blocks you from reaching the goal it was
> written for, the rule is wrong, not the goal. Don't look for a wording
> loophole — ask what the rule is protecting, and protect that.

> **Was `/clarify`.** Renamed to `/blueprint` (it's a planning tool). `clarify` / `уточни спеку` still route here as aliases.

## Usage

```
/blueprint <spec.md> [--consensus-rounds N]
```

- `--consensus-rounds` defaults to 3. Set it to 0 to skip the cross-model consensus loop (Phase 7.6) — only internal validation runs.
- **Third reviewer (optional, opt-in):** if `OPENROUTER_API_KEY` is set, Phase 7.6 adds one diverse frontier model via OpenRouter (default `z-ai/glm-5.2`, override with `OPENROUTER_MODEL`) as an independent finder alongside `claude -p`. No key → it stays Claude + Codex-self-assess, no error.

## Weaknesses and when NOT to use

- **Slow and thorough — overkill for hour-long tasks.** Decomposition + Done-when proofs + edge cases + 3 consensus rounds (if claude CLI is available) take 10-15 minutes. For smaller tasks, write the plan by hand.
- **Does not work on raw chat exports or unstructured notes.** The input spec must already be sectioned with `## ` (after `/cleanup`). Otherwise — abort.
- **Not suited for product-style PRDs.** This skill forces a `Done when:` shell proof per task; for product-management PRDs use `mattpocock:to-prd` (freeform success metrics).
- **Phase 7.6 needs at least one external reviewer.** Best signal: the `claude` CLI on `$PATH` (npm `@anthropic-ai/claude-code`), invoked as `claude -p` with `roles/codex-reviewer.md`. Optionally a third model via OpenRouter (`OPENROUTER_API_KEY`). With **neither** — fallback to single-model `codex exec` of `roles/spec-validator.md` (weaker).
- **Not for autonomous orchestration.** The output has no `[P]` markers, Stages, or dependency graphs — the execute pipeline was removed in v2.0.
- **Non-interactive mode (`codex exec` invocation of `/blueprint` itself).** The clarifying questions (step 2), Scope-cut audit (step 5), approval (step 9), and backup disposition (step 10) need user input via TUI. From `codex exec` without TTY, fail with an explicit error rather than auto-resolving. Must run from `codex` TUI.

## How to do it wrong vs right

### Task proof (`Done when:`)

❌ **Wrong:** `Done when: the endpoint works.`
- "Works" — who decides? No command. Boolean — no UNKNOWN.

✅ **Right:** `Done when: \`curl -sw '%{http_code}' :8080/api/users -o /dev/null\` prints 200 in <200ms.`
- Concrete numbers, a runnable command. Tristate: PASS / FAIL / UNKNOWN.

### Task scope

❌ **Wrong:** `### TASK-1: Implement authentication system` — many files, mixed purposes, not one-command verifiable.

✅ **Right:** `### TASK-1: Create User model in src/models/user.py with email/password`
- 1 file, one deliverable. `Done when: \`python -c "from src.models.user import User; User(email='a@b',password='x')"\` runs clean.`

### Cross-model consensus disagreement

❌ **Wrong:** A reviewer returns "requirement X looks unusual, suggest removing it". I apply it — I remove it.
- The user added it on purpose. Removing it stomps their intent.

✅ **Right:** Issue type = NEEDS_USER (the reviewer flagged it, or the Codex self-assessor reclassified). Prompt the user with both views via numbered TUI list. The user decides.

### Implicit scope reduction

❌ **Wrong:** Input mentions "batch user creation" and "admin role for DELETE". I tag them `[later]` and move on; "rate limiting" → `Non-goals`, without asking.
- The user wrote those on purpose. Tagging `[later]` silently == deleting a user-stated requirement.

✅ **Right:** Step 5 has a hard-gate Scope-cut audit with numbered TUI prompts. Anything tagged `[later]`, moved to `Non-goals`, or dropped from a task's coverage is surfaced **before** the plan is written. Per item: `Keep deferred` / `Include in v1` / `Drop entirely`. Nothing quietly downgraded.

## Writing style for the plan

> Sharpen/terminology/cross-ref rules borrowed from `mattpocock:grill-with-docs` (MIT). The "challenge the task" and "assumptions & open questions" moves are borrowed from [malakhov-dmitrii/fusion](https://github.com/malakhov-dmitrii/fusion) (MIT). Applies in step 2 (questioner) and steps 3-5.

### Challenge the task before decomposing (multi-angle)

Before turning notes into tasks, spend one pass questioning the task itself: what if we **don't build it** (need met another way)? a **much simpler** version (80/20)? does the right shape **depend on a future plan**? which **scenarios** flip the answer (scale, single- vs multi-tenant, offline)? If a cheaper framing is plausible, surface it as a step-2 TUI question — don't silently commit to the literal reading.

### Sharpen fuzzy language

When the input uses vague terms ("user", "account", "system", "data"), propose a precise canonical term and ask which the user means via TUI prompt. Push for precision until the next reader can't misread it.

❌ **Fuzzy:** "Users can manage their subscriptions"
✅ **Sharp:** "Subscription owners (Customer accounts) can cancel/resume their own subscriptions; admins can on behalf of any Customer."

### Be opinionated about terminology

Pick ONE canonical term per concept and keep it through the whole plan. Map to a code type where one exists; note aliases in a brief "Terminology" preamble if the ambiguity is worth flagging.

### Keep requirements tight and plain

Each requirement is one plain sentence, tagged `[must]` / `[nice]` / `[later]` — no RFC-2119 `MUST/SHOULD/MAY` shouting, no forced `FR-NNN` ids (add light `R1`/`R2` ids only for big specs needing task↔requirement links). WHAT, not HOW. Details: `references/contracts.md`.

❌ **Ceremonial:** `FR-001: The auth middleware MUST verify the signature, check expiration, return 401...`
✅ **Plain:** `- [must] Bad tokens (missing / expired / wrong signature) → 401.`

### Stress-test edge cases with concrete scenarios

Each edge case is a concrete input + expected output, written inline (`Edge: ...`).

❌ **Abstract:** "Edge case: empty request body."
✅ **Concrete:** `Edge: POST /users with body {} (no email) → 400 {error:"email_required"}.`

### Cross-reference with code

If the codebase has paths/types matching spec terms, read them. If code says X and the spec says Y, surface the conflict in step 2 via TUI prompt.

❌ **Stale:** Spec says `POST /users {email, name}`; code already accepts `{email, name, phone}`. Plan written as-is.
✅ **Reconciled:** "Spec says POST {email, name}; code already accepts phone. Regression, or forgot phone?" — ask first.

### Vertical slices, not horizontal layers

Each task cuts through ALL relevant layers end-to-end (schema → API → UI → tests). A finished slice is demoable on its own. Many thin slices over few thick ones.

❌ **Horizontal:** TASK-1 "all DB columns"; TASK-2 "all API"; … Nothing demoable until task 3.
✅ **Vertical:** TASK-1 "email on User: column + API + form + test"; TASK-2 "phone: same set."

### Foundations first — don't start in mid-air, don't bury the scaffold

The **first task** leaves the project runnable/verifiable, so every later `Done when:` has something to run against. **Greenfield** → first task creates the minimal skeleton + smoke test; `Done when:` proves a fresh clone goes green (`npm ci && npm test` exits 0 with ≥1 passing test; `uv run pytest -q` collects+passes one). **Brownfield** → first task is a one-line baseline proof the build/test is green (`make test` exits 0); pins the starting state `/verify-done` re-checks first. **No buried scaffold:** the harness/fixtures/CI live in that task and are reused via `**Leverage**: <foundation task> harness` — never re-created as a side effect of a feature task. **Order, don't graph:** group by area, each area exactly once, prerequisites above dependents; the only sequencing is that order + an inline `· after TASK-x` in the checklist. No Stages, `[P]`, or dependency graph.

### Behavioural `Done when:`, not procedural

The proof describes what the system DOES (observable through its interface), not HOW.

❌ **Procedural:** `Done when: middleware extracts the token, calls validateJWT(), returns 401.`
✅ **Behavioural:** `Done when: \`curl -H 'Auth: <expired>' :8080/me\` → 401 {error:"token_expired"}.`

### One place for what needs a human — `## Needs your attention`

Everything that needs **you** goes in ONE block at the top of the tasks file — never scattered across both files and a dozen per-task `Status:` lines.

`tasks.md` → **`## Needs your attention`** (omit the heading on a clean plan). Two kinds of line: **blocking forks** — `❓ NEEDS YOU` with a light tag (`[decision]`/`[question]`/`[unknown]`), each ending in **`→ blocks: TASK-n[, TASK-m]`** (or `→ blocks: all`); **HITL tasks** — `HITL: TASK-n — title (why)`, one per task carrying `**Mode**: HITL`.

`reference.md` → **`## Assumptions`** — ranked **non-blocking** assumptions only (high/medium/low + basis). Blocking `❓ NEEDS YOU` do NOT appear here. No item in both files.

```markdown
# tasks.md
## Needs your attention
- ❓ NEEDS YOU [decision]: is DELETE admin-only? (input was ambiguous) → blocks: TASK-11
- HITL: TASK-3 — auth design call (pick session vs bearer before building)

# reference.md
## Assumptions
- Assume Postgres (high — matches src/db).
- Assume JWT, not sessions (medium — input didn't say).
```

### tasks.md is a lean checklist; full task detail lives in reference.md

The tasks file is a **tracker, not a spec dump**. The verbose per-task detail (files, proof, edge cases) lives in `reference.md` under `## Task details`, read when you implement a given task.

- `tasks.md` → `## Tasks` is a **checklist**: one line per task, **`- [ ] TASK-n — short title`** (bare `TASK-n`, never `### TASK-n`), grouped under `**▸ AREA-n**` (each group once, foundations-first), light flags `· after TASK-x` / `· HITL` / `· ❓`. No graph, no `[P]`, no Stages.
- `reference.md` → `## Task details` holds the full `### TASK-n` blocks (`**Files**`, `**Leverage**`, `Done when:` proof, inline `Edge:`), grouped by `▸ AREA-n` mirroring the checklist. **`Done when:` lives here — `/verify-done` + goal-prep read the proofs from `## Task details`.**
- One-to-one: every checklist `TASK-n` ↔ exactly one `### TASK-n` block.

### Keep the reference concise and DRY — lossless

The reference is the plan's body now: state each fact ONCE, in the section it belongs to, cross-reference instead of repeating. Tighten prose to facts (cut filler, restatement) but **never drop a fact** — every requirement, decision, assumption, risk, edge, and code-pointer survives somewhere. No cross-section duplication (a fact lives in exactly one of Overview/Requirements/Assumptions/Risks/Non-goals/Task details; per-task specifics only in the `### TASK-n` block). Structured facts → a table. Merge near-duplicate prose/risks. Lossless check: every distinct fact from the pre-edit reference + `<spec>.bak` is still findable.

## Roles

Step 2 (questioner pattern) and the Phase 7.6 consensus loop — templates live in `roles/` (shared with the Claude variant via install-time symlinks):

- `roles/questioner.md` — format contract for clarifying questions in step 2 (an `AskUserQuestion` format spec for the Claude variant — in Codex, render as numbered TUI prompts). Includes the multi-angle challenge.
- `roles/codex-reviewer.md` — **full prompt** for the cross-model reviewer. **Same file used by both variants.** In the Codex variant: passed to `claude -p` as stdin, with `<spec_path>` substituted.
- `roles/openrouter-reviewer.md` — **full prompt** for the optional third reviewer (a diverse frontier model via OpenRouter). The spec content is appended to the prompt body (the model has no file access).
- `roles/codex-self-assessor.md` — Phase 7.6 self-assessor for the Codex variant (mirror of `claude-self-assessor.md`). Categorizes the union of reviewer findings as ACCEPT / REJECT_PETTY / NEEDS_USER. Run via `codex exec -` fresh subprocess.
- `roles/spec-validator.md` — fallback used inside Phase 7.6 when NO external reviewer is available.

Substitutions:

| Variable | Source |
|---|---|
| `{spec_path}` | the spec file after step 6 (write) |
| `{round}` | round counter in Phase 7.6 (1, 2, 3) |
| `{spec_path}.bak` | original spec (pre-enrichment) for coverage check |
| `{reviewer_prompt}` | `roles/codex-reviewer.md`, `<spec_path>` substituted, passed as stdin to `claude -p` |

Invocations (Codex variant):

- **Cross-model reviewer = `claude -p`** (Claude is the "other model" since host is Codex):
  ```bash
  command -v claude >/dev/null 2>&1 || { echo "claude CLI not installed; using fallback"; FALLBACK=1; }
  PROMPT="$(sed "s|<spec_path>|$SPEC_PATH|g" roles/codex-reviewer.md)"
  OUTPUT="$(printf '%s' "$PROMPT" | claude -p -)"
  FINDINGS="$(printf '%s' "$OUTPUT" | python3 -c '
import sys, re, json
text = sys.stdin.read()
matches = re.findall(r"```json\s*\n(.*?)\n```", text, re.DOTALL)
print(matches[-1] if matches else json.dumps({"summary":"approve","findings":[]}))
')"
  ```
- **OpenRouter third reviewer (optional):** only if `OPENROUTER_API_KEY` is set. The model has no file access — append the spec content to the prompt body. Same JSON schema; same extractor.
  ```bash
  OR_MODEL="${OPENROUTER_MODEL:-z-ai/glm-5.2}"                # primary
  OR_FALLBACK="${OPENROUTER_FALLBACK:-moonshotai/kimi-k2.6}"  # OpenRouter auto-routes to this if primary fails
  PROMPT="$(cat roles/openrouter-reviewer.md)
SPEC FILE ($SPEC_PATH):
$(cat "$SPEC_PATH")"
  resp="$(curl -sS --max-time 120 -w $'\n%{http_code}' \
    https://openrouter.ai/api/v1/chat/completions \
    -H "Authorization: Bearer $OPENROUTER_API_KEY" -H "Content-Type: application/json" \
    -H "X-Title: blueprint consensus" \
    -d "$(jq -nc --arg m "$OR_MODEL" --arg fb "$OR_FALLBACK" --arg c "$PROMPT" \
          '{model:$m, models:[$m,$fb], messages:[{role:"user",content:$c}], temperature:0.2}')")"
  http="${resp##*$'\n'}"; body="${resp%$'\n'*}"
  [ "$http" = "200" ] && printf '%s' "$body" | jq -r '.choices[0].message.content' \
    || echo "OpenRouter HTTP $http — dropping third reviewer this round" >&2
  ```
- **Self-assessor = `codex exec -`** (same family as host, fresh ctx) over the union of reviewer findings:
  ```bash
  printf '%s\n\nSpec file: %s\n\nReviewer findings (union):\n%s' \
    "$(cat roles/codex-self-assessor.md)" "$SPEC_PATH" "$ALL_FINDINGS" \
    | codex exec -
  ```
- **Fallback validator (no external reviewer):**
  ```bash
  envsubst < roles/spec-validator.md | codex exec -
  ```

## What the skill does (step by step)

1. **Read and analyze the spec.** Validate (markdown, `## ` headers, no `[MISSING]` markers), classify type (product / technical / small), scan the codebase if present, flag `[NEEDS CLARIFICATION]` items.
2. **Challenge + ask** (hard gate). Run the multi-angle challenge (don't-build / simpler / future-dependent / scenarios). Then ask what's unclear — max 5 questions via numbered TUI prompts (`roles/questioner.md`'s `AskUserQuestion` semantic → numbered TUI list). If already clear and the framing is sound — skip.
3. **Decompose into atomic tasks.** Format adapts to type — `references/task-format.md`. Each task touches 1-3 files (a vertical slice) and has a `Done when:` line with a runnable shell proof. **Foundations first** — the first task leaves the project runnable/green (greenfield: skeleton + smoke test; brownfield: a baseline proof), the harness lives there and is reused, never buried later. Order so prerequisites precede dependents; each area appears exactly once. No `[P]`, Stages, `AC-N.N`, or `Given/When/Then`.
4. **Pin requirements & contracts.** Plain sentences tagged `[must]`/`[nice]`/`[later]` (light `R1`/`R2` ids only if needed). Skip if small/single-component. Details: `references/contracts.md`.
5. **Self-review checklist.** Placeholder scan, internal consistency, ambiguity check, and a **hard-gate Scope-cut audit (user-facing)**.

   **Hard-to-reverse decisions** (no ceremony). If a task locks in a choice that's costly to undo with a real trade-off (DB schema, public API contract, auth/infra/messaging choice, security boundary, major dependency lock-in), record it in **one line** in the reference file's `## Risks` — what was chosen + the trade-off. Genuine forks you shouldn't pick alone already go to the tasks file's `## Needs your attention` as `❓ NEEDS YOU` (with `→ blocks: TASK-n`). **No `docs/adr/` files, no numbering, no template.**

   The **Scope-cut audit (user-facing)** scans for deferral signals:
   - Requirements tagged `[later]`, or `[must]`/`[nice]` carrying `(v2)`, `(future)`, `(deferred)`, `(later)`, `(stretch goal)`, `(MVP only)`, `(out of scope for now)`, `(not for now)`.
   - `Non-goals` items mapping back to input.
   - Input features/endpoints/edge cases with no backing task or silently dropped.

   If any signal is found, surface a numbered TUI prompt per item with `Keep deferred (current)` / `Include in v1` / `Drop entirely` / `Drop (record in the plan)`. Apply decisions. For `Drop (record in the plan)`, note it in one line under the reference file's `## Non-goals` (what + why) — no separate files. Loop back to step 3/4 if scope changes require re-decomposition. NEVER write to disk while scope cuts are unconfirmed. Nothing found → gate silently passes.
6. **Write the plan.** Back up the original (`<spec>.bak`). Normally **two files** — a lean `tasks.md` checklist + a `reference.md` body. **When the plan is more than one file, put them in a flat directory `<spec-stem>/`** (e.g. `auth-spec.md` → `auth-spec/`) — **no nested subdirs**; a trivial spec that fits one file stays as `<spec>.md`.
   - **`<spec-stem>/tasks.md` — the at-a-glance tracker.** In order: a `> Task detail + context: see reference.md` pointer; **`## Needs your attention`** (only if it has content — blocking `❓ NEEDS YOU` each with `→ blocks: TASK-n`, plus one line per HITL task); then **`## Tasks`** — a **checklist**, one `- [ ] TASK-n — short title` line per task grouped by `**▸ AREA-n**` (each group once, foundations-first), light `· after TASK-x`/`· HITL`/`· ❓` flags. No `### TASK-n` blocks here.
   - **`<spec-stem>/reference.md` — the plan body + context.** `## Overview`, full `## Requirements` (`[must]/[nice]/[later]`), Terminology, **`## Assumptions`** (ranked **non-blocking** only — blocking `❓ NEEDS YOU` live in tasks.md, never here), `## Risks` (one line each), `## Non-goals`, and **`## Task details`** — the full `### TASK-n` blocks (`**Files**`, `**Leverage**`, `Done when:` proof, inline `Edge:`), grouped by `▸ AREA-n` mirroring the checklist. Keep it **concise + DRY — lossless**. **`Done when:` lives here — the contract `/verify-done` + goal-prep read.**
   - **Self-sufficiency rule:** to execute TASK-n, read its `### TASK-n` block in the reference; the checklist tells you what's left + order. Single-file fallback: `<spec>.md` with `## Overview` + `## Tasks` checklist + `## Task details`. Downstream resolve `<spec-stem>/tasks.md` (checklist) + `<spec-stem>/reference.md` `## Task details` (proofs). Template: `references/task-format.md`.
7. **Mechanical validation.** `python3 scripts/verify-spec.py <spec>`. FAIL → fix and re-run. (Style warnings about old ceremony are non-blocking.)
8. **Cross-model consensus loop (Phase 7.6).** External reviewer(s) find, Codex self-assesses, iterate until CONSENSUS or max rounds. Next section. Skippable with `--consensus-rounds 0`.
9. **Approval gate.** Summary report + numbered TUI prompt (Approve / Modify / Questions). After approval → step 10.
10. **Backup disposition + downstream offer.** First TUI prompt (backup):
    1. **Delete `<spec>.bak`** (default) — `rm <spec>.bak`. Rollback via `git checkout HEAD -- <spec>` (the `pre-blueprint: <name>` snapshot holds the original).
    2. **Keep `<spec>.bak`** — for further iteration or a safety net.

    Then, **only if `/to-prd` is installed** (`~/.codex/skills/to-prd/SKILL.md` exists), a second TUI prompt (downstream):
    1. **Stay local** (default) — continue manually, with `mattpocock:tdd`, or `codex exec` driving the build.
    2. **Publish via `/to-prd`** — print `Type /to-prd next to wrap this spec as a PRD and publish.` Do NOT auto-invoke.

    If `/to-prd` is not installed → print `"Plan approved. /clear before continuing."`.

## Phase 7.6 — Cross-model consensus loop (Codex variant — symmetric to Claude)

After steps 6-7 (write plan + verify-spec.py), the convergence loop runs. Each round, every **available** external reviewer finds independently; Codex (fresh `codex exec -`) triages the **union**. Reviewers:

- **Claude** — `claude -p` with `roles/codex-reviewer.md` (if `claude` on `$PATH`).
- **OpenRouter third reviewer** — a diverse frontier model (default `z-ai/glm-5.2`) via the chat API (if `OPENROUTER_API_KEY` set), with `roles/openrouter-reviewer.md`.
- If **neither** → single-model fallback (`roles/spec-validator.md` via `codex exec -`).

```
MAX_ROUNDS = consensus_rounds_flag (default 3, 0 disables)
round = 0
reviewer_prompt = sed "s|<spec_path>|$SPEC_PATH|g" roles/codex-reviewer.md

reviewers = []
if bash `command -v claude` nonempty:   reviewers += ["claude"]
if env OPENROUTER_API_KEY set:          reviewers += ["openrouter"]

if reviewers is empty:
  log WARNING "no external reviewer (claude / OPENROUTER_API_KEY); single-model fallback"
  result = bash: envsubst < roles/spec-validator.md | codex exec -
  → CONSENSUS or NEEDS_FIX (single round); goto Step 9

rounds = []
while round < MAX_ROUNDS:
  round += 1

  # 1. Each reviewer finds independently → union of findings JSON (same schema),
  #    tagged with its source. A reviewer erroring (no JSON, OpenRouter non-200)
  #    degrades to an empty approve for THIS round, logged — never aborts.
  all_findings = []
  for r in reviewers:
    all_findings += run_reviewer(r)   # claude -p  |  OpenRouter curl

  # 2. Codex self-assessment over the UNION (fresh codex exec -)
  assessment = bash:
    printf '%s\n\nSpec file: %s\n\nReviewer findings (union):\n%s' \
      "$(cat roles/codex-self-assessor.md)" "$SPEC_PATH" "$(json all_findings)" | codex exec -

  # 3. Consensus = every reviewer "approve" AND assessment.verdict == AGREE_PASS
  if all(f.summary == "approve" for f in all_findings) and assessment.verdict == AGREE_PASS:
    → CONSENSUS, exit loop

  # 4. Process via categorization (dedupe identical findings from >1 reviewer —
  #    stronger signal, note it, apply once)
  applied, rejected, needs_user = [], [], []
  for each finding in dedupe(all_findings):
    cat = assessment.categorization[finding.id]
    if cat == ACCEPT:        apply finding.recommendation to spec; applied.append(finding)
    elif cat == REJECT_PETTY: rejected.append((finding, reason))
    elif cat == NEEDS_USER:   needs_user.append(finding)

  print round summary: N applied, M rejected (reasons), K queued for user, per-reviewer counts
  rounds.append({all_findings, assessment, applied, rejected, needs_user})

  if needs_user not empty:
    numbered TUI prompt per issue with reviewer views; apply user decisions

  # 5. Oscillation detection
  if round >= 3 and hash(dedupe(all_findings)) == rounds[-3].findings_hash:
    → ESCALATE: "the models are stuck — your call"; print full rounds[]; break

if round == MAX_ROUNDS and not CONSENSUS:
  ESCALATE: "(A) approve as-is, (B) abort, (C) one more round"; print full rounds[]
```

Failure modes:
- **No external reviewer** (`claude` not on `$PATH` AND no `OPENROUTER_API_KEY`) → single-model `roles/spec-validator.md` via `codex exec -`, continues with a warning.
- **OpenRouter unavailable** (401 missing/invalid key, 402 no credits, 429 rate-limit, 5xx provider down) → drop the third reviewer that round, log the HTTP code, continue. Pin the exact model slug.
- **A reviewer's response has no JSON block** → extractor returns empty `approve` (logged, no-op). Persistent → escalate.
- **Models gang up on user intent** → `roles/codex-reviewer.md` / `roles/openrouter-reviewer.md` forbid proposing removal of unusual requirements; `roles/codex-self-assessor.md` mirrors the rule.
- **Petty disagreements** → reviewer prompts exclude style/formatting/word-choice; leaks → REJECT_PETTY.
- **Oscillation** → hash comparison between rounds N and N-2, escalation.

Output schema (defined identically by `roles/codex-reviewer.md` and `roles/openrouter-reviewer.md`):
```json
{
  "summary": "needs-attention | approve",
  "findings": [
    { "file": "<spec.md path>", "line_start": <int>, "line_end": <int>,
      "confidence": <0..1>, "recommendation": "<concrete change>" }
  ]
}
```

## Outputs

- `<spec-stem>/tasks.md` — **tracker** (at-a-glance): `## Needs your attention` (if any) + `## Tasks` checklist (`- [ ] TASK-n` per task). (Trivial single-file spec → `<spec>.md`.)
- `<spec-stem>/reference.md` — **plan body + context**: overview / requirements / `## Assumptions` (ranked, non-blocking) / risks / non-goals / **`## Task details`** (the `### TASK-n` blocks with `Done when:` proofs — what `/verify-done` + goal-prep read). Concise + DRY, lossless. Folds into `<spec>.md` for a trivial single-file spec.
- `<spec>.bak` — original before enrichment. Offered for deletion at step 10.

Git: `pre-blueprint: <name>` (snapshot before) and `blueprint: enrich <name>` (after step 6).

Phase 7.6 internals (per-round findings, applied/rejected/escalated, per-reviewer counts) live in memory, printed at round boundaries — no critique files. On failure/oscillation, the full round-by-round summary is dumped before escalation.

## Connections to other skills

- **Input:** typically after `/cleanup` (sectioned markdown without `[MISSING]`). A manually written spec is fine if structurally valid. Optionally preceded by `/extract-links`.
- **Upstream (project-level, orthogonal):** `mattpocock:grill-with-docs` owns `CONTEXT.md` (glossary). `/blueprint` does NOT touch `CONTEXT.md`; hard-to-reverse decisions are noted inline in `## Risks`, not in a `docs/adr/` tree.
- **Output (on disk):** the plan directory `<spec-stem>/` (`tasks.md` + `reference.md`), or `<spec>.md` for a trivial spec; original backed up to `<spec>.bak`, kept until step 10.
- **Output (optional, in tracker):** Step 10 offers a literal "type `/to-prd` next" if `mattpocock:to-prd` is installed at `~/.codex/skills/to-prd/`.
- **Downstream builders:** `mattpocock:tdd`, `codex exec` for autonomous, or manual implementation.
- **Cross-model dependency:** Phase 7.6 uses `claude -p` (npm `@anthropic-ai/claude-code`) and/or a diverse OpenRouter model (`OPENROUTER_API_KEY`). Without either — fallback to `roles/spec-validator.md` via `codex exec -`.

## Rules

### Commonality
The plan is a shared artifact. Downstream work (mattpocock:tdd, goal feature, manual builder) makes decisions from it. A placeholder, a vague `Done when:`, or a contradictory requirement → the next step works from a holey map.

### Prior commitment
In step 5 you committed to placeholder scan + consistency + ambiguity check + **Scope-cut audit (user-facing gate)**. In step 7 — `verify-spec.py`. In step 8 — the consensus loop (or fallback). Skipping any withdraws the basis for the final verdict.

### Authority (scope decisions belong to the user)
Tagging a requirement `[later]`, moving a feature into `Non-goals`, or dropping an edge case — these are scope decisions, not spec hygiene. The user wrote the input on purpose; v1-vs-deferred is theirs. The Scope-cut audit is a hard user-facing gate precisely so the model never makes this call alone.

### Social proof (cross-model rationale)
Phase 7.6 exists because single-model self-review is weaker. An independent reviewer (Claude via `claude -p`, plus an optional diverse third model from a different lab) catches issues the first biases past. A finding raised by more than one reviewer is a stronger signal. Skipping Phase 7.6 when a reviewer is available removes the only real basis to trust the plan beyond "Codex approved its own output".

## Self-check before delivering the result

Would this plan pass review by a senior engineer who has to build the system from it? Concretely:

- Does every task have a concrete `Done when:` shell proof (not "it works", not "manual check")?
- No placeholders (`TBD`, `...`, `[NEEDS CLARIFICATION]`, `<insert here>`)?
- **Was the step 5 Scope-cut audit run**, with every detected deferral (`[later]`, `Non-goals` items, dropped input features/edge cases) confirmed by the user via TUI prompt? No silent deferral.
- Were hard-to-reverse decisions noted inline in `## Risks` (one line each), not `docs/adr/` files?
- Is every task atomic — 1-3 files, single purpose, closeable by an independent worker without questions to the author?
- **Foundations first:** does the first task leave the project runnable/green (greenfield skeleton + smoke test, or brownfield baseline proof)? Is the harness in that task and reused — not buried later? Each area exactly once, prerequisites before dependents?
- **One attention surface:** are ALL blocking `❓ NEEDS YOU` in tasks.md `## Needs your attention` (each `→ blocks: TASK-n`) plus the HITL tasks — with NONE duplicated in reference.md (which carries only the ranked **non-blocking** `## Assumptions`)?
- **Checklist ↔ details:** is tasks.md `## Tasks` a checklist (one `- [ ] TASK-n` per task, bare ids, each area once), and does every checklist task have exactly one `### TASK-n` block in reference `## Task details` (and vice-versa)? Are `Done when:` proofs in `## Task details`?
- **Reference concise + DRY + lossless:** no fact in two sections; per-task specifics only in `## Task details`; near-duplicate prose/risks merged — yet nothing lost?
- Plan written as a flat `<spec-stem>/` directory (`tasks.md` checklist + `reference.md` body) — or a single `<spec>.md` if trivial; no nested subdirs?
- Did Phase 7.6 pass (or was it explicitly skipped with reasoning)?
- Coverage: does every Overview item have at least one task? Does every task track back to Overview / a requirement?
- Was the user offered keep-or-delete `<spec>.bak` at step 10?

If "no" on any item — redo, don't ship.
