---
name: babysit
description: >
  Autonomous watch → fix → deploy → recheck LOOP for a running service: every N
  minutes it reads only NEW logs and, on trouble, delegates a bounded fix to a
  sub-agent, ships it via your `deploy_cmd` (or a deploy MCP), and verifies —
  repeating until you stop it. Escalates with a repeating sound + desktop
  notification only when stuck or a change is unsafe. Use ONLY when the user
  explicitly wants this ongoing UNATTENDED loop — not a one-off log read, health
  check, or single fix. Claude Code only (needs the native /loop). Triggers:
  "/babysit", "babysit the service", "watch and auto-fix/deploy", "keep the
  service healthy unattended", "присматривай за сервисом".
when_to_use: >
  The user wants a running service kept healthy unattended OVER TIME via a
  repeating fix-and-deploy loop, in an environment where a bad deploy is
  recoverable. NOT for a one-off log read / health check / single bug fix (use a
  normal agent), and NOT a monitoring/paging system. Claude Code only — it needs
  the native /loop cadence, the Agent tool, and a way to deploy.
---

# /babysit — autonomous watch · fix · deploy · re-check loop

Babysit a running service so you don't have to. Each tick: read **only new
logs**, decide healthy-or-not, and — if not — hand a bounded fix to a sub-agent,
deploy it, and verify. Loop until you cancel. Call you (sound every 30s) **only**
when stuck or when a change is too risky to make unattended.

> **Claude Code only.** This skill needs the native `/loop` cadence, the `Agent`
> tool, and (optionally) a deploy MCP. Codex has no in-session loop primitive, so
> there is no Codex variant — on Codex, drive a single `/babysit` tick from an
> external cron + `codex exec` instead.

> **Letter = spirit.** If a rule blocks you from reaching the goal it was written
> for, the rule is wrong, not the goal. Don't look for a wording loophole — ask
> what the rule protects, and protect that. Here the goal is: keep the service
> healthy *without* surprising the operator. When in doubt, escalate; never
> deploy a guess.

## Deploy / log adapter (platform-agnostic)

babysit talks to your service through **two shell commands** — nothing platform-specific is assumed:

- **`log_cmd`** — prints recent logs to stdout. Examples: `ssh prod 'journalctl -u app --since "-6min" --no-pager'`, `docker logs --since 6m <c>`, `kubectl logs --since=6m deploy/app`, `tail -n 200 /var/log/app.log`.
- **`deploy_cmd`** — ships the committed fix. Examples: `git push deploy main`, `make deploy`, `flyctl deploy`, `kubectl rollout restart deploy/app`.
- **`rollback_cmd`** *(optional)* — one-step undo. Examples: `git revert HEAD && git push deploy main`, re-deploy the prior good build. If absent, babysit escalates instead of auto-undoing.

If you happen to run a platform with an MCP (e.g. **coolify**, or any other), you may point these at MCP tools instead of shell — resolve the app/resource id once at setup, and note which tool fetches logs, which deploys, and how to poll a deploy to a terminal state. The adapter is the contract; the backend is your choice.

## Weaknesses and when NOT to use

- **It deploys to a real environment unattended.** That is the whole point and
  the whole danger. Use only where a bad deploy is *recoverable* (CI gate,
  health check, easy rollback). Never point it at something where one wrong
  push is unrecoverable (irreversible migration, payment cutover, data wipe).
- **Only as good as its trouble-definition.** If "wrong" is vague, it either
  ignores real fires or thrashes on benign noise. Spend the setup minute making
  the definition concrete (patterns, health check, thresholds).
- **A fix loop can mask a design flaw.** Two failed fixes on the same signature
  means *stop and think*, not "try a third agent". That's why recurrence
  escalates instead of retrying forever.
- **Not a monitoring system.** No SLOs, no historical dashboards, no paging
  integration. It's a babysitter for a session, not Datadog. For real on-call,
  wire a real pager.
- **Needs a reachable signal.** If it can't read logs *and* can't run a health
  check, it can't observe — it escalates and stops (a blind babysitter is worse
  than none).

## Three autonomy modes (default: **full-auto**)

| mode | on trouble |
|---|---|
| **full-auto** | sub-agent fixes → **deploy** → verify → loop. Escalate only on the triggers below. |
| **fix-ask-deploy** | sub-agent prepares + commits the fix, then **escalates for approval** before deploying. |
| **observe** | never touches code or deploy. Detects trouble → **escalates**. You fix. |

Mode is chosen at setup and stored in `config.json`; `/babysit resume` keeps it.

## State on disk (`.babysit/` in the target project — gitignored)

```
.babysit/
  config.json     # log_cmd, trouble-definition, deploy_cmd, interval, mode, guardrails
  state.json      # iteration #, log cursor, open incidents, per-signature fix attempts, deploy history, status
  babysit.log     # append-only audit trail (one line per event)
  incidents/      # one file per escalation: logs excerpt + classification + agent summary + deploy result
  alert.sh        # escalation sound/notify loop (written at setup)
  alert.pid       # PID of a running alert loop (absent = silent)
  alert.stop      # touch this to silence the alert; remove to allow it again
```

Everything the loop needs lives here. **Each tick re-reads disk, not the
conversation** — so context never accumulates across hours of ticking. This is
the core context-economy trick; honour it (don't re-summarise prior ticks into
context, read `state.json`).

## What counts as a problem (`trouble_definition`)

Concrete, in priority order — match any → it's a problem:
1. **Health check fails** — `health_cmd` exits non-zero, or `health_url` is not 2xx.
2. **Error patterns** — new log lines matching the user's regex/signatures
   (e.g. `FATAL`, `panic:`, `Traceback`, `5\d\d `, `OOMKilled`, `connection refused`).
3. **Error-rate threshold** — matches/min over the user's limit.
4. **Crash/restart loop** — repeated process restarts in the window.

Only **new** lines (since `state.log_cursor`) count, so a pre-existing error
logged once at boot doesn't re-trigger every tick.

---

## Phase 0 — Resolve what to do

Read the argument the skill was invoked with (the text after `/babysit`, or the
user's stated intent), then:

- `stop` → **STOP** (below). `status` → **STATUS**. `resume` → re-arm an existing config.
- No `.babysit/config.json` → **SETUP** (first run).
- Otherwise → **ITERATE** (one tick; this is what `/loop` re-fires).

## Phase 1 — SETUP (first run only)

1. **Gather config.** Prefer parsing the invocation / nearby notes; ask only what's
   missing, via **one** `AskUserQuestion` (≤4 questions, don't interrogate):
   - `project_dir` — repo to fix in (default: cwd).
   - `log_cmd` — a shell command that prints recent logs (see the adapter section).
     If using a logs MCP instead, resolve the app/resource id once and note the tool.
   - `health_cmd` and/or `health_url` — optional but strongly recommended; it's
     the cheapest, least-ambiguous signal and the post-deploy verifier.
   - `trouble_definition` — patterns / thresholds (see above). Get something
     concrete; a vague definition is the #1 failure mode.
   - `deploy_cmd` — the shell command that ships a fix (see the adapter section).
     If using a deploy MCP instead, note the resource id, the deploy tool, and how
     to poll it to a terminal state. Optionally `rollback_cmd`.
   - `commit_branch` — branch the fix is committed to (default: current branch).
     Heed the global rule about not committing to `main` *unless* `main` is the
     deploy branch — for a prod hotfix loop it often is; confirm, don't assume.
   - `interval` — e.g. `5m` (this is the `/loop` cadence, "every N").
   - `mode` — full-auto | fix-ask-deploy | observe (default **full-auto**).
   - **Guardrails** (defaults, override on request):
     `max_fix_attempts_per_signature: 2`, `max_deploys_per_hour: 4`,
     `max_blind_ticks: 3` (consecutive ticks with no readable signal → escalate),
     `max_iterations: null` (until stopped).
2. **Write** `.babysit/config.json` and seed `.babysit/state.json`
   (`{iteration:0, log_cursor:null, status:"baseline", incidents:[], signatures:{}, deploys:[], loop_armed:false}`).
3. **Write `.babysit/alert.sh`** (script below) and ensure `.babysit/` is in the
   target project's `.gitignore` (append if absent).
4. **Baseline tick (observe-only, no fix/deploy).** Read current logs, set
   `log_cursor` to "now", note what *normal* looks like. This stops babysit from
   firing on a pre-existing error the moment it starts. Record the baseline.
5. **Arm the cadence.** Invoke the native **`loop`** skill with
   `args: "<interval> /babysit"` (e.g. `5m /babysit`) so `/babysit` re-fires
   every interval, then set `state.loop_armed = true`. If programmatic arming
   isn't available, fall back to: tell the user to run `/loop <interval> /babysit`,
   and/or self-pace with `ScheduleWakeup` (prompt `"/loop /babysit"`).
   **Idempotency:** never arm twice — if `loop_armed` is already true, skip.
6. **Report**: mode, interval, what counts as trouble, how to `stop`/`status`.
   Then stop this turn — the loop takes over.

## Phase 2 — ITERATE (one tick — runs every interval)

Keep this tick **cheap and shallow** — its job is triage, not investigation.

1. **Load** `config.json` + `state.json` from disk. `iteration++`.
2. **Fetch only new logs** since `state.log_cursor` (run `log_cmd`); advance the cursor.
   Run `health_cmd`/`health_url` if configured.
   - **Signal unreachable** (logs error AND no health signal): `blind_ticks++`.
     If `blind_ticks ≥ max_blind_ticks` → **ESCALATE** ("can't observe"). Else
     record and return (try again next tick).
3. **Classify** against `trouble_definition`. Healthy → reset `blind_ticks`,
   write a heartbeat line, return. (Don't spend tokens; this is the common path.)
4. **Problem** → compute a normalized **error signature** (strip timestamps,
   ids, line numbers) to track recurrence. Then:
   - **Recurrence guard:** if `signatures[sig].fix_attempts ≥ max_fix_attempts`
     → **ESCALATE** ("fix didn't hold"). Do **not** try again.
   - **Rate guard:** if deploys in the last hour ≥ `max_deploys_per_hour`
     → **ESCALATE** ("deploy storm") and back off.
   - **mode = observe** → **ESCALATE** ("trouble, you fix"). Done.
   - Otherwise **delegate the fix** (Phase 3).
5. After Phase 3 returns, **act on the verdict** (Phase 4).
6. **Record** the tick to `state.json` + append `babysit.log`. Return — `/loop`
   re-fires after the interval.

## Phase 3 — Delegate the fix to a sub-agent (context economy)

**Never diagnose/fix in the main loop** — that bloats context across hours.
Spawn one `Agent` (subagent_type `general-purpose`; `Explore` first if the cause
is unclear) with a **bounded** brief:

> You are fixing one production incident. Working dir: `<project_dir>`, deploy
> branch `<commit_branch>`.
> **Logs (new lines this tick):** `<excerpt>`. **Signature:** `<sig>`.
> **Health:** `<health output>`. **Trouble definition:** `<…>`.
> Do: reproduce/locate root cause → make the **smallest** correct fix → run the
> project's tests/build/linters if they exist → commit to `<commit_branch>` with
> a clear message. Do **NOT** deploy. Do **NOT** make schema/data migrations,
> touch secrets, or do anything irreversible — if the fix needs that, STOP and
> report `needs_human`.
> Return ONLY this (your final message is data, not prose):
> `fixed: <bool>` · `root_cause: <one line>` · `files: <list>` ·
> `commit: <sha|none>` · `confidence: <low|med|high>` ·
> `needs_human: <bool>` · `reason: <if needs_human or not fixed>`.

Only that structured summary returns to the loop. The full investigation stays
in the sub-agent's context and is discarded — the babysitter stays light.

## Phase 4 — Act on the verdict

- `needs_human:true` OR `fixed:false` OR `confidence:low` → **ESCALATE** with the
  agent's `reason`. Don't deploy a fix you don't trust.
- **mode = fix-ask-deploy** and `fixed:true` → **ESCALATE for approval**
  (`status:"pending-approval"`, stash the commit sha). Deploy only after the
  operator approves on a later tick.
- **mode = full-auto** and `fixed:true`, `confidence:med|high` → **DEPLOY**:
  run `deploy_cmd` (or your deploy MCP's deploy, polled to a terminal state).
  Record `{ts, sig, commit, result}` in `state.deploys`.
  - **Verify** (the deploy isn't done until it's verified): wait for it to
    settle, fetch fresh logs + health.
    - **Healthy** → mark incident resolved, `signatures[sig].fix_attempts++`
      stays as the count that worked; clear status. 🎉
    - **Still broken / worse than baseline** → `signatures[sig].fix_attempts++`;
      if now `≥ max_fix_attempts` → **ESCALATE** ("fix didn't hold") and, if a
      one-step rollback exists (`rollback_cmd` / re-deploy the prior good build),
      **roll back** and say so. If no safe rollback, escalate loudly and stop
      touching prod.

## ESCALATE — "call me until I come"

This is the only path that makes noise. Trigger it for the things below; for
anything else, keep quiet and keep working.

**Escalation triggers** (the "100% needs a human" set):
- Sub-agent `needs_human` / no fix / low confidence.
- Same signature unresolved after `max_fix_attempts` fixes.
- Deploy command/MCP failed, or post-deploy health is **worse** than baseline.
- Security signal in logs (auth bypass, leaked secret, active exploit) — escalate
  **immediately**, before any fix.
- Data-loss / irreversible risk detected.
- `blind_ticks ≥ max_blind_ticks` (can't observe).
- `max_deploys_per_hour` tripped (thrash protection).
- `mode = observe` (any problem) or `mode = fix-ask-deploy` (fix ready → approval).

**How to escalate:**
1. Write the incident to `.babysit/incidents/<iso-ts>-<sig>.md` (log excerpt,
   classification, agent summary, deploy result, recommended human action).
2. Fire the `PushNotification` tool with a one-line summary + the incident path.
3. **Start the sound** (only if not already ringing — check `alert.pid`):
   `rm -f .babysit/alert.stop` then run `.babysit/alert.sh "<short reason>"` with
   **run_in_background: true**. It beeps + `notify-send`s every 30s until
   silenced or capped (20 min), so you can't sleep through it.
4. Set `state.status = "escalated"` and **stop auto-fixing this signature** — the
   loop may keep *observing* on its cadence, but it will not re-attempt the wall
   it just hit. Don't spin.
5. **When the operator returns** (next interactive turn while escalated):
   `touch .babysit/alert.stop` to silence the alarm, summarise the incident, take
   their decision (approve deploy / hand back to auto / stop), clear the status.

### `.babysit/alert.sh` (write this verbatim at setup)

```bash
#!/usr/bin/env bash
# babysit escalation: beep + desktop-notify every 30s until silenced or capped.
# silence: `touch .babysit/alert.stop`  ·  re-arm: remove that file.
set -u
DIR="$(cd "$(dirname "$0")" && pwd)"
MSG="${1:-babysit needs you}"
MAX="${2:-40}"                       # 40 * 30s ≈ 20 min hard cap (no runaway)
SND="/usr/share/sounds/freedesktop/stereo/alarm-clock-elapsed.oga"
echo $$ > "$DIR/alert.pid"
trap 'rm -f "$DIR/alert.pid"' EXIT
play() {
  if   command -v pw-play >/dev/null 2>&1;            then pw-play "$SND" 2>/dev/null
  elif command -v paplay  >/dev/null 2>&1;            then paplay  "$SND" 2>/dev/null
  elif command -v canberra-gtk-play >/dev/null 2>&1;  then canberra-gtk-play -i alarm-clock-elapsed 2>/dev/null
  elif command -v aplay   >/dev/null 2>&1;            then aplay -q "$SND" 2>/dev/null
  else printf '\a'; fi
}
for _ in $(seq 1 "$MAX"); do
  [ -f "$DIR/alert.stop" ] && break
  command -v notify-send >/dev/null 2>&1 && notify-send -u critical "🔔 babysit" "$MSG"
  play
  sleep 30
done
rm -f "$DIR/alert.pid"
```

## STOP / STATUS / RESUME

- **STOP** (`/babysit stop`): `touch .babysit/alert.stop` (silence), cancel the
  `/loop` (stop the loop skill / drop the ScheduleWakeup), set
  `state.status="stopped"`, print a session summary (ticks, incidents, deploys).
- **STATUS** (`/babysit status`): print mode, interval, last few ticks, open
  incidents, recent deploys, whether the alarm is ringing. No side effects.
- **RESUME** (`/babysit resume`): re-arm the cadence for an existing config
  (e.g. after a restart) without redoing setup.

## How to do it wrong vs right

❌ Diagnose and edit in the main loop → context balloons over hours; the loop
   gets slower and dumber each tick.
✅ Triage cheaply in the loop; delegate every fix to a fresh sub-agent; keep only
   the structured verdict.

❌ Re-trigger on the same boot-time error every single tick.
✅ Track a `log_cursor`; only **new** lines count.

❌ Retry a failing fix a third, fourth, fifth time.
✅ Two strikes on a signature → escalate. Repetition without new information is
   not progress.

❌ Deploy a `low`-confidence fix because the loop "should keep moving".
✅ Low confidence / `needs_human` / no rollback path → make noise, stop, wait.

❌ Beep forever / leave a runaway background process.
✅ Capped alert (20 min) + a `alert.stop` file + PID file; silenced the moment
   the operator engages.

## Senior-operator self-check (before each deploy / escalation)

- Is "trouble" real (matches the definition on **new** lines) or am I chasing noise?
- Is this fix the *smallest* correct change, committed to the right branch?
- Can I undo this deploy in one step if it's wrong? If not — should I be deploying
  at all unattended?
- Have I hit this exact wall before? (Check `signatures[sig]`.) If yes — escalate.
- Am I about to do something irreversible or security-sensitive? → escalate, never auto.
