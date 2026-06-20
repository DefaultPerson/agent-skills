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
  hypothesising, which is the cheapest place to be wrong. Do NOT use
  for trivial typos, immediately-obvious errors, or feature work.
allowed-tools: [Bash, Glob, Grep, Read, Edit, Write, AskUserQuestion]
---

# Diagnose

A discipline for hard bugs. Skip phases only when explicitly justified.

> **Letter = spirit.** If a rule blocks you from reaching the goal it was
> written for, the rule is wrong, not the goal. Don't look for a wording
> loophole — ask what the rule is protecting, and protect that.

## Weaknesses and when NOT to use

- **Overkill for trivial bugs.** If `grep` finds the bug in 30 seconds, just fix it. The 6-phase discipline pays off only when the bug is genuinely hard.
- **Not for feature work.** If the "bug" is "we don't yet implement X", that's a missing feature, not a bug. Use `/blueprint` to decompose, not `/diagnose`.
- **Cannot debug what you can't reach.** If the bug only manifests in production and you have no signal source (logs, traces, repro environment), the skill stops at Phase 1 — you can't proceed without a feedback loop.
- **No replacement for taste.** Phase 3 ranking depends on domain instinct. The skill structures the work; it doesn't supply the gut.

## How to do it wrong vs right

### Building a feedback loop

❌ **Wrong:** Stare at the code, guess what's wrong, edit, hope.
- No signal to confirm the edit fixed anything.
- "Sometimes works now" = no fix, just lucky.

✅ **Right:** Construct a fast deterministic pass/fail signal first. Failing test, curl script, CLI diff, headless browser, trace replay. Once the loop is reliable, every change is an experiment with a clear result.

### Hypothesis discipline

❌ **Wrong:** Single hypothesis ("must be the cache"), edit, fail, switch to another single hypothesis, edit, fail.
- Anchors on the first plausible idea.
- No falsifiability — "fixed it" indistinguishable from "moved the symptom".

✅ **Right:** Write 3-5 ranked hypotheses BEFORE testing any. Each one falsifiable: "If X is the cause, then changing Y will make the bug disappear / changing Z will make it worse." Show the list to the user — they often know which is most likely from context.

### Regression test

❌ **Wrong:** Apply the fix; manually verify the symptom is gone; move on.
- Next refactor reintroduces the bug because nothing locks the fix down.

✅ **Right:** Write the regression test FIRST at the correct seam, watch it fail, apply fix, watch it pass. If no correct seam exists — note it. That's itself a finding the codebase architecture needs work.

### Debug log cleanup

❌ **Wrong:** Sprinkle `console.log(...)` / `print(...)` across the code; forget half of them during cleanup; PR ships with leftover noise.

✅ **Right:** Tag every probe with a unique prefix like `[DEBUG-a4f2]`. Cleanup = `grep -r '\[DEBUG-a4f2\]' src/ -l | xargs <editor>` to remove. One grep, no leftovers.

## What the skill does (step by step)

### Phase 1 — Build a feedback loop

**This is the skill.** Everything else is mechanical. If you have a fast, deterministic, agent-runnable pass/fail signal for the bug, you will find the cause — bisection, hypothesis-testing, and instrumentation all just consume that signal. If you don't have one, no amount of staring at code will save you.

Spend disproportionate effort here. **Be aggressive. Be creative. Refuse to give up.**

#### Ways to construct one — try in roughly this order

1. **Failing test** at whatever seam reaches the bug — unit, integration, e2e.
2. **Curl / HTTP script** against a running dev server.
3. **CLI invocation** with fixture input, diffing stdout against a known-good snapshot.
4. **Headless browser script** (Playwright / Puppeteer) driving the UI, asserting on DOM / console / network.
5. **Replay a captured trace.** Save a real network request / payload / event log to disk; replay it through the code path in isolation.
6. **Throwaway harness.** Spin up a minimal subset (one service, mocked deps) that exercises the bug code path with a single function call.
7. **Property / fuzz loop.** If the bug is "sometimes wrong output", run 1000 random inputs and look for the failure mode.
8. **Bisection harness.** If the bug appeared between two known states (commit, dataset, version), automate "boot at state X, check, repeat" so you can `git bisect run` it.
9. **Differential loop.** Run the same input through old-version vs new-version (or two configs) and diff outputs.
10. **HITL bash script.** Last resort. If a human must click, drive *them* with a structured loop. Captured output feeds back to you.

Build the right feedback loop, and the bug is 90% fixed.

#### Iterate on the loop itself

Treat the loop as a product. Once you have *a* loop, ask:

- Can I make it faster? (Cache setup, skip unrelated init, narrow test scope.)
- Can I make the signal sharper? (Assert on the specific symptom, not "didn't crash".)
- Can I make it more deterministic? (Pin time, seed RNG, isolate filesystem, freeze network.)

A 30-second flaky loop is barely better than no loop. A 2-second deterministic loop is a debugging superpower.

#### Non-deterministic bugs

The goal is not a clean repro but a **higher reproduction rate**. Loop the trigger 100×, parallelise, add stress, narrow timing windows, inject sleeps. A 50%-flake bug is debuggable; 1% is not — keep raising the rate until it's debuggable.

#### When you genuinely cannot build a loop

Stop and say so explicitly. List what you tried. Ask the user for: (a) access to an environment that reproduces it, (b) a captured artifact (HAR file, log dump, core dump, screen recording with timestamps), or (c) permission to add temporary production instrumentation. **Do not proceed to hypothesise without a loop.**

Do not proceed to Phase 2 until you have a loop you believe in.

### Phase 2 — Reproduce

Run the loop. Watch the bug appear.

Confirm:

- [ ] The loop produces the failure mode the **user** described — not a different failure that happens to be nearby. Wrong bug = wrong fix.
- [ ] The failure is reproducible across multiple runs (or, for non-deterministic bugs, reproducible at a high enough rate to debug against).
- [ ] You have captured the exact symptom (error message, wrong output, slow timing) so later phases can verify the fix actually addresses it.

Do not proceed until the bug reproduces.

### Phase 3 — Hypothesise

Generate **3-5 ranked hypotheses** before testing any of them. Single-hypothesis generation anchors on the first plausible idea.

Each hypothesis must be **falsifiable**: state the prediction it makes.

> Format: "If <X> is the cause, then <changing Y> will make the bug disappear / <changing Z> will make it worse."

If you cannot state the prediction, the hypothesis is a vibe — discard or sharpen it.

**Show the ranked list to the user before testing.** They often have domain knowledge that re-ranks instantly ("we just deployed a change to #3"), or know hypotheses they've already ruled out. Cheap checkpoint, big time saver. Don't block on it — proceed with your ranking if the user is AFK.

### Phase 4 — Instrument

Each probe must map to a specific prediction from Phase 3. **Change one variable at a time.**

Tool preference:

1. **Debugger / REPL inspection** if the env supports it. One breakpoint beats ten logs.
2. **Targeted logs** at the boundaries that distinguish hypotheses.
3. Never "log everything and grep".

**Tag every debug log** with a unique prefix, e.g. `[DEBUG-a4f2]`. Cleanup at the end becomes a single grep. Untagged logs survive; tagged logs die.

**Perf branch.** For performance regressions, logs are usually wrong. Instead: establish a baseline measurement (timing harness, `performance.now()`, profiler, query plan), then bisect. Measure first, fix second.

### Phase 5 — Fix + regression test

Write the regression test **before the fix** — but only if there is a **correct seam** for it.

A correct seam is one where the test exercises the **real bug pattern** as it occurs at the call site. If the only available seam is too shallow (single-caller test when the bug needs multiple callers, unit test that can't replicate the chain that triggered the bug), a regression test there gives false confidence.

**If no correct seam exists, that itself is the finding.** Note it. The codebase architecture is preventing the bug from being locked down. Flag for Phase 6 cleanup — this might be a `/deepen` candidate.

If a correct seam exists:

1. Turn the minimised repro into a failing test at that seam.
2. Watch it fail.
3. Apply the fix.
4. Watch it pass.
5. Re-run the Phase 1 feedback loop against the original (un-minimised) scenario.

### Phase 6 — Cleanup + post-mortem

Required before declaring done:

- [ ] Original repro no longer reproduces (re-run the Phase 1 loop).
- [ ] Regression test passes (or absence-of-seam is documented).
- [ ] All `[DEBUG-...]` instrumentation removed (`grep` the prefix).
- [ ] Throwaway prototypes deleted (or moved to a clearly-marked debug location).
- [ ] The hypothesis that turned out correct is stated in the commit / PR message — so the next debugger learns.

**Then ask: what would have prevented this bug?** If the answer involves architectural change (no good test seam, tangled callers, hidden coupling), surface a `/deepen` candidate with specifics. Make the recommendation **after** the fix is in — you have more information now than when you started.

## Outputs

- A passing regression test at the correct seam (or a documented note that no correct seam exists).
- The fix itself.
- A commit / PR message stating the correct hypothesis.
- (Optional) A `/deepen` candidate if the bug surfaced architectural friction.

## Rules

### Commonality (the loop is the shared artifact)

The feedback loop is what makes the bug findable for anyone — not just you in this session. Skip building one and the fix becomes private knowledge no one else can verify or extend.

### Prior commitment

You committed to the loop in Phase 1. Skipping ahead because "I have a strong feeling about it" is exactly the anchoring trap that ranked-hypotheses guards against. Stay disciplined.

### Authority (the user is the senior debugger)

When ranked hypotheses go to the user (Phase 3), they may re-rank or add a hypothesis from context you don't have ("we just rolled out X"). Honor that re-ranking; you have less information than they do about recent operational changes.

## Self-check before declaring the fix done

- Did Phase 1 produce a loop you'd recommend to another engineer chasing the same bug?
- Are all 3-5 hypotheses recorded (even the rejected ones), so the post-mortem shows which were ruled out?
- Is the regression test exercising the **real bug pattern** at the **right seam**, not a shallow proxy?
- All `[DEBUG-...]` removed via single grep?
- Commit/PR message names the correct hypothesis and how it was confirmed?
- If no correct seam existed for the regression test, is that captured (so someone can revisit architecture later)?

If "no" on any item — redo, don't ship.
