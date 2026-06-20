# `autoresearch-scratchpad.md` format

The scratchpad is the autoresearch loop's persistent memory. It lives at
`<cwd>/autoresearch-scratchpad.md` (project root, same as the existing
agent-workflow autoresearch convention) and is checked into the
experiment branch `autoresearch/<slug>`.

## Frontmatter

```yaml
---
# Identity
goal: "<original goal text from /autoresearch <goal>>"
scope: "<comma-separated paths the loop may modify, e.g. 'src/api/, train.py'>"

# Measurement
metric_cmd: "<shell command that prints a single number to stdout>"
guard_cmd: "<shell command that returns 0 on healthy state, or empty>"
direction: higher_is_better      # or lower_is_better

# Progress
best_metric: 0.72
best_commit: "abc1234"
iteration: 7
max_iterations: 20

# Scheduling
iteration_estimate_hours: 0.5
cron_id: null                    # set only when CronCreate path is used

# Status
status: active                   # active | complete | aborted
cross_llm_review_enabled: false  # user opt-in at Phase 0.55 (default from `command -v codex` for CC variant, `command -v claude` for Codex variant)

# Plumbing
state_schema_version: 3
---
```

## Body sections

Four mandatory sections, even when empty:

```markdown
## What worked

- iter 3: dropping the second LSTM layer (acc 0.71 → 0.74).
- iter 6: replacing softmax with sigmoid for binary head (acc 0.74 → 0.78).

## What failed

- iter 4: adding dropout 0.5 — collapsed to 0.65 (overcorrected). DISCARD.
- iter 5: batch size 256 — OOM. CRASH.

## Next to try

- Smaller learning rate (3e-5 instead of 1e-4) — Adam noisiness suspected.
- Label smoothing 0.1 — based on iter 6 sigmoid stability.

## Blocked ideas

- Quantization to int8 — depends on Torch upgrade; out of scope this run.
```

## Conventions

- **Always** update the body when you update the frontmatter. If
  `## What worked` doesn't grow on a KEEP iteration, the loop isn't
  learning.
- Keep entries dated by iteration ("iter 3:") so the audit can trace which
  history.tsv row produced the insight.
- Move ideas between sections explicitly. An idea that failed once but
  might work after another change moves to "Next to try" with a "(retry
  after <other thing>)" note.
- **Blocked ideas** is one-way; if it really turns out to be unblocked,
  add a fresh entry under "Next to try" with the unblocking rationale.

## What this file is NOT

- Not a journal. Keep it terse. Long context goes into commit messages and
  history.tsv `description` columns.
- Not the source of truth for what's done. `autoresearch-history.tsv` is
  the append-only ledger of every iteration.
- Not editable mid-iteration by humans — if you want to change scope or
  metric, run `/autoresearch --abort` and start fresh.

## Reading the scratchpad in Phase 1

The Phase 1 read parses:

- Every frontmatter field — for the iteration loop.
- The four body sections — for what to try next (Phase 2).
- The last 20 lines of `autoresearch-history.tsv` — for the recent
  history.

That's the full state restore. Nothing in conversation context is
required.

## Concurrency

Hold an `flock` on `<cwd>/.autoresearch.lock` and write via temp-file +
`mv` rename. See `references/state-conventions.md` for the full
pattern. Two concurrent autoresearch loops in the same project would
otherwise corrupt the file.

## Companion files (v3 schema)

One sibling artifact in the project root:

- `autoresearch-history.tsv` — append-only ledger (one row per iteration:
  iteration, commit, metric, delta, status, description).

Per-iteration `autoresearch-iterations/iter-N.md` receipts were dropped
in v0.3.1 — the subagent's structured final message + `git show
<commit>` + `autoresearch-history.tsv` row already cover the audit
trail. Existing receipt files from older runs are left in place;
nothing reads them anymore.
