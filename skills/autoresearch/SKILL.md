---
name: autoresearch
description: >
  Autonomous keep-or-revert experiment loop. Iteratively optimizes any metric
  through single atomic changes, committing before verification and reverting
  failures. Adapted from agent-workflow autoresearch with the Ralph Stop-hook
  dependency removed — now ScheduleWakeup-paced (short iterations) or
  CronCreate-paced (multi-hour iterations). Each wake-up reads state from
  disk, so context-window growth never blocks the loop. As of v0.2.0,
  per-iteration MODIFY+COMMIT is delegated to a bounded subagent
  (iron-skills:autoresearch-worker) that returns a structured final message;
  the main loop's context stays constant across iterations.
  Triggers: "autoresearch", "/autoresearch", "auto research", "optimize metric",
  "keep or revert loop", "автоисследование", "оптимизируй метрику".
allowed-tools: Bash, Glob, Grep, Read, Edit, Write, AskUserQuestion
---

# /autoresearch

Keep-or-revert metric loop. One atomic change per iteration → commit →
verify → keep or revert. No Stop hook; pacing via ScheduleWakeup or
CronCreate.

## Usage

```text
/autoresearch <goal in natural language>
/autoresearch --continue    # used by wake-up / cron resume — skips Phase 0
/autoresearch --abort       # cleanup: revert pending changes, delete crons
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
      question: "Estimated time per iteration?",
      header: "Iter time",
      multiSelect: false,
      options: [
        {label: "Under 5 min (Recommended for fast tests)", description: "Use ScheduleWakeup 90s; cache stays warm."},
        {label: "5-30 min", description: "Use ScheduleWakeup 270s (last warm window)."},
        {label: "30 min - 1 hour", description: "Borderline; ScheduleWakeup 1500s or switch to CronCreate."},
        {label: "Over 1 hour", description: "Switch to CronCreate (durable, fresh session per iteration)."}
      ]
    }
  ]
})
```

Map answers to scratchpad fields: direction, max_iterations,
iteration_estimate_hours. Iteration time picks the scheduling mechanism
in Phase 0.7.

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
   v0.3.1). User can delete the directory manually if desired.

Then continue with the standard branches below.

- If `iteration < max_iterations` AND `status == active`: continue
  from Phase 1 (whether the previous run ended via ScheduleWakeup/cron
  or crashed mid-iteration — treatment is identical).
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
a cross-LLM rescue/review hook for the loop. This Claude Code variant
calls the codex CLI as the "other" LLM (the Codex variant under
`skills-codex/autoresearch/SKILL.md` calls `claude -p` instead —
symmetric design).

```bash
if command -v codex >/dev/null 2>&1; then CODEX_ON_PATH=1; else CODEX_ON_PATH=0; fi
```

Ask:

```
AskUserQuestion({
  questions: [{
    question: "Enable codex auto-suggest? After 3 consecutive failures I can spawn the codex:codex-rescue subagent (or print /codex:rescue for you). Pre-merge I can run codex review --base main via Bash. Requires the codex CLI on PATH (npm i -g @openai/codex).",
    header: "Cross-LLM review",
    multiSelect: false,
    options: [
      // First option Recommended based on CODEX_ON_PATH (1 → Yes first, 0 → No first)
      {label: <"Yes — suggest at stuck-points (Recommended)" if detected else "No — keep loop deterministic (Recommended)">,
       description: "On 3 fails → spawn codex:codex-rescue subagent. Pre-merge → run codex review --base main via Bash."},
      {label: <opposite>,
       description: "Loop runs deterministic; no cross-LLM prompts."},
      {label: "What is codex?",
       description: "Show install info and re-ask."}
    ]
  }]
})
```

If user picks "What is codex?", print:

```
codex is OpenAI's terminal coding agent (npm i -g @openai/codex). With
codex on PATH this skill uses it two ways:
  - codex review (CLI via Bash) for adversarial review of working-tree
    diffs and branch-vs-main diffs.
  - codex:codex-rescue (subagent via Agent tool, if openai/codex-plugin-cc
    is installed) for stuck-loop rescue.
Both use a different model than the main loop. We avoid the
/codex:adversarial-review slash command because it has
disable-model-invocation: true (blocks Skill tool from invoking it
from within another skill); the CLI has no such gate.
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
iteration_estimate_hours: <number>
status: active           # active | complete | aborted
cron_id: null            # set if cadence requires CronCreate
cross_llm_review_enabled: <from Phase 0.55>   # true | false (was codex_enabled in v2, codex_available in v1)
state_schema_version: 3
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

### 0.7 Choose scheduling mechanism

Decide based on `iteration_estimate_hours`:

| `iter_est_h` | Mechanism | Reason |
|--------------|-----------|--------|
| `<= 1` | ScheduleWakeup (delay derived from `iter_secs`, see formula below) | Iterations fit in one cache window; keep session warm. |
| `> 1` | CronCreate (durable, every `ceil(iter_est_h + 0.5)h`) | Long iterations need fresh sessions. |

ScheduleWakeup delay formula (keep within 270s cache-warm window when
possible, else go past 300s into a fresh prompt-cache miss):

```python
if iter_secs <= 60:     delay = 90      # short tests, generous slack
elif iter_secs <= 270:  delay = 270     # last warm window
elif iter_secs <= 1500: delay = 1500    # bigger run, one cache miss
else:                   delay = 3600    # ScheduleWakeup max
```

If CronCreate path:

```bash
# Load schema once
ToolSearch select:CronCreate,CronDelete,CronList

# Derive non-:00/:30 minute via slug hash to spread crons across the hour
MIN=$(printf '%s' "<goal-slug>" | cksum | cut -d' ' -f1 | awk '{print ($1 % 58) + 1}')
HOUR_STRIDE=$(( $(printf '%.0f' "$ITER_EST_H") + 1 ))

CronCreate({
  cron: "${MIN} */${HOUR_STRIDE} * * *",
  prompt: "/autoresearch --continue",
  durable: true,
  reason: "autoresearch iteration trigger for <goal-slug>"
})
```

Store the returned id in `cron_id` in the scratchpad.

Print to user:

```text
Autoresearch is set up.
- Scope: <scope>
- Metric: <metric_cmd> (direction: <direction>, baseline: <baseline>)
- Schedule: <ScheduleWakeup interval | CronCreate cron expression>
- Max iterations: <N>
- Branch: autoresearch/<goal-slug>
- Cleanup: /autoresearch --abort
```

Also print this info-line (best-effort warning — there is no API to
detect an active native /goal programmatically):

```
If a native /goal is currently active in this session, its Haiku
evaluator runs after every /autoresearch turn — extra small-fast-model
tokens, plus a small risk that the evaluator misreads autoresearch
commit/revert output as the goal's condition being met (false-positive
close). Consider /goal clear before continuing.
```

**Do not start Phase 1 immediately for CronCreate mode** — exit cleanly,
cron will wake the next iteration.

**ScheduleWakeup mode** proceeds to Phase 1 in the same session.

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
`scratchpad.cross_llm_review_enabled == true`. Auto-invoke without
asking — the whole point is unattended overnight runs.

Preferred path: spawn `codex:codex-rescue` subagent (read-only
analysis, returns suggestions without editing files).

```
Agent({
  subagent_type: "codex:codex-rescue",
  description: "Stuck: 3 fails in a row at iter <N>",
  prompt: `Autoresearch is stuck. 3 consecutive failing iterations on
the same metric.

Goal: ${scratchpad.goal}
Metric command: ${scratchpad.metric_cmd}
Direction: ${scratchpad.direction}
Last 3 history rows: ${tail3(history_tsv)}
Recent scratchpad memory: ${scratchpad.body}

Diagnose the likely root cause and propose ONE fundamentally different
approach. Read-only — don't edit files. Return analysis + suggestion as
prose.`,
})
```

Fallback if `codex:codex-rescue` is not registered: run via Bash
`codex review --uncommitted "<same prompt body>"`.

Capture the rescue output:
- Append a one-line summary to scratchpad `## Next to try` with prefix
  `[from rescue iter N] `.
- Bump `scratchpad.rescue_count` (optional frontmatter field — create
  with value 1 if missing).
- Set `last_rescue_at: <iso now>` in frontmatter.

Print 1-line console notice:
`[iter N+1] auto-invoked rescue: <one-line summary>`

Then continue normal Phase 2 IDEATE — pivot logic now has the rescue's
suggestion in `## Next to try`, so IDEATE will likely pick it next.

**Never auto-apply** any code changes from rescue output. The
`codex:codex-rescue` subagent is constrained to analysis-only by the
prompt above; the Bash CLI fallback (`codex review --uncommitted`) is
analysis-only by design. If rescue output ever proposes a patch, ignore
the patch and use only the diagnosis + suggestion text. See
`references/codex-integration.md`.

If `scratchpad.cross_llm_review_enabled == false` → no rescue, normal
pivot logic only.

---

## Phase 2.5 — Delegate to autoresearch-worker

Spawn the `iron-skills:autoresearch-worker` subagent to apply the
chosen hypothesis. The parent does **not** read source files or compose
edits — that work happens inside the subagent's context, keeping the
parent's context constant per iteration.

Compose the worker prompt from current scratchpad state:

```text
Hypothesis to apply: <selected from scratchpad ## Next to try>
Scope (modify only these): <scratchpad.scope>
Iteration: <N>
Goal context: <scratchpad.goal>

Recent learnings:
- Worked (last 2): ...
- Failed (last 2): ...
- Blocked ideas: ...

Apply ONE atomic change inside scope. Commit. Return a structured
final message per the autoresearch-worker contract (key:value lines,
no markdown). Include `lesson: <forward-looking suggestion>` when you
notice something the next iteration should know.
```

Spawn:

```
Agent({
  subagent_type: "iron-skills:autoresearch-worker",
  description: f"iter {N}: {short_hypothesis}",
  prompt: WORKER_PROMPT
})
```

Parse the agent's final message for these key:value lines:

- `result: applied | aborted`
- `commit: <hash or null>`
- `files_changed: <comma-separated paths>`
- `summary: <one sentence>`
- `lesson: <optional forward-looking suggestion, may be empty>`

If `lesson` is non-empty, append it to scratchpad `## Next to try` with
prefix `[from worker iter N] ` in Phase 7.

**If `result: aborted`:**
- Log to `autoresearch-history.tsv` as `DISCARD` with the aborted
  reason from `summary`.
- Skip Phase 5 (verify) and go directly to Phase 7 (LOG).

**If `result: applied`:**
- The subagent has already committed the change. Continue to Phase 5
  (VERIFY) — the parent now runs metric/guard against that commit.

**Fallback if `iron-skills:autoresearch-worker` is not registered:**
retry with `subagent_type: "general-purpose"` and prepend the entire
`agents/autoresearch-worker.md` body (minus frontmatter) to the prompt
so the generic subagent has the contract inline.

**Parse failure fallback:** if the agent's final message lacks the
required keys, treat it as `result: aborted, summary: "worker returned
malformed final message"` and log a DISCARD. Don't try to read state
from disk — there's no on-disk record beyond git log + history.tsv
(per-iteration receipt files were dropped in v0.3.1).

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

The commit being judged was made by the autoresearch-worker subagent in
Phase 2.5. The parent decides KEEP vs revert based on metric/guard
results, not on subagent's self-assessment.

```text
IF metric improved (respecting direction) AND (no guard OR guard passed):
    status = KEEP
    Update scratchpad frontmatter:
      best_metric: <new metric>
      best_commit: <new commit hash>
ELSE:
    status = DISCARD | CRASH | GUARD_FAIL
    git revert --no-edit HEAD     # reverts the subagent's commit
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

Read `iteration`, `max_iterations`, `iteration_estimate_hours`, `cron_id`
from scratchpad frontmatter.

```text
IF iteration >= max_iterations:
    Print summary:
      - Best metric: X (baseline: Y, delta: Z%)
      - Iterations: N total, K kept, M discarded
      - Best commit: <hash>
      - Branch: autoresearch/<goal-slug>

    Cleanup:
      - If cron_id != null:
          Load CronDelete schema → CronDelete({id: cron_id})
      - Set status: complete in scratchpad.

    If scratchpad.cross_llm_review_enabled == true: before user merges, run via Bash: `codex review --base main "<prompt summarizing best_commit changes>"`. Present findings via AskUserQuestion; do not auto-apply. (CLI used instead of /codex:adversarial-review because the slash command has disable-model-invocation: true — see references/codex-integration.md.)

    Print final summary line:
      "autoresearch finished — best metric <X> (baseline <Y>, delta <Z%>),
       <N> iterations (<K> kept, <M> discarded), branch autoresearch/<slug>"
    Exit cleanly.

ELSE:
    Print: "Iteration <N>: <STATUS>. Metric: <value> (best: <best>, delta: <delta>)"

    IF cron_id != null:
      # Cron mode — exit cleanly, next tick will trigger.
      Exit.

    ELSE:
      # ScheduleWakeup mode
      iter_secs = elapsed wall time of this iteration
      delay = wakeup_delay(iter_secs)   # formula in Phase 0.7
      ScheduleWakeup({
        delaySeconds: delay,
        prompt: "/autoresearch --continue",
        reason: "autoresearch iter <N+1>"
      })
      Exit.
```

---

## `--abort` handling

When `$ARGUMENTS` contains `--abort`:

1. Read scratchpad frontmatter. If file missing — nothing to abort.
2. If `cron_id != null`: Load `CronDelete` schema, delete the cron.
3. Set `status: aborted`. (Any pending ScheduleWakeup is one-shot; the
   next wake-up will see `status: aborted` and exit cleanly without
   needing a flag.)
4. Print summary: iterations completed, best metric, branch name.
5. Exit. Do not revert successful commits — they're on the branch.

---

## Cleanup notes

After completion or abort:

- The experiment branch `autoresearch/<goal-slug>` contains all kept
  changes. User merges with `git switch main && git merge autoresearch/<goal-slug>` or cherry-picks.
- `autoresearch-scratchpad.md` and `autoresearch-history.tsv` stay on the
  branch as the experiment record.
- Crons are auto-deleted in Phase 8 on `complete`, or on `--abort`.
- ScheduleWakeup is one-shot — nothing to clean.

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

## Differences from `agent-workflow/skills/workflow/autoresearch`

| Removed | Reason |
|---------|--------|
| `mode: ralph` (Phase 0.2 Q6, Phase 0.7 Mode A, Phase 8 ralph branch) | Stop hook coupling out of scope for iron-skills. |
| `.claude/ralph-loop.local.md` creation | Replaced by ScheduleWakeup. |
| "continue to Phase 1" pseudo-loop in Phase 8 | Replaced by explicit ScheduleWakeup or CronCreate exit. |
| Phase 3 (MODIFY) + Phase 4 (COMMIT) inline (pre-v0.2.0) | Moved into the `iron-skills:autoresearch-worker` subagent so the main loop's context stays constant per iteration. |

| Added | Why |
|-------|-----|
| Phase 0.5b — resume validation | Re-entry across wake-ups + handles edge states (max reached / aborted / completed). Crashed-mid-iteration is treated as a normal resume — no special flag needed. |
| Phase 2 mid-loop auto-rescue (v0.3.1, was AskUserQuestion in v0.2.x–v0.3.0) | 3 consecutive fails + `cross_llm_review_enabled=true` → spawn `codex:codex-rescue` subagent automatically (no AskUserQuestion). Suggestion lands in scratchpad `## Next to try`. Designed for unattended overnight runs. |
| `--abort` handling | Explicit cleanup path (was implicit via ralph cleanup). |
| Phase 0.55 — cross-LLM review opt-in (v0.2.0, renamed v0.3.0) | Replaces silent detection with explicit AskUserQuestion at setup; stored as `cross_llm_review_enabled` (was `codex_enabled` in v2, `codex_available` in v1). |
| Phase 2.5 — delegate to subagent (v0.2.0) | `iron-skills:autoresearch-worker` does MODIFY+COMMIT inside its own context; parent reads only a short structured final message. |
| Subagent `lesson:` final-message field (v0.3.1) | Optional forward-looking suggestion from the bounded implementer; parent appends to scratchpad `## Next to try`. Replaces what the dropped per-iteration receipt files used to capture under their old "Notes for parent" prose section. |
| State schema v3 (v0.3.0) | Renames `codex_enabled` → `cross_llm_review_enabled` to reflect bidirectional Claude Code ↔ Codex review. Phase 0.5b auto-migrates v1/v2 → v3. |

| Removed in v0.3.1 | Reason |
|---|---|
| Mid-loop `AskUserQuestion` at 3-fail trigger | Made overnight runs impossible. Replaced with auto-rescue (row above). |
| Per-iteration `autoresearch-iterations/iter-N.md` receipt files | Subagent's structured final message + `git log` + `history.tsv` already covered the audit trail. Receipts were ~1.8 KB of redundant prose per iteration. |

Backwards-compatible: same file names (`autoresearch-scratchpad.md`,
`autoresearch-history.tsv`) and branch name (`autoresearch/<slug>`).
Users coming from agent-workflow can `/autoresearch --continue` against
their existing state — the scratchpad parser tolerates extra/missing
frontmatter fields gracefully.

## See also

- `skills/autoresearch/references/scratchpad-skeleton.md` — full
  scratchpad format with examples.
- `references/scheduling-policy.md` — ScheduleWakeup vs
  CronCreate decision detail.
- `references/state-conventions.md` — atomic writes and locking.
- `references/codex-integration.md` — auto-suggest triggers.
- `references/git-fallback.md` — why git is required.
