---
name: autoresearch
description: >
  Codex CLI variant. Autonomous keep-or-revert experiment loop.
  Iteratively optimizes any metric through single atomic changes,
  committing before verification and reverting failures. Adapted from
  agent-workflow autoresearch. Codex has no scheduling primitives
  (no /loop, no cron), so this variant runs an in-session sequential
  loop — Phases 1-7 execute back-to-back until max_iterations,
  convergence, or session close. Multi-day runs require manual
  /autoresearch --continue per fresh session; the scratchpad on
  disk survives.
  Triggers: "autoresearch", "/autoresearch", "auto research", "optimize metric",
  "keep or revert loop", "автоисследование", "оптимизируй метрику".
allowed-tools: Bash, Glob, Grep, Read, Edit, Write, AskUserQuestion
---

# /autoresearch (Codex variant)

Keep-or-revert metric loop. One atomic change per iteration → commit →
verify → keep or revert. In-session sequential — Codex has no
ScheduleWakeup or CronCreate equivalents, so iterations run back-to-back
inside the current session. The mirror Claude Code variant under the
root `skills/autoresearch/SKILL.md` does use ScheduleWakeup/CronCreate
for multi-session durability.

## Usage

```text
/autoresearch <goal in natural language>
/autoresearch --continue    # resume from saved scratchpad in a fresh session — skips Phase 0
/autoresearch --abort       # mark scratchpad status: aborted; do not revert kept commits
```

`$ARGUMENTS` is the raw input.

## Git requirement

`/autoresearch` requires a git repository (the loop is built on
commit + revert). Without git, abort with:

> /autoresearch requires a git repo. Run `git init && git add -A && git
> commit -m 'baseline'` first.

See `references/git-fallback.md` for full rationale.

---

## Phase 0 — SETUP

**Skip to Phase 1 if** `autoresearch-scratchpad.md` already exists in the
project root **or** `$ARGUMENTS` contains `--continue`.

### 0.1 Parse goal

Extract optimization goal from `$ARGUMENTS`. If empty → ask via
`AskUserQuestion`.

### 0.2 Interactive setup

Two stages. Free-text inputs ask via plain prose (user types the answer
directly). Discrete-choice inputs use `AskUserQuestion` in a single batch.

**Stage A — free-text (ask in sequence):**

1. **Scope** — files/directories you may modify (e.g. `src/api/`, `train.py`, `tests/`).
2. **Metric command** — shell command that prints a single number to stdout (e.g. `pytest -q 2>&1 | tail -1`, `wc -l src/*.py`).
3. **Guard command** (optional) — sanity check (`pytest`, `npm test`, `cargo check`). Empty to skip.

**Stage B — discrete choices (one `AskUserQuestion` batch, 3 questions):**

```
AskUserQuestion({
  questions: [
    {
      question: "Direction: should the metric go up or down?",
      header: "Direction",
      multiSelect: false,
      options: [
        {label: "Higher is better (Recommended for accuracy)", description: "Keep iterations that increase the metric (accuracy, throughput)."},
        {label: "Lower is better", description: "Keep iterations that decrease the metric (latency, line count, errors)."}
      ]
    },
    {
      question: "Max iterations before stopping?",
      header: "Max iter",
      multiSelect: false,
      options: [
        {label: "20 (Recommended)", description: "Default for most optimization runs."},
        {label: "10", description: "Quick sweep / exploratory."},
        {label: "50", description: "Long run / hard problems."},
        {label: "100", description: "Very long run; consider CronCreate scheduling."}
      ]
    },
    {
      question: "Estimated time per iteration? (used only for the upfront warning — Codex variant runs in-session sequentially with no scheduling.)",
      header: "Iter time",
      multiSelect: false,
      options: [
        {label: "Under 5 min (Recommended for fast tests)", description: "Fast — many iterations fit in one Codex session."},
        {label: "5-30 min", description: "Moderate — a session might fit 10-30 iterations."},
        {label: "30 min - 1 hour", description: "Slow — expect ≤10 iterations per session; plan for `--continue` across multiple sessions."},
        {label: "Over 1 hour", description: "Very slow — consider switching to the Claude Code variant which has durable CronCreate scheduling."}
      ]
    }
  ]
})
```

Map answers to scratchpad fields: direction, max_iterations. Iteration
time is logged for the user's planning only — the Codex variant has no
scheduling fork in Phase 0.7.

### 0.3 Dry-run validation

```bash
AUTORESEARCH_TMP="/tmp/autoresearch-$(git rev-parse --short HEAD)-$$"
<metric_cmd> > ${AUTORESEARCH_TMP}-run.log 2>&1
grep -oE '[0-9]+\.?[0-9]*' ${AUTORESEARCH_TMP}-run.log | tail -1
```

If no number extractable → ask user to fix the metric command. Do not
proceed.

### 0.4 Create experiment branch

```bash
git checkout -b autoresearch/<goal-slug>
```

Where `<goal-slug>` is derived from the goal text:

```bash
slug=$(printf '%s' "$GOAL" \
    | tr '[:upper:]' '[:lower:]' \
    | sed 's/[^a-z0-9]/-/g; s/--*/-/g; s/^-//; s/-$//' \
    | cut -c1-40)
```

### 0.5 Baseline

Run metric command, record extracted number as `BASELINE` (iteration 0).

### 0.5b Resume validation (only on `--continue`)

If `autoresearch-scratchpad.md` exists, parse frontmatter.

**v1/v2 → v3 schema migration:** if `state_schema_version` is missing,
equals `1`, or equals `2`, the scratchpad predates the v0.3.0 cross-LLM
rename. Migrate inline:

1. Run Phase 0.55 (cross-LLM opt-in) to set `cross_llm_review_enabled` from user.
2. Rewrite frontmatter:
   - Remove deprecated `codex_available`, `codex_skipped_at_phase_2`, and the
     old `codex_enabled` field (renamed below).
   - Add `cross_llm_review_enabled: <from step 1>`.
   - Set `state_schema_version: 3`.
3. Print: `Migrated scratchpad v<old> → v3 (renamed codex_enabled → cross_llm_review_enabled)`.
4. Pre-existing `autoresearch-iterations/<...>.md` files from older runs
   are left in place — no code reads them anymore (receipts dropped in
   v0.3.1).

Then continue with the standard branches below.

- If `iteration < max_iterations` AND `status == active`: previous
  session ended mid-loop (Codex doesn't resume automatically) →
  continue from Phase 1 inline.
- If `iteration >= max_iterations`:
  ```
  AskUserQuestion({
    questions: [{
      question: "Previous /autoresearch run hit max_iterations (<N>). How to proceed?",
      header: "Max reached",
      multiSelect: false,
      options: [
        {label: "Extend max_iterations and continue (Recommended)", description: "Increase the cap; resume from where we left off."},
        {label: "Reset and start fresh", description: "Delete scratchpad + history; keep the experiment branch for reference."},
        {label: "Abort cleanly", description: "Set status: aborted; no further changes."}
      ]
    }]
  })
  ```
- If `status == aborted` or `status == complete`:
  ```
  AskUserQuestion({
    questions: [{
      question: "Previous /autoresearch run ended with status `<status>`. Restart?",
      header: "Run ended",
      multiSelect: false,
      options: [
        {label: "Archive and start fresh (Recommended)", description: "Move scratchpad+history to `_archive/<slug>-<ts>/`; new run from baseline."},
        {label: "Resume in place", description: "Reset status to active; continue iterations on the same branch."},
        {label: "Abort", description: "Do nothing; exit."}
      ]
    }]
  })
  ```

### 0.55 Cross-LLM review opt-in

After resume validation (or freshly on first run), ask whether to enable
a cross-LLM rescue/review hook for the loop. This Codex variant calls
the claude CLI as the "other" LLM (the Claude Code variant under root
`skills/autoresearch/SKILL.md` calls `codex review` instead — symmetric
design).

```bash
if command -v claude >/dev/null 2>&1; then CLAUDE_ON_PATH=1; else CLAUDE_ON_PATH=0; fi
```

Ask:

```
AskUserQuestion({
  questions: [{
    question: "Enable cross-LLM auto-suggest? After 3 consecutive failures I can run `claude -p` with the recent history for a different-model rescue. Pre-merge I can run `git diff main | claude -p` for adversarial review. Requires the claude CLI on PATH (npm i -g @anthropic-ai/claude-code).",
    header: "Cross-LLM review",
    multiSelect: false,
    options: [
      // First option Recommended based on CLAUDE_ON_PATH (1 → Yes first, 0 → No first)
      {label: <"Yes — suggest at stuck-points (Recommended)" if detected else "No — keep loop deterministic (Recommended)">,
       description: "On 3 fails → invoke `claude -p` with stuck-context for rescue. Pre-merge → run `git diff main | claude -p` for review."},
      {label: <opposite>,
       description: "Loop runs deterministic; no cross-LLM prompts."},
      {label: "What is claude -p?",
       description: "Show install info and re-ask."}
    ]
  }]
})
```

If user picks "What is claude -p?", print:

```
claude is Anthropic's terminal coding agent (npm i -g
@anthropic-ai/claude-code). The -p flag runs it in headless print mode:
`claude -p "<prompt>"` returns a single response and exits. With claude
on PATH this skill uses it two ways:
  - Rescue at stuck-loop: `claude -p` with last 3 history rows + stuck
    metric, asking for a different-angle approach.
  - Pre-merge review: `git diff main | claude -p` for adversarial
    second opinion before the user merges the experiment branch.
Both use a different model than the main loop.
```

Then re-ask the same AskUserQuestion.

Store decision in scratchpad frontmatter as `cross_llm_review_enabled: true | false`.

### 0.6 Create state files

`autoresearch-scratchpad.md` (config in frontmatter + empty working memory):

```markdown
---
goal: "<goal>"
scope: "<scope>"
metric_cmd: "<metric command>"
guard_cmd: "<guard command or empty>"
direction: "<higher_is_better or lower_is_better>"
best_metric: <baseline>
best_commit: "<HEAD hash>"
iteration: 0
max_iterations: <N>
status: active           # active | complete | aborted
cross_llm_review_enabled: <from Phase 0.55>   # true | false (was codex_enabled in v2, codex_available in v1)
state_schema_version: 3
# Note: Codex variant omits iteration_estimate_hours/cron_id — Codex
# has no scheduling primitives. Migration on --continue tolerates
# extra fields (no-op if a CC-variant scratchpad carries cron_id).
---

## What worked

## What failed

## Next to try

## Blocked ideas
```

`autoresearch-history.tsv` (header + baseline row):

```text
iteration	commit	metric	delta	status	description
0	<HEAD hash>	<baseline>	-	BASELINE	initial measurement
```

### 0.7 In-session loop driver

Codex has no `ScheduleWakeup`, no `CronCreate`, and no `/loop` command
(verified via `codex --help`). The autoresearch loop runs **in-session
sequential** — Phases 1-7 execute back-to-back inside the current
Codex session.

Behavior:

- After SETUP completes, fall straight into Phase 1 and run the loop
  inline. Each iteration: READ STATE → IDEATE → MODIFY+COMMIT →
  VERIFY → KEEP/REVERT → LOG.
- After each iteration, re-check Phase 8 (EXIT CHECK). If
  `iteration < max_iterations` AND `status == active`: continue
  directly to Phase 1 of the next iteration.
- The loop ends only on `iteration >= max_iterations`, an explicit
  `/autoresearch --abort`, convergence, or the user closing the
  Codex session.

Print to user before starting Phase 1:

```text
Autoresearch is set up.
- Scope: <scope>
- Metric: <metric_cmd> (direction: <direction>, baseline: <baseline>)
- Max iterations: <N>
- Branch: autoresearch/<goal-slug>
- Loop mode: in-session sequential (Codex variant)
- Cleanup: /autoresearch --abort

Starting Phase 1 now. Iterations will run back-to-back until
max_iterations or you interrupt.
```

Also print this info-line (best-effort warning — there is no API to
detect an active native /goal programmatically):

```
If a native /goal is currently active in this session, its evaluator
runs after every /autoresearch turn — extra small-fast-model
tokens, plus a small risk that the evaluator misreads autoresearch
commit/revert output as the goal's condition being met
(false-positive close). Consider /goal clear before continuing.
```

**Multi-day runs:** Codex cannot durably re-enter a closed session.
For runs longer than one session, the user re-invokes
`/autoresearch --continue` per fresh session — Phase 0.5b resumes
from the saved scratchpad position. No automatic resumption.

---

## Phase 1 — READ STATE

Do this at the **start of every iteration**. Re-read everything from
disk — this is how the loop survives context compaction.

1. Read `autoresearch-scratchpad.md` — parse frontmatter for config, read
   body for memory.
2. Read last 20 lines of `autoresearch-history.tsv`.
3. `git log --oneline -15` — recent experiments.
4. `git diff` — working tree must be clean. If not, `git stash` and
   investigate.

Compute:

- **Consecutive discards**: count trailing `DISCARD` / `CRASH` /
  `GUARD_FAIL` rows.
- **Diff hash** (stall detector):

  ```bash
  { git diff; git diff --cached; git status --porcelain; } | md5sum | head -c 32
  ```

---

## Phase 2 — IDEATE

Pick ONE atomic change to try.

Priority order:

1. **Fix crashes first.** Last status `CRASH` → diagnose before new ideas.
2. **Exploit.** Recent KEEPs exist → variations of what worked.
3. **Explore.** Pick from scratchpad `## Next to try`.
4. **Pivot.** > 5 consecutive discards → re-read all state, combine
   near-miss ideas, try a fundamentally different approach.
5. **Circuit breaker.** Diff hash identical > 3 iterations → break the
   pattern, or stop.

Rules:

- ONE atomic change per iteration. If you catch "and also" — split.
- Never modify `metric_cmd` or `guard_cmd`.
- Never modify files outside scope.

Cross-LLM auto-rescue trigger (v0.3.1 — no AskUserQuestion mid-loop):
3 consecutive `DISCARD`/`CRASH`/`GUARD_FAIL` AND
`scratchpad.cross_llm_review_enabled == true`. Auto-invoke via Bash
without asking — the whole point is unattended runs.

```bash
claude -p "Autoresearch stuck at iter <N>.

Goal: <scratchpad.goal>
Metric command: <scratchpad.metric_cmd>
Direction: <scratchpad.direction>
Last 3 history rows:
<tail -3 autoresearch-history.tsv>

Recent scratchpad memory:
<scratchpad body>

Diagnose the likely root cause and propose ONE fundamentally different
approach. Read-only — don't edit files. Return analysis + suggestion
as prose."
```

Capture the claude response:
- Append a one-line summary to scratchpad `## Next to try` with prefix
  `[from rescue iter N] `.
- Bump `scratchpad.rescue_count` (optional frontmatter field; create
  with value 1 if missing).
- Set `last_rescue_at: <iso now>` in frontmatter.

Print 1-line console notice:
`[iter N+1] auto-invoked claude -p rescue: <one-line summary>`

Then continue normal Phase 2 IDEATE — pivot logic now has the rescue's
suggestion in `## Next to try`, so IDEATE will likely pick it next.

**Never auto-apply** any code from rescue output. The `-p` prompt above
explicitly tells claude not to edit files; if the response ever proposes
a patch, ignore the patch and use only the diagnosis + suggestion text.

If `scratchpad.cross_llm_review_enabled == false` → no rescue, normal
pivot logic only.

If `claude` CLI is not on PATH → log
`rescue_skipped_at_iter: <N>: claude not on PATH` to scratchpad
`## What failed` and continue with normal pivot.

---

## Phase 2.5 — MODIFY + COMMIT (inline)

Codex does **not** ship the `iron-skills:autoresearch-worker` subagent (that
agent type is Claude-Code-host-only). The Codex variant therefore runs
MODIFY + COMMIT inline, in the same Codex session. Context growth is
the price — read only the minimal slice of files needed for this
iteration's hypothesis.

Steps:

1. Read only the files inside `scratchpad.scope` that this hypothesis
   actually touches. Do **not** browse outside scope.
2. Apply ONE atomic edit. If you catch "and also" — split into separate
   iterations.
3. Stage and commit:

   ```bash
   git add <touched files inside scope>
   git commit -m "autoresearch iter <N>: <one-line hypothesis summary>"
   COMMIT=$(git rev-parse --short HEAD)
   ```

4. Record the iteration in memory (no on-disk receipt as of v0.3.1 —
   `autoresearch-iterations/iter-N.md` files were dropped; commit msg
   + `git show <COMMIT>` + Phase 7 history.tsv row are the audit trail).
   In-memory state for Phases 5–7:

   ```
   result: applied
   commit: $COMMIT
   files_changed: <comma-separated paths>
   summary: <one sentence, ≤120 chars>
   lesson: <optional forward-looking suggestion; if non-empty, parent
            appends to scratchpad ## Next to try in Phase 7 with prefix
            "[from worker iter N] ">
   ```

**If you decide to abort the iteration** (e.g. the hypothesis turned
out to be already implemented, or out of scope):
- Do not commit anything.
- Record `result: aborted, summary: "<one-sentence reason>"` in memory.
- Skip Phase 5 (verify) and go directly to Phase 7 (LOG) — the row
  becomes `DISCARD` in history.tsv.

**If you committed:** continue to Phase 5 (VERIFY) — run metric/guard
against the new commit.

---

## Phase 5 — VERIFY

```bash
<metric_cmd> > ${AUTORESEARCH_TMP}-run.log 2>&1
echo "Exit: $?"
grep -oE '[0-9]+\.?[0-9]*' ${AUTORESEARCH_TMP}-run.log | tail -1
```

- Exit non-zero → `status = CRASH`.
- No number extractable → `status = CRASH`.
- Otherwise → proceed to Guard (if any) or Decide.

---

## Phase 5.5 — GUARD (skip if no `guard_cmd`)

```bash
<guard_cmd> > ${AUTORESEARCH_TMP}-guard.log 2>&1
echo "Exit: $?"
```

- Guard passes (exit 0) → Decide.
- Guard fails → up to 2 rework attempts. After each rework:
  `git add <files> && git commit --amend --no-edit`, re-run guard.
- Still failing after 2 reworks → `status = GUARD_FAIL`.

---

## Phase 6 — DECIDE

The commit being judged was made inline in Phase 2.5. Decide KEEP vs
revert based on metric/guard results.

```text
IF metric improved (respecting direction) AND (no guard OR guard passed):
    status = KEEP
    Update scratchpad frontmatter:
      best_metric: <new metric>
      best_commit: <new commit hash>
ELSE:
    status = DISCARD | CRASH | GUARD_FAIL
    git revert --no-edit HEAD     # reverts the Phase 2.5 commit
```

Improvement:

- `higher_is_better` → new > best
- `lower_is_better` → new < best

---

## Phase 7 — LOG + SCRATCHPAD

### 7.1 Append history

One line to `autoresearch-history.tsv`:

```text
<iteration>	<commit or REVERTED>	<metric>	<delta from best>	<status>	<description>
```

### 7.2 Update scratchpad

- Increment `iteration` in frontmatter.
- Update body:
  - `## What worked` — add on KEEP.
  - `## What failed` — add on DISCARD/CRASH/GUARD_FAIL with reason.
  - `## Next to try` — remove tried idea, add new ones based on result.
  - `## Blocked ideas` — move confirmed dead-ends here.

You **must** modify the scratchpad body each iteration. If it doesn't
change, you're not learning.

Write atomically: temp file in the same directory + `mv` to target.
Hold an `flock` against `.lock` in the project root to prevent two
concurrent wake-ups from interleaving writes:

```bash
(
    flock -n 9 || { echo "[lock-conflict] another /autoresearch session is writing"; exit 1; }
    tmp=$(mktemp -p . .autoresearch-scratchpad.XXXXXX)
    printf '%s' "$NEW_CONTENT" > "$tmp"
    mv "$tmp" autoresearch-scratchpad.md
) 9>.autoresearch.lock
```

---

## Phase 8 — EXIT CHECK

Read `iteration`, `max_iterations`, `status`, `cross_llm_review_enabled`
from scratchpad frontmatter.

```text
IF iteration >= max_iterations OR status != active:
    Print summary:
      - Best metric: X (baseline: Y, delta: Z%)
      - Iterations: N total, K kept, M discarded
      - Best commit: <hash>
      - Branch: autoresearch/<goal-slug>

    Set status: complete in scratchpad.

    IF scratchpad.cross_llm_review_enabled == true AND command -v claude succeeds:
        Before user merges, run via Bash:
            git diff main...autoresearch/<slug> | claude -p "Adversarially
            review the diff above. Goal: <scratchpad.goal>. Metric improved
            from <baseline> to <best_metric> (<direction>). Best commit:
            <best_commit>. Flag risky changes, missed cases, and anti-pattern
            violations. Read-only — do not suggest fixes I should apply, only
            findings."
        Present findings to the user via prose. Use AskUserQuestion to ask
        which findings, if any, to address. Do not auto-apply.

    Print final summary line:
      "autoresearch finished — best metric <X> (baseline <Y>, delta <Z%>),
       <N> iterations (<K> kept, <M> discarded), branch autoresearch/<slug>"
    Exit cleanly.

ELSE:
    Print: "Iteration <N>: <STATUS>. Metric: <value> (best: <best>, delta: <delta>)"

    # Codex variant: no scheduling — fall straight back to Phase 1 of
    # the next iteration in the same session. Loop continues until
    # max_iterations, --abort, or the user closes the Codex session.
    Continue to Phase 1.
```

---

## `--abort` handling

When `$ARGUMENTS` contains `--abort`:

1. Read scratchpad frontmatter. If file missing — nothing to abort.
2. Set `status: aborted`.
3. Print summary: iterations completed, best metric, branch name.
4. Exit. Do not revert successful commits — they're on the branch.

(No cron/wakeup cleanup needed — Codex variant never schedules
anything; the loop runs only inside the current session.)

---

## Cleanup notes

After completion or abort:

- The experiment branch `autoresearch/<goal-slug>` contains all kept
  changes. User merges with `git switch main && git merge autoresearch/<goal-slug>` or cherry-picks.
- `autoresearch-scratchpad.md` and `autoresearch-history.tsv` stay on the
  branch as the experiment record.
- No crons to clean (Codex has none).

---

## Rules (verbatim from agent-workflow autoresearch — battle-tested)

- Act immediately after setup — no confirmation per iteration.
- Match the user's language in output.
- ONE atomic change per iteration. Always.
- Commit **before** verify. Always.
- Re-read state from disk at the start of every iteration. Always.
- Never modify `metric_cmd` or `guard_cmd`.
- Never modify files outside scope.
- Redirect command output to `/tmp` — never flood the context window.
- If a phase fails catastrophically — revert, log, continue.

---

## Differences from Claude Code variant + from agent-workflow upstream

| Removed (vs `agent-workflow/skills/workflow/autoresearch`) | Reason |
|---------|--------|
| `mode: ralph` (Phase 0.2 Q6, Phase 0.7 Mode A, Phase 8 ralph branch) | Stop hook coupling out of scope for iron-skills. |
| `.claude/ralph-loop.local.md` creation | Codex has no ralph equivalent; loop runs in-session. |

| Removed (vs Claude Code variant at root `skills/autoresearch/SKILL.md`) | Reason |
|---------|--------|
| ScheduleWakeup / CronCreate scheduling fork (Phase 0.7) | Codex has no scheduling primitives — `codex --help` shows no /loop, no cron. Falls back to in-session sequential loop. |
| `cron_id`, `iteration_estimate_hours` frontmatter fields | Only used by the CC scheduling fork. Codex variant tolerates them in older scratchpads but does not write them. (`wakeup_pending`, `last_wakeup_at` dropped in v0.3.4 from CC variant too — were never useful.) |
| `Agent({subagent_type: "iron-skills:autoresearch-worker", ...})` delegation in Phase 2.5 | `iron-skills:autoresearch-worker` is registered as a Claude Code subagent only. Codex variant runs MODIFY+COMMIT inline — context grows linearly but loop survives. |
| `Agent({subagent_type: "codex:codex-rescue", ...})` rescue in Phase 2 | That subagent is registered by openai/codex-plugin-cc (Claude Code only). Codex variant uses `claude -p` via Bash instead. |
| `codex review --base main` pre-merge in Phase 8 | Replaced by `git diff main...HEAD | claude -p` (cross-LLM points to claude from Codex). |

| Added in Codex variant | Why |
|-------|-----|
| Phase 0.55 — cross-LLM review opt-in (asks about `claude -p`, not `codex review`) | Symmetric inverse of CC variant: detect-the-other-LLM. |
| Phase 0.7 — in-session sequential loop description | Documents the lack of scheduling explicitly. |
| Phase 2 — `claude -p` rescue path (auto-invoked since v0.3.1) | Replaces Agent subagent rescue (Codex-host-only path). Auto-invoked without AskUserQuestion so overnight runs don't stall. |
| Phase 2.5 — inline MODIFY+COMMIT (no on-disk receipt since v0.3.1) | No subagent delegation; in-memory structured record only. Commit msg + history.tsv are the audit trail. |
| Phase 8 EXIT — `git diff main | claude -p` pre-merge review | Cross-LLM review symmetric to CC's `codex review --base main`. |

Backwards-compatible: same file names (`autoresearch-scratchpad.md`,
`autoresearch-history.tsv`) and branch name (`autoresearch/<slug>`).
Users coming from agent-workflow OR from the CC variant can
`/autoresearch --continue` against their existing state — the
scratchpad parser tolerates extra/missing frontmatter fields gracefully.

## See also

- `skills/autoresearch/references/scratchpad-skeleton.md` — full
  scratchpad format with examples.
- `references/state-conventions.md` — atomic writes and locking.
- `references/codex-integration.md` — cross-LLM CLI patterns.
- `references/git-fallback.md` — why git is required.
- `references/scheduling-policy.md` — Claude Code's scheduling
  primitives; Codex variant simply has none.
