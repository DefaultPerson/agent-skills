# Scheduling policy

> **Scope:** `/autoresearch` only. `/goal-prep` is one-shot
> non-execution. Native `/goal` is inline (single-session) — no pacing
> needed from us.

## Codex CLI host — no scheduling primitives

Codex CLI does **not** have `/loop`, `/cron`, or scheduling primitives
(verified via `codex --help`). When `/autoresearch` runs on Codex:

- The Claude Code-only ScheduleWakeup/CronCreate paths are unavailable.
- Fall back to **in-session sequential loop**: Phases 1-7 execute
  back-to-back in the current session, exiting only at
  `max_iterations`, convergence, or session close.
- For multi-day runs on Codex: user must manually re-invoke
  `/autoresearch --continue` per session (the scratchpad survives;
  the loop resumes from saved iteration).
- For iterations > 30 min on Codex: NOT RECOMMENDED — single session
  will exhaust before completing many iterations.

For Claude Code host, full scheduling support continues per below.

## Claude Code host primitives

`/autoresearch` paces its keep-or-revert loop with two Claude Code
primitives:

- **`ScheduleWakeup`** — in-session, wakes the same conversation after a delay.
- **`CronCreate` / `CronList` / `CronDelete`** — cron-based, opens a fresh session.

No Stop hook is used in this plugin's own code. (Native `/goal` itself is
a Stop-hook wrapper — that's upstream. Anthropic's official `ralph-wiggum`
plugin also uses Stop hooks; the mechanism is legitimate, we just don't
use it ourselves.)

## Cache-window math (ScheduleWakeup)

The Anthropic prompt cache has a 5-minute TTL.

| Delay | Behavior |
|-------|----------|
| 60–270s | Stays in cache. Cheap and fast. |
| 300s | **Worst-of-both region.** Pays the cache miss without amortizing it. Never pick this. |
| 301–3600s | One cache miss; amortized over a long wait. Acceptable for idle waits. |

`/autoresearch` delay (inline formula in the autoresearch SKILL.md
Phase 0.7):

- **iter under 5 min** → 90s (intra-iteration catchup, warm cache).
- **iter 5–30 min** → 270s (still in warm window).
- **iter over 30 min** → switch to `CronCreate` instead.

`ScheduleWakeup` is clamped to `[60, 3600]`. For longer than one hour or
for durability across session restarts, use `CronCreate`.

## CronCreate guidelines

Cron schemas are deferred tools — not loaded by default. Load per session:

```text
ToolSearch({query: "select:CronCreate,CronDelete,CronList", max_results: 5})
```

Loaded schemas do **not** persist across wake-ups; every fresh session must
re-load.

### Cron expression rules

- **Avoid `:00` and `:30` minutes** — fleet thundering herd. Pick a minute
  in `7..25` or `35..53`.
- **Slug-derived deterministic offset** (inline, spreads crons across
  the safe minute ranges):

  ```bash
  MIN=$(( ( $(printf '%s' "$SLUG" | sum | awk '{print $1}') % 19 ) + 7 ))
  ```

- Always set `durable: true`. Without it the cron vanishes when the
  controlling session ends.

### 7-day auto-expiry

`CronCreate` jobs auto-expire after 7 days. For multi-day autoresearch
runs, re-register at iteration boundary if `(now - created_at) > 6 days`:

```bash
# Pseudocode
if (now - cron.created_at) > 6 days:
    CronDelete({id: cron.id})
    new_id = CronCreate({...})
    scratchpad.cron_id = new_id
    scratchpad.cron_created_at = now
```

### Cleanup at completion

On `max_iterations` reached or `/autoresearch --abort`:

1. Load `CronDelete` schema via `ToolSearch`.
2. Call `CronDelete({id: scratchpad.cron_id})`.
3. Set `scratchpad.status: complete` (or `aborted`).

`ScheduleWakeup` is one-shot; nothing to clean up.

## Decision table

Pick the mechanism by `iteration_estimate_hours`:

| Estimate | Mechanism | Notes |
|----------|-----------|-------|
| ≤ 1h | ScheduleWakeup | Stays inside the 3600s cap; cache-aware delay via the Phase 0.7 formula. |
| > 1h | CronCreate (`durable: true`) | Cron at `MM */ceil(estimate+0.5)h * * *`, MM = slug-derived. |

## When the wake-up never fires

- **ScheduleWakeup**: if the user closes Claude Code, the wake-up is lost.
  The loop pauses until the user manually runs `/autoresearch --continue`.
- **CronCreate**: durable; continues firing in a fresh session.

For long autoresearch runs prefer cron — it survives any session close.
