# <Goal Title>

> Charter compiled by `/goal-prep`. The actual execution loop runs
> through the host's native `/goal` command (Claude Code or Codex CLI).
> The native /goal evaluator does **not** read this file — it only sees
> conversation context. Use this charter as your own reference and to
> paste sections into the conversation when starting /goal.

## Objective

<Bounded statement of what this goal is trying to accomplish. Not an
infinite mission. Specific enough that the completion condition can be
checked observably.>

## Original Request

<Shortest faithful copy of what the user asked for. Preserve plan details
verbatim if the user provided them.>

## Intake Summary

- Input shape: `vague | specific | existing_plan | recovery | audit`
- Audience: <beneficiary or "unknown">
- Authority: `requested | approved | inferred | needs_approval | blocked`
- Proof type: `test | demo | artifact | metric | review | source_backed_answer | decision`
- Completion proof: <observable signal that the full original outcome is complete — this is what becomes the native /goal condition>
- Likely misfire: <how /goal could succeed at the wrong thing>
- Blind spots considered: <risks, unstated choices, success dimensions surfaced during intake>
- Existing plan facts: <user-provided steps/files/constraints/sequencing to preserve and validate, or "none">

## Goal Kind

`specific | open_ended | existing_plan | recovery | audit`

## Note on cadence

Native `/goal` is **inline-only** — it loops within a single Claude Code
session until the condition is met or the turn cap is reached. There is
no built-in daily/weekly cadence.

For long-horizon work (multi-day investigations, weekly maintenance):
either re-run `/goal-prep` daily/weekly with refined intake,
or resume the previous session with `claude --resume` (the active goal
is restored automatically as part of session state). A calendar reminder
is the recommended trigger.

## Current Tranche

<What is enough for the full owner outcome, and what is the current safe
slice? For execution goals, the default is continuous: discover enough
evidence, choose a safe implementation slice, implement it, verify it,
audit it, then immediately advance to the next safe slice until the
condition is met. Plan-only or one-slice-only stopping is valid only
when explicitly requested.>

## Non-Negotiable Constraints

<Anti-patterns block auto-seeded by `/goal-prep` from
`templates/anti-patterns/base.md` plus the kind-specific layer
(`qa.md` / `refactor.md` / `greenfield.md`). User may add or remove items;
removal must be explicit.>

## Adversarial Review

Before declaring this goal complete to native /goal:

### Step 1 — Structured completion audit

Fill in this table by inspecting current state (files, command output,
git diff). One row per requirement from `## Intake Summary`
completion_proof. Each row needs evidence (a concrete file path,
command, or commit hash) and a status.

| Requirement | Evidence | Status |
|---|---|---|
| <derive from completion_proof> | <file:line / command output / commit hash> | Complete / Partial / Missing |
| ... | ... | ... |

Verification commands actually run during this audit:

```bash
<paste the verify commands and their exit codes / last 3 output lines>
```

Reject completion if **any** row is `Partial` or `Missing` — keep
working. Evidence must be specific (e.g. `src/auth/session.ts:42`,
`pytest -q tests/ → 14 passed, exit 0`), not vague ("tests pass").

<!-- Step 2 below is CONDITIONAL: /goal-prep includes it only if the
     user opted in to cross-LLM review at Phase 0.55. If skipped,
     Step 2 (heading and body) is omitted from the emitted goal.md.
     The audit table above (Step 1) is always included. -->

### Step 2 — Adversarial review pass

After the audit table is complete and every row is `Complete`:

1. Run via Bash: `codex review --uncommitted "<prompt>"` against the dirty diff (CLI not slash command — `/codex:adversarial-review` has `disable-model-invocation: true` which blocks the Skill tool from invoking it programmatically).
2. Read findings; do not auto-apply fixes.
3. For each finding decide: address now (continue work) / log as
   follow-up (write to notes/<some>.md) / ignore (with reason).
4. Only then let native /goal mark the condition met.

Rationale: the table forces concrete evidence per requirement (the
single biggest predictor of premature completion is vague evidence).
Codex adversarial-review uses a different model with adversarial framing
to catch what the Haiku evaluator and main model both miss.

Pattern adapted from `tolibear/goalbuddy` T999 audit (MIT, attribution
in LICENSE).

## Stop Rule

Stop when the native /goal condition is met *and* the Adversarial Review
above has been performed.

Do not stop after planning, discovery, or initial scope mapping if the
user asked for working software or automation. Continue until the
condition is observably satisfied.

Do not stop because a slice needs owner input, credentials, production
access, destructive operations, or policy decisions. Log the blocker as
a note, work around it where safe, and continue. Native /goal will keep
the condition open across turns.

## Run Command

`/goal-prep` printed a three-step copy-clear-paste flow at exit:

1. Copy the `/goal <condition>, or stop after 20 turns` command on
   screen.
2. Type `/clear` to reset conversation context.
3. Paste the /goal command as your next message.

The one-line command is also saved here for later re-paste:

```bash
cat <slug-dir>/run.txt    # paste this after /clear in a fresh session
```

Native /goal auto-loops with a small-fast-model evaluator until the
condition is met or the turn cap is reached. The main model is
expected to `Read <slug-dir>/goal.md` (this file) on turn 1 — that's
how anti-patterns and the completion audit table land in conversation
context. Resume after a session ends with `claude --resume` /
`claude --continue` (Claude Code) or `codex resume` (Codex): the
active goal is restored automatically. Turn count, timer, and
token-spend baseline reset on resume.

If conversation context was lost, just re-issue `cat run.txt` and
paste — main model will Read this charter again from disk.
