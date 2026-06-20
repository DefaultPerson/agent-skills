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
allowed-tools: [Bash, Glob, Grep, Read, Edit, Write, Agent, AskUserQuestion]
---

# Blueprint

Turn a clean spec into a readable, implementation-ready **plan**: atomic vertical-slice tasks each with a `Done when:` shell proof, plain-language requirements, edge cases, ranked assumptions, and risks. The rigor lives in the proofs — not in ceremony.

> **Letter = spirit.** If a rule blocks you from reaching the goal it was
> written for, the rule is wrong, not the goal. Don't look for a wording
> loophole — ask what the rule is protecting, and protect that.

> **Was `/clarify`.** Renamed to `/blueprint` (it's a planning tool). `clarify` / `уточни спеку` still route here as aliases.

## Usage

```
/blueprint <spec.md> [--consensus-rounds N]
```

- `--consensus-rounds` defaults to 3. Set it to 0 to skip the cross-model consensus loop (Phase 7.6) — only internal validation runs.
- **Third reviewer (optional, opt-in):** if `OPENROUTER_API_KEY` is set, Phase 7.6 adds one diverse frontier model via OpenRouter (default `z-ai/glm-5.2`, override with `OPENROUTER_MODEL`) as an independent finder alongside Codex. No key → it stays Codex + Claude, no error.

## Weaknesses and when NOT to use

- **Slow and thorough — overkill for hour-long tasks.** Decomposition + Done-when proofs + edge cases + 3 consensus rounds (if codex is available) take 10-15 minutes. For smaller tasks, write the plan by hand.
- **Does not work on raw chat exports or unstructured notes.** The input spec must already be sectioned with `## ` (after `/cleanup`). Otherwise — abort.
- **Not suited for product-style PRDs.** This skill forces a `Done when:` shell proof per task; for product-management PRDs use `mattpocock:to-prd` (freeform success metrics).
- **Phase 7.6 consensus loop needs at least one external reviewer.** Best signal comes from the `codex` CLI on `$PATH` (npm `@openai/codex`), invoked as `codex review --uncommitted "<prompt>"`. Optionally a third model via OpenRouter (`OPENROUTER_API_KEY`). With **neither** available — fallback to internal validation (a single model reviewing its own output, weaker).
- **Not for autonomous orchestration.** The output has no `[P]` markers, Stages, or dependency graphs — the execute pipeline was removed from this repo in v2.0. Output is for `mattpocock:tdd` or manual work.

## How to do it wrong vs right

### Task proof (`Done when:`)

❌ **Wrong:** `Done when: the endpoint works.`
- "Works" — who decides?
- No command. Boolean (works / doesn't) — no UNKNOWN.

✅ **Right:** `Done when: \`curl -sw '%{http_code}' :8080/api/users -o /dev/null\` prints 200 in <200ms.`
- Concrete numbers, a runnable command.
- Tristate: PASS / FAIL / UNKNOWN (when the server isn't running).

### Task scope

❌ **Wrong:** `### TASK-1: Implement authentication system`
- Touches many files, multiple purposes, not verifiable with one command.

✅ **Right:** `### TASK-1: Create User model in src/models/user.py with email/password`
- 1 file, clear boundary, one deliverable.
- `Done when: \`python -c "from src.models.user import User; User(email='a@b',password='x')"\` runs clean.`

### Cross-model consensus disagreement

❌ **Wrong:** A reviewer returns "requirement X looks unusual, suggest removing it". I apply it — I remove it.
- The user added the requirement on purpose. Removing it "helped me faster" but stomped the user's intent.

✅ **Right:** Issue type = NEEDS_USER (the reviewer flagged it that way, or Claude self-assessor reclassified). AskUserQuestion with both views. The user decides.

### Implicit scope reduction

❌ **Wrong:** Input mentions "batch user creation" and "admin role for DELETE". Mid-decomposition I think "those feel like v2" — I tag them `[later]` and move on. Same for "rate limiting" → a `Non-goals` section, without asking.
- The user wrote those on purpose. Tagging them `[later]` silently == deleting a user-stated requirement. The builder skips them; the user finds out only on the final read.

✅ **Right:** Step 5 has a hard-gate Scope-cut audit. Anything tagged `[later]`, moved to `Non-goals`, or dropped from a task's coverage gets surfaced via batched AskUserQuestion **before** the spec is written. Per item: `Keep deferred` / `Include in v1` / `Drop entirely`. Nothing gets quietly downgraded.

## Writing style for the plan

> Sharpen/terminology/cross-ref rules borrowed from `mattpocock:grill-with-docs` (MIT). The "challenge the task" and "assumptions & open questions" moves are borrowed from [malakhov-dmitrii/fusion](https://github.com/malakhov-dmitrii/fusion) (MIT). Applies in step 2 (questioner) and steps 3-5 (decomposition / requirements / edge cases).

### Challenge the task before decomposing (multi-angle)

Before turning notes into tasks, spend one pass questioning the task itself — the first framing isn't always the right one:

- What if we **don't build this** at all (is the underlying need met another way)?
- What if we build a **much simpler** version (80% of value, 20% of the work)?
- Does the right shape **depend on a future plan** the input hints at?
- Which **scenarios** change the answer (scale, single-user vs multi-tenant, offline)?

If a cheaper or simpler framing is plausible, surface it in step 2 as a question — don't silently commit to the literal reading.

### Sharpen fuzzy language

When the input uses vague or overloaded terms ("user", "account", "system", "data"), propose a precise canonical term and ask which the user means. Push for precision until the next reader can't misread it.

❌ **Fuzzy:** "Users can manage their subscriptions"
✅ **Sharp:** "Subscription owners (Customer accounts) can cancel/resume their own subscriptions; admin operators can cancel/resume on behalf of any Customer."

### Be opinionated about terminology

Pick ONE canonical term per concept and keep it through the whole plan. If the input uses synonyms (user/account/principal), pick the most precise — usually the one mapping to a code type — and note the aliases in a brief "Terminology" preamble if the ambiguity is worth flagging.

### Keep requirements tight and plain

Each requirement is one plain sentence, tagged `[must]` / `[nice]` / `[later]` — no RFC-2119 `MUST/SHOULD/MAY` shouting, no forced `FR-NNN` ids (add light `R1`/`R2` ids only for big specs that need task↔requirement links). Describe WHAT the system does, not HOW. Details: `references/contracts.md`.

❌ **Ceremonial:** `FR-001: The auth middleware MUST verify the signature, check expiration, and return 401...`
✅ **Plain:** `- [must] Bad tokens (missing / expired / wrong signature) → 401.`

### Stress-test edge cases with concrete scenarios

Each edge case is a concrete input + expected output, written inline (`Edge: ...`). The next reader writes a test from it without asking what "invalid" means.

❌ **Abstract:** "Edge case: empty request body."
✅ **Concrete:** `Edge: POST /users with body {} (no email) → 400 {error:"email_required"}.`

### Cross-reference with code

If the codebase has paths/types matching spec terms, read them. If code says X and the spec says Y, surface the conflict in step 2 (questioner). The spec must agree with shipping code or explicitly call out the divergence.

❌ **Stale:** Spec describes `POST /users` accepting `{email, name}`; code already accepts `{email, name, phone}`. Plan written as-is.
✅ **Reconciled:** "Spec says POST {email, name}; code already accepts phone. Regression, or forgot phone?" — ask before proceeding.

### Vertical slices, not horizontal layers

Each task cuts through ALL relevant layers end-to-end (schema → API → UI → tests), not one layer. A finished slice is demoable on its own. Prefer many thin slices over few thick ones.

❌ **Horizontal:** TASK-1 "Add all DB columns"; TASK-2 "Add all API"; … Nothing demoable until task 3.
✅ **Vertical:** TASK-1 "Add email to User: column + API field + form + test"; TASK-2 "phone: same set."

### Behavioural `Done when:`, not procedural

The proof describes what the system DOES (observable through its interface), not HOW. The reader writes the test from it without reading implementation prose.

❌ **Procedural:** `Done when: middleware extracts the token, calls validateJWT(), returns 401.`
✅ **Behavioural:** `Done when: \`curl -H 'Auth: <expired>' :8080/me\` → 401 {error:"token_expired"}.`

### Surface assumptions & open questions

Put an **`## Assumptions & open questions`** section in the **reference file** (`<spec>.reference.md`); surface any *blocking* `❓ NEEDS YOU` items also in the tasks file's `## Open questions` so they can't be missed before execution. Borrowed from fusion. A planner can't verify everything; be honest about it instead of guessing silently:

- List each assumption with a confidence (high / medium / low) and what it's based on.
- Mark genuine human-decision points with `❓ NEEDS YOU:` — these are forks the model shouldn't pick alone.

```markdown
## Assumptions & open questions
- Assume Postgres (high — matches src/db).
- Assume JWT, not sessions (medium — input didn't say).
- ❓ NEEDS YOU: is DELETE admin-only? (input was ambiguous)
```

## Roles

Step 2 (questioner pattern) and the Phase 7.6 consensus loop (with fallback validator) — templates live in `roles/`:

- `roles/questioner.md` — format contract for AskUserQuestion in step 2 (not a subagent — a format spec). Includes the multi-angle challenge.
- `roles/codex-reviewer.md` — **full prompt** passed verbatim to `codex review --uncommitted` (Claude host) or `claude -p` (Codex host). Owns the adversarial role, substance criteria, user-intent preservation rule, and JSON output schema. Standalone — no template wrapping.
- `roles/openrouter-reviewer.md` — **full prompt** for the optional third reviewer (a diverse frontier model via OpenRouter). Same adversarial role + JSON schema; reviews the spec content passed in the request body.
- `roles/claude-self-assessor.md` — Phase 7.6 Claude self-assessment in a fresh subprocess (`claude -p`), categorizes the union of reviewer findings as ACCEPT / REJECT_PETTY / NEEDS_USER.
- `roles/spec-validator.md` — fallback used inside Phase 7.6 when NO external reviewer is available.

Substitutions:

| Variable | Source |
|---|---|
| `{spec_path}` | the spec file after step 6 (write) |
| `{round}` | round counter in Phase 7.6 (1, 2, 3) |
| `{spec_path}.bak` | original spec (pre-enrichment) for coverage check |
| `{codex_prompt}` | full text content of `roles/codex-reviewer.md` (entire file, passed as the review prompt) |

Invocations:
- **Codex adversarial review:** call `codex review --uncommitted` directly via Bash. Stable public dependency (`npm install -g @openai/codex`); no `codex-plugin-cc` runtime.
  ```bash
  command -v codex >/dev/null 2>&1 || { echo "codex CLI not installed"; exit 1; }
  PROMPT="$(cat skills/blueprint/roles/codex-reviewer.md)"
  OUTPUT="$(codex review --uncommitted "$PROMPT")"
  # Extract the last fenced JSON code block — the prompt instructs the model to emit findings there.
  FINDINGS="$(printf '%s' "$OUTPUT" | python3 -c '
import sys, re, json
text = sys.stdin.read()
matches = re.findall(r"```json\s*\n(.*?)\n```", text, re.DOTALL)
print(matches[-1] if matches else json.dumps({"summary":"approve","findings":[]}))
')"
  ```
  Output schema (controlled by `roles/codex-reviewer.md`): `{summary: "needs-attention"|"approve", findings: [{file, line_start, line_end, confidence, recommendation}]}`. No JSON block → falls back to an empty `approve` result (logged, treated as no-op).
- **OpenRouter third reviewer (optional):** only if `OPENROUTER_API_KEY` is set. The spec is a chat-API review, so pass the prompt + the spec content in the request body. Same JSON schema; same extractor.
  ```bash
  [ -n "${OPENROUTER_API_KEY:-}" ] || { echo "no OPENROUTER_API_KEY; skipping third reviewer" >&2; return 0; }
  OR_MODEL="${OPENROUTER_MODEL:-z-ai/glm-5.2}"                # primary
  OR_FALLBACK="${OPENROUTER_FALLBACK:-moonshotai/kimi-k2.6}"  # OpenRouter auto-routes to this if primary fails
  PROMPT="$(cat skills/blueprint/roles/openrouter-reviewer.md)
SPEC FILE ($spec_path):
$(cat "$spec_path")"
  resp="$(curl -sS --max-time 120 -w $'\n%{http_code}' \
    https://openrouter.ai/api/v1/chat/completions \
    -H "Authorization: Bearer $OPENROUTER_API_KEY" -H "Content-Type: application/json" \
    -H "X-Title: blueprint consensus" \
    -d "$(jq -nc --arg m "$OR_MODEL" --arg fb "$OR_FALLBACK" --arg c "$PROMPT" \
          '{model:$m, models:[$m,$fb], messages:[{role:"user",content:$c}], temperature:0.2}')")"
  http="${resp##*$'\n'}"; body="${resp%$'\n'*}"
  if [ "$http" = "200" ]; then
    TEXT="$(printf '%s' "$body" | jq -r '.choices[0].message.content')"
    # same python extractor as Codex pulls the last ```json``` block from $TEXT
  else
    echo "OpenRouter HTTP $http — dropping third reviewer this round" >&2   # graceful degrade
  fi
  ```
- **Claude self-assessment:** Bash subprocess `claude -p` with the prompt from `roles/claude-self-assessor.md` plus the union of reviewer findings JSON pasted in.
- **Fallback validator (no external reviewer):** `Agent(subagent_type="Explore", prompt=substitute("roles/spec-validator.md", vars))`.

## What the skill does (step by step)

1. **Read and analyze the spec.** Validate (markdown, has `## ` headers, no cleanup markers `[MISSING]`/etc), classify type (product / technical / small), scan the codebase if present, flag `[NEEDS CLARIFICATION]` items. Also sweep `docs/adr/*.md` if it exists — extract slugs and titles into an in-memory list of "established decisions" for Phase 5 conflict detection. Skip silently if `docs/adr/` is absent.
2. **Challenge + ask** (hard gate). Run the multi-angle challenge (don't-build / simpler / future-dependent / scenarios). Then ask the user what's unclear — max 5 questions via AskUserQuestion, format in `roles/questioner.md`. If the spec is already clear and the framing is sound — skip.
3. **Decompose into atomic tasks.** Format adapts to type — details in `references/task-format.md`. Main rule: each task touches 1-3 files (a vertical slice) and has a `Done when:` line with a runnable shell proof. No `[P]` markers, Stages, `AC-N.N`, or `Given/When/Then` — those are gone.
4. **Pin requirements & contracts.** Plain sentences tagged `[must]`/`[nice]`/`[later]` (light `R1`/`R2` ids only if a big spec needs links). Skip if the spec is small or single-component. Details in `references/contracts.md`.
5. **Self-review checklist.** Placeholder scan, internal consistency, ambiguity check, **ADR candidate detection**, and a **hard-gate Scope-cut audit (user-facing)**.

   **ADR candidate detection** (runs before the Scope-cut audit). Scan the in-memory plan (Implementation Decisions, Requirements, Tasks with architectural impact) for decisions that pass ALL THREE criteria from `references/adr-format.md`:

   1. **Hard to reverse** — DB schema change, public API contract, infra/auth/messaging choice, security boundary, major dependency lock-in.
   2. **Surprising without context** — a future reader looking at just the code will wonder "why this way?"
   3. **Real trade-off** — an explicit alternative was considered and rejected.

   Build a candidate list (max 5 — cut-off to prevent over-detection). For each, score against the 3 criteria; pass only if all three are true. Surface the 3 highest-reverse-cost passes via AskUserQuestion (one per candidate, single-select):
   - **Create ADR-NNNN: `<short title>`** — write minimal ADR per `references/adr-format.md` (1-3 sentences) at `docs/adr/NNNN-slug.md`. NNNN = max existing + 1, four-digit padded. Create `docs/adr/` lazily if absent.
   - **Already documented (specify ADR-MMMM)** — the user names the existing ADR; if the plan contradicts it, flag in the same step as a conflict question (Keep / Revise to match ADR / Supersede ADR / Discuss).
   - **Skip** — ignore the candidate.

   Additionally, scan the plan against the Phase 1 ADR sweep list. If any requirement/task contradicts an established ADR, surface it as a conflict question regardless of the 3-criteria filter.

   After ADR decisions are applied, proceed to the **Scope-cut audit (user-facing)**. The audit scans the in-memory plan for deferral signals:
   - Requirements tagged `[later]`, or `[must]`/`[nice]` carrying phrases `(v2)`, `(future)`, `(deferred)`, `(later)`, `(stretch goal)`, `(MVP only)`, `(out of scope for now)`, `(not for now)`.
   - Items in a `Non-goals` section that map back to anything mentioned in the input.
   - Features / endpoints / edge cases present in the input with no backing task or silently dropped from a task's coverage.

   If any signal is found, surface a batched AskUserQuestion (multiSelect=false, one question per item, up to 4 per call — batch into multiple calls if more) with options `Keep deferred (current)` / `Include in v1` / `Drop entirely` / `Drop and document in .out-of-scope/`. Apply user decisions to the in-memory plan. For `Drop and document`, write `.out-of-scope/<concept>.md` per `references/out-of-scope-format.md` (or append). Loop back to step 3/4 if scope changes require re-decomposition. NEVER write to disk while scope cuts are unconfirmed. If the audit finds nothing — gate silently passes.

   Phase 1 also reads existing `.out-of-scope/*.md` if present. If the input mentions a concept matching a prior rejection, surface in step 2 so the user can confirm the rejection still stands or reconsider (in which case the matching `.out-of-scope/` file is removed).
6. **Write the plan as TWO files** (context economy — executors/sub-agents/`/verify-done`/goal-prep load only the lean tasks file, not the whole plan). Back up the original (`<spec>.bak`), then write:
   - **`<spec>.md` — tasks file (PRIMARY, executable, trackable):** a `> Context: see <spec>.reference.md` pointer line; a `## Open questions` block IF blocking `❓ NEEDS YOU` items remain; `## Tasks` where each task is **self-sufficient** (title, `**Files**`, `Done when:` shell proof, inline `Edge:`). This is the downstream contract — native `/goal`, per-stage sub-agents, `/verify-done`, and goal-prep all read THIS file.
   - **`<spec>.reference.md` — reference (read-once context):** `## Overview` narrative, full `## Requirements` (`[must]/[nice]/[later]` + rationale), Terminology, `## Assumptions & open questions` (ranked), `## Risks`, ADR links.
   - **Self-sufficiency rule:** a task must be executable from the tasks file ALONE (the `Done when:` IS the acceptance); the reference is only "why". Cross-ref a task → a requirement by light id (`R1`) only when it genuinely cites one.
   - **Threshold:** a trivial / single-component spec may stay one file (fold the reference sections into `<spec>.md`); split when non-trivial. Downstream readers use a resolver: prefer `<spec>.md` as the tasks file; if no `<spec>.reference.md` exists, treat `<spec>.md` as both.

   Template structures: see `references/task-format.md`.
7. **Mechanical validation.** `python3 scripts/verify-spec.py <spec>`. FAIL → fix and re-run. (Style warnings about old ceremony are non-blocking but worth clearing.)
8. **Cross-model consensus loop (Phase 7.6).** External reviewer(s) find, Claude self-assesses, iterate until CONSENSUS or max rounds. Details — next section. Can be skipped with `--consensus-rounds 0`.
9. **Approval gate.** Summary report + AskUserQuestion (Approve / Modify / Questions). After approval, proceed to step 10.
10. **Backup disposition + downstream offer.** Spec is approved — `<spec>.bak` is no longer load-bearing. First AskUserQuestion (backup):
    1. **Delete `<spec>.bak`** (default, recommended) — `rm <spec>.bak`. Rollback still possible via `git checkout HEAD -- <spec>` (the `pre-blueprint: <name>` snapshot from step 6 holds the original).
    2. **Keep `<spec>.bak`** — for further iteration or an extra safety net.

    Then, **only if `/to-prd` is installed** (Glob check: `~/.claude/skills/to-prd/SKILL.md` exists), a second AskUserQuestion (downstream):
    1. **Stay local** (default) — `/clear` and continue manually, with `mattpocock:tdd` on the file, or the Claude Code goal feature.
    2. **Publish to issue tracker via `/to-prd`** — print the literal instruction `Type /to-prd next to wrap this spec as a PRD and publish.` Do NOT auto-invoke; the user types `/to-prd` themselves.

    If `/to-prd` is not installed, skip the downstream question — print `"Plan approved. /clear before continuing."`.

The old "Execution Order" section (Stages, [P] markers, dependency graph for parallel spawn) is GONE in v2.0. It existed for the execute orchestration, which no longer ships.

## Phase 7.6 — Cross-model consensus loop

After steps 6-7 (write plan + verify-spec.py mechanical check), the convergence loop runs. Step 8 in the walkthrough is Phase 7.6.

Each round, every **available** external reviewer produces findings independently; Claude (in a fresh `claude -p` subprocess) triages the **union**. Independent finders, one triager. Reviewers:

- **Codex** — `codex review --uncommitted` (if `codex` on `$PATH`). Prompt: `roles/codex-reviewer.md`.
- **OpenRouter third reviewer** — a diverse frontier model (default `z-ai/glm-5.2`) via the chat API (if `OPENROUTER_API_KEY` is set). Prompt: `roles/openrouter-reviewer.md`.
- If **neither** is available → single-model fallback (`roles/spec-validator.md`).

```
MAX_ROUNDS = consensus_rounds_flag (default 3, 0 disables)
round = 0

reviewers = []
if bash `command -v codex` nonempty:          reviewers += ["codex"]
if env OPENROUTER_API_KEY set:                reviewers += ["openrouter"]

if reviewers is empty:
  log WARNING "no external reviewer (codex / OPENROUTER_API_KEY); single-model fallback"
  result = Agent(subagent_type="Explore",
                 prompt=substitute("roles/spec-validator.md", {spec_path, spec_path_bak}))
  → CONSENSUS or NEEDS_FIX (single round only); goto Step 9

# Spec is in the working tree, NOT committed. `codex review --uncommitted`
# reads staged/unstaged/untracked; the OpenRouter call reads the file content.

rounds = []
while round < MAX_ROUNDS:
  round += 1

  # 1. Each reviewer finds independently → list of findings JSON (same schema),
  #    tagged with its source. A reviewer erroring (codex missing JSON, OpenRouter
  #    non-200) degrades to an empty approve for THIS round, logged — never aborts.
  all_findings = []
  for r in reviewers:
    all_findings += run_reviewer(r)   # codex review --uncommitted  |  OpenRouter curl

  # 2. Claude self-assessment over the UNION (fresh subprocess)
  assessment = bash: claude -p < (
    read("roles/claude-self-assessor.md")
    + "\n\nSpec file: " + spec_path
    + "\n\nReviewer findings (union):\n" + json(all_findings))

  # 3. Consensus = every reviewer "approve" AND assessment.verdict == AGREE_PASS
  if all(f.summary == "approve" for f in all_findings) and assessment.verdict == AGREE_PASS:
    → CONSENSUS, exit loop

  # 4. Process findings via assessment categorization (dedupe identical findings
  #    raised by >1 reviewer — that's a STRONGER signal, note it, apply once)
  applied, rejected, needs_user = [], [], []
  for each finding in dedupe(all_findings):
    cat = assessment.categorization[finding.id]
    if cat == ACCEPT:        apply finding.recommendation to spec; applied.append(finding)
    elif cat == REJECT_PETTY: rejected.append((finding, reason))
    elif cat == NEEDS_USER:   needs_user.append(finding)

  print round summary: N applied, M rejected (reasons), K queued for user, per-reviewer counts
  rounds.append({all_findings, assessment, applied, rejected, needs_user})

  if needs_user not empty:
    AskUserQuestion with the issues + reviewer views; apply user decisions

  # 5. Oscillation detection
  if round >= 3 and hash(dedupe(all_findings)) == rounds[-3].findings_hash:
    → ESCALATE: "the models are stuck — your call"; print full rounds[]; break

if round == MAX_ROUNDS and not CONSENSUS:
  ESCALATE: "(A) approve as-is, (B) abort, (C) one more round"; print full rounds[]
```

Failure modes:
- **No external reviewer** (`codex` not on `$PATH` AND no `OPENROUTER_API_KEY`) → single-model `roles/spec-validator.md`, continues with a warning.
- **Spec not in a git repository** → `codex review --uncommitted` needs git; if outside a repo, drop Codex (OpenRouter still works — it reads the file). If that leaves no reviewer, fall back to spec-validator.
- **OpenRouter unavailable** (missing/invalid key → 401, no credits → 402, rate-limit → 429, provider down → 5xx) → drop the third reviewer for that round, log the HTTP code, continue with whoever's left. Pin the exact model slug so a future GLM/Kimi version doesn't silently change the reviewer.
- **A reviewer's response has no JSON block** → extractor returns `{"summary":"approve","findings":[]}` (logged, no-op). Persistent across rounds → escalate.
- **Models gang up on user intent** → `roles/codex-reviewer.md` / `roles/openrouter-reviewer.md` forbid proposing removal of unusual requirements; `roles/claude-self-assessor.md` mirrors the rule when categorizing.
- **Petty disagreements** → reviewer prompts exclude style/formatting/word-choice; leaks → REJECT_PETTY, logged, not applied.
- **Oscillation** → hash comparison between rounds N and N-2, escalation.

Output schema (defined by `roles/codex-reviewer.md` and `roles/openrouter-reviewer.md` identically):
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

- `<spec>.md` — the **tasks file** (primary): overwrites the original path; the lean executable/trackable artifact (`## Tasks` + blocking `## Open questions`). Downstream reads this.
- `<spec>.reference.md` — the **reference**: `## Overview` / `## Requirements` / `## Assumptions & open questions` / `## Risks` / ADR links. Omitted for a trivial single-file spec.
- `<spec>.bak` — original before enrichment. Created in step 6, lives through Phase 7.6, offered for deletion at step 10. If deleted, rollback goes through `git checkout HEAD -- <spec>` against the `pre-blueprint: <name>` snapshot.

Git: `pre-blueprint: <name>` (snapshot before) and `blueprint: enrich <name>` (after step 6).

Phase 7.6 internals (per-round findings, applied/rejected/escalated breakdown, per-reviewer counts) live in memory and are printed to stdout at round boundaries — no critique files written. On failure/oscillation, the full round-by-round summary is dumped before user escalation.

## Connections to other skills

- **Input:** typically after `/cleanup` (sectioned markdown without `[MISSING]` markers). A manually written spec is also fine if structurally valid. Optionally preceded by `/extract-links`.
- **Upstream (project-level, orthogonal):** `mattpocock:grill-with-docs` for project-wide domain modelling — it owns `CONTEXT.md` (glossary) and general ADR creation. `/blueprint` reads existing `docs/adr/*.md` to respect prior decisions but does NOT touch `CONTEXT.md`. ADR offers in Phase 5 are scoped to decisions surfaced *by the spec being planned*.
- **Output (on disk):** the **tasks file** `<spec>.md` replaces the original (+ a `<spec>.reference.md` for context); `.bak` kept until step 10; new ADRs (if approved in Phase 5) land in `docs/adr/`.
- **Output (optional, in tracker):** Step 10 offers a literal "type `/to-prd` next" instruction if `mattpocock:to-prd` is installed.
- **Downstream builders:** `mattpocock:tdd` (RED-GREEN-REFACTOR), Claude Code goal feature (autonomous), or manual implementation.
- **Cross-model dependency:** Phase 7.6 uses `codex review --uncommitted` ([codex CLI](https://github.com/openai/codex)) and/or a diverse OpenRouter model (`OPENROUTER_API_KEY`). Without either — graceful fallback to `roles/spec-validator.md`.

## Rules

### Commonality
The plan is a shared artifact. Downstream work (mattpocock:tdd, goal feature, manual builder) makes decisions from it. If you let a placeholder through, leave a vague `Done when:`, or fail to resolve a contradictory requirement — the next step works from a holey map. Not "helping faster" — breaking the shared work.

### Prior commitment
In step 5 (self-review) you committed to placeholder scan + consistency + ambiguity check + **Scope-cut audit (user-facing gate)**. In step 7 — `verify-spec.py`. In step 8 — the consensus loop (or fallback). Skipping any step withdraws the basis for the final verdict the user acts on.

### Authority (scope decisions belong to the user)
Tagging a requirement `[later]`, moving a feature into `Non-goals`, or dropping an edge case from a task's coverage — these are scope decisions, NOT cleanup or "spec hygiene". The user wrote the input on purpose; deciding what's in v1 vs deferred is theirs. The Scope-cut audit in step 5 is a hard user-facing gate precisely so the model never makes this call alone. "It looks unconventional" / "v2 would be cleaner" / "the user probably didn't mean it" are not valid reasons to silently downgrade — surface it.

### Social proof (cross-model rationale)
Phase 7.6 exists because single-model self-review is weaker. An independent reviewer (Codex, plus an optional diverse third model from a different lab) catches issues the first biases past. A finding raised by more than one reviewer is a stronger signal. If you "skip" Phase 7.6 when a reviewer is available, you remove the only real basis to trust the plan beyond "Claude approved its own output".

## Self-check before delivering the result

Would this plan pass review by a senior engineer who has to build the system from it? Concretely:

- Does every task have a concrete `Done when:` shell proof (not "it works", not "manual check")?
- No placeholders (`TBD`, `...`, `[NEEDS CLARIFICATION]`, `<insert here>`)?
- **Was the step 5 Scope-cut audit run**, with every detected deferral (`[later]`, `Non-goals` items, dropped input features/edge cases) confirmed by the user via AskUserQuestion? No silent deferral.
- **Was the step 5 ADR candidate detection run?** Hard-to-reverse + surprising + real-trade-off decisions surfaced (max 3); existing ADRs respected or conflicts flagged.
- Is every task atomic — 1-3 files, single purpose, closeable by an independent worker without questions to the author?
- Does the **reference file** carry an honest `## Assumptions & open questions` (ranked), with blocking `❓ NEEDS YOU` also surfaced in the tasks file's `## Open questions`?
- Two files written — `<spec>.md` (tasks, self-sufficient) + `<spec>.reference.md` (context) — or one file only if the spec was trivial?
- Did Phase 7.6 pass (or was it explicitly skipped with reasoning)?
- Coverage: does every Overview item have at least one task? Does every task track back to Overview / a requirement?
- Was the user offered keep-or-delete `<spec>.bak` at step 10?

If "no" on any item — redo, don't ship.
