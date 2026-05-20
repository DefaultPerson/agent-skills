---
name: diagnose
description: >
  Disciplined debug loop for hard bugs and performance regressions:
  build a feedback loop FIRST, then reproduce → ranked hypotheses →
  instrument → fix → regression-test → cleanup. Use when a bug is
  non-trivial, intermittent, or has resisted ad-hoc inspection. For
  one-line typos or obvious errors — just fix it; this skill is overkill.
  Triggers: "diagnose", "/diagnose", "debug this", "why is this broken",
  "почини баг", "разберись", "performance regression".
when_to_use: >
  A bug or perf regression that you cannot fix by reading the code for
  five minutes. The skill enforces feedback-loop construction before
  hypothesising, which is the cheapest place to be wrong.
allowed-tools: [Bash, Glob, Grep, Read, Edit, Write]
---

# Diagnose (Codex variant)

A discipline for hard bugs. Skip phases only when explicitly justified.

This is the **Codex CLI variant**. Behaviourally identical to the Claude variant — user-facing prompts use numbered TUI input instead of `AskUserQuestion`. Shared references (`references/`) are symlinked from the Claude variant tree (via `install-codex.sh`); content is the same.

> **Letter = spirit.** If a rule blocks you from reaching the goal it was
> written for, the rule is wrong, not the goal. Don't look for a wording
> loophole — ask what the rule is protecting, and protect that.

## Weaknesses and when NOT to use

- **Overkill for trivial bugs.** If `grep` finds the bug in 30 seconds, just fix it.
- **Not for feature work.** Use `/clarify` for missing features.
- **Cannot debug what you can't reach.** If no logs, no traces, no repro environment — the skill stops at Phase 1.
- **No replacement for taste.** Phase 3 ranking depends on domain instinct.
- **Non-interactive mode (`codex exec` invocation of `/diagnose` itself).** Phase 3 user check-in and any AskUserQuestion-style prompts need TUI. From `codex exec` without TTY, fail with explicit error rather than auto-proceeding.

## How to do it wrong vs right

### Building a feedback loop

❌ **Wrong:** Stare at the code, guess, edit, hope.

✅ **Right:** Construct a fast deterministic pass/fail signal first. Once the loop is reliable, every change is an experiment with a clear result.

### Hypothesis discipline

❌ **Wrong:** Single hypothesis, edit, fail, switch to another, edit, fail.

✅ **Right:** Write 3-5 ranked hypotheses BEFORE testing any. Each falsifiable. Show the list to the user via numbered TUI — they often re-rank from operational context.

### Regression test

❌ **Wrong:** Fix, eyeball verify, move on.

✅ **Right:** Test first at the correct seam, watch fail, apply fix, watch pass. No correct seam = that's the finding.

### Debug log cleanup

❌ **Wrong:** Sprinkled `print(...)` calls leak into the PR.

✅ **Right:** Tag every probe with a unique prefix `[DEBUG-a4f2]`. Cleanup = single grep.

## What the skill does (step by step)

### Phase 1 — Build a feedback loop

**This is the skill.** Spend disproportionate effort here.

Ways to construct one — try in roughly this order:

1. **Failing test** at whatever seam reaches the bug.
2. **Curl / HTTP script** against a running dev server.
3. **CLI invocation** with fixture input, diffing stdout against a known-good snapshot.
4. **Headless browser script** (Playwright / Puppeteer).
5. **Replay a captured trace.**
6. **Throwaway harness.**
7. **Property / fuzz loop.**
8. **Bisection harness.** (`git bisect run` over the loop.)
9. **Differential loop.**
10. **HITL bash script.** Last resort.

Iterate on the loop itself: make it faster, sharper, more deterministic. A 2-second deterministic loop beats a 30-second flaky one.

For **non-deterministic bugs:** raise the reproduction rate to debuggable (50%+); don't insist on clean repro.

If you genuinely cannot build a loop — stop, say so, list what you tried, ask the user for environment / artifact / instrumentation permission. **Do not proceed without a loop.**

### Phase 2 — Reproduce

Run the loop. Watch the bug appear. Confirm it matches what the user described, is reproducible, and the symptom is captured.

### Phase 3 — Hypothesise

Generate 3-5 ranked hypotheses BEFORE testing. Each falsifiable:

> "If <X> is the cause, then <changing Y> will make the bug disappear / <changing Z> will make it worse."

Show as a numbered TUI list. Wait for user re-ranking (or proceed with your ranking if AFK).

### Phase 4 — Instrument

Each probe maps to a specific prediction. Change one variable at a time.

Preference order: debugger / REPL > targeted logs > "log everything and grep" (never).

Tag debug logs with `[DEBUG-a4f2]` (unique per session). Cleanup = single grep.

**Perf branch:** establish baseline measurement first, bisect second. Logs are usually wrong for perf.

### Phase 5 — Fix + regression test

Write the regression test BEFORE the fix — but only if there is a **correct seam** for it (one that exercises the real bug pattern as it occurs at the call site).

If no correct seam exists, that itself is the finding — flag for Phase 6 as a `/deepen` candidate.

If a correct seam exists: failing test → fix → passing test → re-run Phase 1 loop against un-minimised scenario.

### Phase 6 — Cleanup + post-mortem

- [ ] Original repro no longer reproduces.
- [ ] Regression test passes (or absence-of-seam is documented).
- [ ] All `[DEBUG-...]` removed via single grep.
- [ ] Throwaway prototypes deleted or clearly marked.
- [ ] Commit / PR message states the correct hypothesis.

**Then ask: what would have prevented this bug?** If architectural change is the answer — surface a `/deepen` candidate.

## Outputs

- Regression test at correct seam (or note that no correct seam exists).
- The fix.
- Commit / PR message naming the correct hypothesis.
- Optional `/deepen` candidate if the bug surfaced architectural friction.

## Rules

### Commonality (the loop is the shared artifact)
The feedback loop makes the bug findable for anyone — not just you in this session.

### Prior commitment
You committed to the loop in Phase 1. Skipping ahead because "I have a strong feeling" is anchoring.

### Authority (the user is the senior debugger)
When ranked hypotheses go to the user, they may re-rank from operational context you don't have.

## Self-check before declaring the fix done

- Did Phase 1 produce a loop you'd recommend to another engineer chasing the same bug?
- Are all 3-5 hypotheses recorded (even rejected ones)?
- Regression test exercises the **real bug pattern** at the **right seam**?
- All `[DEBUG-...]` removed via single grep?
- Commit/PR message names the correct hypothesis and how it was confirmed?
- If no correct seam — captured?

If "no" on any item — redo.
