---
name: goal-prep
description: >
  Compile a charter for Claude Code's native /goal command. Runs an
  Intake Compiler (11 fields), a diagnostic ladder (6 questions, in 3
  batches), classifies the goal, seeds per-kind anti-patterns, and
  emits a copy-pasteable native /goal command pointing at the on-disk
  charter (anti-patterns + completion audit live in the charter file).
  Strictly non-execution: never performs the user's requested work,
  never reads implementation files, never browses reference repos.
  Triggers: "goal-prep", "/goal-prep", "prepare goal", "intake",
  "compile goal charter", "подготовка цели", "интейк", "прогрев цели".
allowed-tools: Bash, Glob, Grep, Read, Edit, Write, AskUserQuestion
---

# /goal-prep

Companion to Claude Code's native `/goal`.
Adapted from `tolibear/goalbuddy` `$goal-prep` (MIT). Same architectural
strut: prep is a charter compiler, never a lightweight executor.

## Why the on-disk charter pattern

Native `/goal <condition>` is a Stop-hook wrapper with a Haiku evaluator
that runs after every turn. The evaluator sees **only conversation
context** — files on disk are invisible to it. So the **outcome
predicates** (the conditions the evaluator checks) must live in the
`/goal` condition string itself.

Anti-patterns, intake summary, and the full audit table, by contrast,
are **main-model discipline** — not gates the evaluator enforces. They
live in `goal.md` on disk, and the `/goal` condition tells the main
model to `Read .ags/<slug>/goal.md first` so they enter the model's
context on turn 1 via the Read tool. No paste of a heavy preamble is
needed (and pre-v0.3.3 versions of this skill that did paste one were
duplicating goal.md content into conversation for no extra evaluator
gain).

## Invocation boundary — STRICT

During a `/goal-prep` turn, do **not** perform the user's requested work,
even if the work looks read-only, preparatory, or obviously useful.

Forbidden actions during prep:

- Reading implementation files (`src/`, `lib/`, `app/`, etc.) for content.
- Browsing reference repos linked from the user's request.
- Running linters, test runners, or build commands.
- Generating design plans, images, or assets.
- Calling other skills the user mentioned ("use the taste skill", "refresh X").
- Pre-editing any file outside the charter directory.

Allowed actions:

- Reading `README.md`, `package.json`, `pyproject.toml`, `Cargo.toml`,
  `go.mod`, `CLAUDE.md`, `AGENTS.md` at the **repo root only**, for shape
  detection — not content for the task.
- Reading a **plan/spec file handed in as the goal input** — a `/blueprint`
  tasks file (`<spec-stem>/tasks.md`, or a single `<spec>.md`) via `--from`
  or named in the request, and its optional `reference.md`. That's the goal's specification, not
  implementation code — reading it is intake, not execution (see Phase 5.1).
- Asking diagnostic intake questions via `AskUserQuestion`.
- Creating only `<cwd>/.ags/<slug>/{goal.md, run.txt, notes/}`.
- Printing the copy-clear-paste flow + native `/goal <condition>` line.

If the user names another skill or tool, **record it in the charter** under
`intake.existing_plan_facts`. Do not load the skill, do not browse the repo,
do not generate the assets.

## Phases

### Phase 0.5 — Objective length validation

Before the Intake Compiler, validate the raw user input:

```bash
chars=$(printf '%s' "$ARGS" | wc -m)
if [ "$chars" -eq 0 ]; then
    echo "goal objective must not be empty"; exit 1
fi
if [ "$chars" -gt 4000 ]; then
    cat <<EOF
Goal objective is $chars characters; native /goal hard-rejects above
4000. Two ways out:
  1. Tighten the prompt to its essence (anti-patterns & details live
     in the charter goal.md, not in the /goal condition itself).
  2. Stash the long version in a file and pass it to goal-prep:
       /goal-prep --from docs/goal.md
     The validator will read its '## Original Request' field.
EOF
    exit 1
fi
```

The 4000-char ceiling is **upstream**, not ours: Claude Code's `/goal`
enforces it (per https://code.claude.com/docs/en/goal,
`MAX_OBJECTIVE_CHARS = 4000`); openai/codex's `/goal` uses the same
constant (`MAX_THREAD_GOAL_OBJECTIVE_CHARS`). We mirror it at intake so
the run.txt we emit always fits. Long objectives are also usually an
architectural smell — anti-patterns/audit/evidence belong in `goal.md`,
not in the one-line condition the evaluator sees.

When the user passed `--from <path>/goal.md`, this validation runs
against the file's `## Original Request` field instead of `$ARGS`.

### Phase 0.55 — Cross-LLM review availability check

Between length validation and intake, ask whether to include a
cross-LLM adversarial-review step in the charter. The hook calls the
*other* LLM's CLI (the one this skill is not running under) to get a
second opinion on the working-tree diff before completion.

```bash
if command -v codex >/dev/null 2>&1; then CODEX_ON_PATH=1; else CODEX_ON_PATH=0; fi
```

This Claude Code variant of the skill uses `codex review --uncommitted`
as the cross-LLM hook (the inverse Codex-side variant under
`skills-codex/goal-prep/SKILL.md` uses `claude -p` instead).

Ask:

```
AskUserQuestion({
  questions: [{
    question: "Include `codex review --uncommitted` as a pre-completion step in the goal charter? Runs an adversarial code review via the codex CLI (a different model) against the working-tree diff before declaring the goal complete. Requires the codex CLI on PATH.",
    header: "Cross-LLM review",
    multiSelect: false,
    options: [
      // First option is Recommended based on CODEX_ON_PATH.
      // If detected (=1) → "Yes ... (Recommended)" first.
      // If not detected (=0) → "No ... (Recommended)" first.
      {label: <"Yes — include codex review hint (Recommended)" if detected else "No — skip codex review (Recommended)">,
       description: "Charter ## Adversarial Review will contain Step 1 (audit table) + Step 2 (codex pass)."},
      {label: <opposite>,
       description: "Charter ## Adversarial Review contains only Step 1 (audit table)."},
      {label: "What is codex?",
       description: "Show install info and re-ask."}
    ]
  }]
})
```

If user picks "What is codex?", print:

```
codex is OpenAI's terminal coding agent (npm i -g @openai/codex). If
installed and authenticated, `codex review --uncommitted` (run via
Bash) does a second-opinion review with a different model, catching
what the main /goal model misses. The slash form `/codex:adversarial-
review` has disable-model-invocation: true, which blocks the Skill
tool from invoking it inside other skills; the CLI has no such gate.
```

Then re-ask the same AskUserQuestion.

Store decision in `intake.cross_llm_review_enabled: true | false`.
Phase 8.5 reads this flag to conditionally include Step 2.

### Phase 1 — Intake Compiler (silent)

Privately translate the user's input into the 11 intake fields. See
`references/intake-compiler.md` for the protocol. Do not dump the intake to
the user.

### Phase 3 — Diagnostic ladder

6 questions in 3 `AskUserQuestion` batches (1 → 2 → 3). See
`references/diagnostic-ladder.md` for the exact `AskUserQuestion`
invocations, option labels, and descriptions.

- **Batch 1** (Q1 alone): intent reflection. If the user picks "Outcome
  is different", abort Phase 1 and re-run the Intake Compiler against the
  new wording.
- **Batch 2** (Q2 + Q3): success proof + scope/non-goals.
- **Batch 3** (Q4 + Q5 + Q6): authority + handling + heads-up.

Skip the ladder if:

- User passed `--defaults` — use all Recommended options.
- User passed `--from <path/to/goal.md>` — load existing goal.md and skip
  to Phase 5 (slug + dir already implied).
- User input was already specific enough to answer the 5 ladder questions
  inline (e.g. "find 5 P1 bugs in checkout flow before May 13 launch,
  mobile view, ignore Stripe test-mode warning"). Run the Intake Compiler
  anyway but skip the ladder.

### Phase 4 — Classify

Set `goal.kind` (recorded in the charter, NOT in state.yaml — we don't
write one):

- `specific` — clear single outcome, evidence sufficient, scope bounded.
- `open_ended` — long-horizon, multi-tranche, exploration-heavy. Note
  for the user that native /goal is inline-only; long-horizon cadence
  means re-running /goal-prep or resuming the session with
  `claude --resume` manually.
- `existing_plan` — user provided a plan; preserve verbatim in
  `intake.existing_plan_facts`.
- `recovery` — fix something broken.
- `audit` — read-only review; native /goal condition should reflect
  "no edits, document findings only".

### Phase 5 — Slug + directory

Derive slug from `intake.interpreted_outcome` with this shell snippet:

```bash
slug=$(printf '%s' "$INTERPRETED_OUTCOME" \
    | tr '[:upper:]' '[:lower:]' \
    | sed 's/[^a-z0-9]/-/g; s/--*/-/g; s/^-//; s/-$//' \
    | cut -c1-40)
```

**Charter location.** Default is `<cwd>/.ags/<slug>/` — a repo-root
dotfile dir, separate from Claude Code's own `.claude/`. User can
commit it (`git add .ags/<slug>/goal.md`) if the goal is part of the
project history; otherwise add `.ags/` to `.gitignore`.

**Backward compat (v0.3.2 path move).** If `<cwd>/.ags/<slug>/` does
not exist but `<cwd>/.claude/ags/<slug>/` does (legacy v0.3.1 path),
treat it as the existing slug for the prompt below — surface its path
in the question. On "Resume existing" use the old path in place; on
"Archive and recreate" or "Fork", move/create under the new `.ags/`
path.

If a charter for `<slug>` exists at either path, ask:

```
AskUserQuestion({
  questions: [{
    question: "A charter for slug `<slug>` already exists at <existing-path>. How to handle?",
    header: "Slug exists",
    multiSelect: false,
    options: [
      {label: "Resume existing (Recommended)", description: "Re-use the existing goal.md as the base; refresh intake fields from this run if they changed."},
      {label: "Archive and recreate", description: "Move existing to `.ags/_archive/<slug>-<timestamp>/`, then create fresh under `.ags/<slug>/`."},
      {label: "Fork to <slug>-2", description: "Keep existing untouched; create a sibling slug under `.ags/<slug>-2/`."}
    ]
  }]
})
```

Create directory + empty `notes/` for future user artifacts.

### Phase 5.1 — Derive completion from a `/blueprint` plan (when applicable)

If the goal input is a `/blueprint` **tasks file** — passed via `--from <spec-stem>/tasks.md` (or `<spec>.md`), or named in `intake.existing_plan_facts` — detect it **structurally**: the file contains `### TASK-{N}` headers AND `Done when:` lines (don't trigger on a lone keyword). Reading this plan file is intake, not execution — it's the goal's specification.

When detected:

- Set `intake.completion_proof` = "every task's `Done when:` proof passes (each PASS — none FAIL/UNKNOWN) and every `[must]` requirement is satisfied", reusing blueprint's **PASS / FAIL / UNKNOWN** vocabulary (`skills/blueprint/references/task-format.md`).
- Capture one audit row per `### TASK-{N}` (Requirement = task title, Evidence = its `Done when:` command) — Phase 8.5 pre-fills the audit table from these.
- Read the **tasks file** (`<spec-stem>/tasks.md`, or `<spec>.md`) for the proofs; if a sibling `reference.md` exists you may read it for non-goals/context, but completion comes from the tasks file's `Done when:` lines — never from the implementation the tasks point at.
- If the tasks file has a **`## Needs your attention`** block, lift its blocking `❓ NEEDS YOU` items into `intake.existing_plan_facts` and append "resolve all `## Needs your attention` items before declaring done" to `completion_proof` — they are gating preconditions, not optional. Use the **`## Task index`** order (foundations-first) as the suggested execution order; do TASK-1's runnable/green baseline before anything that builds on it.

This makes the charter's completion gate an objective projection of the plan, not hand-written prose. (Non-blueprint goals keep deriving `completion_proof` from intake as before.)

### Phase 6 — Write `goal.md` + `run.txt`

Copy `templates/goal.md`, fill placeholders with intake fields,
anti-patterns block, and the Adversarial Review block from Phase 8.5.
Write `<slug-dir>/run.txt` with the one-line `/goal` command so the
user can re-issue it later without re-running `/goal-prep`.

Write atomically: temp file in the same directory + `mv` to target
(POSIX `mv` is atomic on the same filesystem):

```bash
tmp=$(mktemp -p "${SLUG_DIR}" .run.XXXXXX)
printf '%s' "/goal $CONDITION, or stop after $MAX_TURNS turns" > "$tmp"
mv "$tmp" "${SLUG_DIR}/run.txt"
```

**Do not write `state.yaml` or `.lock`.** Native /goal reads neither.
The charter (`goal.md`) and `run.txt` are the only persistent artifacts.

(Pre-v0.3.3 also wrote `<slug-dir>/preamble.md` — a paste-ready copy
of a heavy Phase 9 preamble that duplicated `goal.md` content. v0.3.3
dropped it: the `/goal` condition emitted by Phase 9 now itself
instructs the main model to `Read .ags/<slug>/goal.md`, so a separate
preamble file is redundant. Existing `preamble.md` files from older
runs are left untouched on disk.)

### Phase 8 — Anti-patterns seed

Concatenate into `goal.md ## Non-Negotiable Constraints`:

1. Always: `templates/anti-patterns/base.md`.
2. Kind-specific layer (one of):
   - QA detected → `templates/anti-patterns/qa.md`
   - Refactor detected → `templates/anti-patterns/refactor.md`
   - Greenfield detected → `templates/anti-patterns/greenfield.md`

Detect via keywords in `intake.interpreted_outcome`:

- `bug|hunt|qa|test|broken|issue|p1|p2|repro` → qa
- `refactor|extract|move|rename|cleanup|dedupe` → refactor
- `build|new|design|create from scratch|greenfield|launch|mvp` → greenfield
- Else → base only.

3. **Per-stage verification cadence (always — especially for blueprint/multi-stage goals).**
   Append this rule to `## Non-Negotiable Constraints`:
   > After each completed stage/task, run its `Done when:` proof and a light self-review
   > **before** advancing to the next — do not batch verification to the end.

   And a hand-off line:
   > End-of-goal acceptance: hand the finished work to `/verify-done` for the tiered gate
   > (conformance + scenarios + quality).

   goal-prep only **writes** these as charter rules; the native `/goal` main model enforces
   them at execution time. (Per-stage check is lightweight — one task's `Done when:`; `/verify-done`
   is the heavy end gate. goal-prep is non-execution and runs neither.)

User may edit `## Non-Negotiable Constraints` afterwards; the seed is just
a starting point.

### Phase 8.5 — Inject Adversarial Review instruction

Write the `## Adversarial Review` section into the emitted `goal.md`.
The section has up to two steps; **Step 2 is conditional** on
`intake.cross_llm_review_enabled` (set at Phase 0.55):

1. **Structured completion audit table** — ALWAYS included. One row per
   requirement derived from `intake.completion_proof`; each row requires
   concrete evidence (file:line, command output, or commit hash) plus a
   status (Complete / Partial / Missing). Audit fails if any row is
   Partial or Missing.

2. **Adversarial review pass** — run via Bash:
   `codex review --uncommitted "<prompt>"` on the dirty diff; review
   findings explicitly, no auto-apply. CLI used instead of the
   `/codex:adversarial-review` slash command because the slash has
   `disable-model-invocation: true` — main model under native `/goal`
   cannot invoke it via Skill tool. CLI has no such gate.
   **Included only if `intake.cross_llm_review_enabled == true`.** If the
   user opted out at Phase 0.55, Step 2 is omitted from `goal.md`.

Pre-fill the audit table: if **Phase 5.1** derived rows from a `/blueprint`
plan, use **one row per `### TASK-{N}`** (Requirement = task title, Evidence =
its `Done when:` command); otherwise one row per requirement derivable from the
intake. Leave the Status column blank — the main model under native /goal fills
Evidence/Status when audit time comes; until a row has concrete evidence and a
`Complete` status it counts as failing (a blank or non-`Complete` status never
passes — mirrors blueprint's UNKNOWN≠PASS rule).

The `/goal` condition emitted by Phase 9 instructs the main model to
`Read .ags/<slug>/goal.md first`, so the anti-patterns and audit table
land in conversation context via that Read on turn 1. The evaluator
sees the condition itself (which lists the outcome predicates) every
turn.

Pattern source: `tolibear/goalbuddy` T999 completion audit (MIT).

### Phase 9 — Emit copy-clear-paste flow + `/goal` command, then exit

Print **exactly** (with substitutions), then return without further
AskUserQuestion — the user takes it from here. **Step order matters**:
the /goal command is on screen NOW; `/clear` would wipe it before the
user could copy. Copy first, then /clear, then paste.

```text
─── DONE — DO THESE THREE STEPS, IN ORDER ───

1. Copy this /goal command to your clipboard:

   /goal <condition>, or stop after 20 turns

2. Type /clear (the conversation gets wiped — but the command above is
   already in your clipboard, so this is safe).

3. Paste the /goal command as your next message. The native /goal loop
   starts; main model reads .ags/<slug>/goal.md on turn 1 to pick up
   non-negotiables, anti-patterns, and the completion audit table.

─── CHARTER ON DISK ───

  <cwd>/.ags/<slug>/goal.md   # full anti-patterns, audit table, review hook
  <cwd>/.ags/<slug>/run.txt   # the /goal command above, one line

Re-issue later: `cat .ags/<slug>/run.txt` and paste into a fresh session.
```

**Condition derivation (the `<condition>` substituted above):**

Build the `/goal` condition so it (a) carries the completion proof
verbatim — that's what the post-turn evaluator checks against
conversation context — and (b) instructs the main model to read the
charter from disk on turn 1, so non-negotiables and audit table enter
context via the Read tool (no paste needed).

```python
charter_hint = (
    f"Read .ags/{slug}/goal.md first for non-negotiables, anti-patterns, "
    f"and the completion audit table; fill the audit table before "
    f"declaring done"
)
condition = f"{intake.completion_proof}. {charter_hint}"
if len(condition) > 3500:
    # Truncate the completion_proof half; the charter hint must survive.
    head = condition[: 3500 - len(charter_hint) - 4]
    condition = f"{head}... {charter_hint}"
# Final form, appended at emit time: ", or stop after <N> turns"
```

The total `/goal <condition>, or stop after N turns` must stay under
4000 chars (native /goal hard limit). Phase 0.5 already pre-validates
the user input.

Do **not** auto-invoke `/goal`, do **not** ask any further
AskUserQuestion, do **not** auto-stage to clipboard. After printing the
block above the skill exits. Once the user types `/clear` a brand-new
session starts — no follow-up question would reach them anyway.

## State after `/goal-prep`

```text
<cwd>/.ags/<slug>/
├── goal.md     # charter, user-editable
├── run.txt     # one-line /goal command (snapshot of Phase 9 emit)
└── notes/      # empty; user may write follow-ups here
```

No `state.yaml`. No `.lock`. The charter + run.txt are the only
persistent artifacts. (`preamble.md` was emitted before v0.3.3 as a
paste-ready preamble copy; v0.3.3 dropped it — the /goal condition now
itself instructs Read on goal.md.)

## Failure modes & handling

- **User input too vague to derive a slug.** Ask one question via
  `AskUserQuestion`: "Short title for this goal? (3-6 words)" Use the
  answer for the slug.
- **Existing `goal.md` differs from intake on the same slug.** Show diff;
  user decides whether to overwrite, fork, or abort.
- **No write permission in cwd.** Abort with clear message; suggest
  moving to a writable project root.
- **Native /goal rejects after the user pastes the /goal command.** Native
  /goal is unavailable when (a) the workspace has not passed the trust
  dialog or (b) `disableAllHooks` is set in managed policy settings
  (per https://code.claude.com/docs/en/goal — `/goal` is a wrapper
  around a session-scoped Stop hook). The plugin cannot detect these
  preconditions in advance. If `/goal` refuses with a trust or hooks
  message, prompt the user to accept the trust dialog or run from a
  non-policy-locked workspace.

## What this skill is NOT

- Not native `/goal`. Execution lives in the built-in command.
- Not `/warmup` — intake compiler + ladder cover that surface.
- Not an interview tool — only ask the diagnostic questions needed for a
  correct first charter.
