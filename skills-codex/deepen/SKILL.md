---
name: deepen
description: >
  Find shallow modules (interface nearly as complex as their implementation)
  and propose deepening refactors. Optionally explores 2-3 interface
  variants in parallel via three concurrent `codex exec -` subprocesses
  ("Design It Twice"). Use for architectural friction: hard-to-test
  modules, tangled callers, refactors that feel obvious but the right
  shape isn't. Triggers: "deepen", "/deepen", "improve architecture",
  "refactor this module", "make X more testable".
when_to_use: >
  An existing codebase where some modules feel wrong — tests have to mock
  too much, changes ripple across many callers, naming feels off. Output
  is a small list of deepening opportunities + (on demand) 2-3 parallel
  interface designs. Do NOT use for green-field code or one-off bug fixes
  (use /diagnose).
allowed-tools: [Bash, Glob, Grep, Read, Edit, Write]
---

# Deepen (Codex variant)

Surface architectural friction; propose **deepening opportunities**.

This is the **Codex CLI variant**. User-facing prompts are numbered TUI input; parallel sub-agent exploration uses 3 concurrent `codex exec -` subprocesses instead of the `Agent` tool. Shared references (`references/architecture-language.md`, `references/deepening-patterns.md`, `references/parallel-interface-design.md`) are symlinked from the Claude variant tree via `install-codex.sh`.

> Adapted from mattpocock/skills `improve-codebase-architecture` (MIT). Vocabulary is Ousterhout-derived.

> **Letter = spirit.** If a rule blocks you from reaching the goal it was
> written for, the rule is wrong, not the goal.

## Weaknesses and when NOT to use

- **Not for green-field code.** Architectural friction needs callers, tests, and history.
- **Not for one-off bug fixes.** `/diagnose` owns the bug loop; if a bug surfaces architectural pain, `/diagnose` Phase 6 hands off here.
- **Doesn't refactor for you.** Output is candidates + (optional) designs. The actual refactor is downstream.
- **Vocabulary is opinionated.** Module / Interface / Seam / Adapter (not "component" / "service" / "API" / "boundary"). Stick to it.
- **Non-interactive mode.** Phase 2 candidate picking and Phase 4 ADR offers need TUI. From `codex exec` without TTY, fail explicitly.

## How to do it wrong vs right

### Module depth

❌ **Wrong:** Extract every pure function for "testability"; bugs hide in caller composition.
✅ **Right:** Group functions that change together behind one small interface. Test through the interface.

### Seam discipline

❌ **Wrong:** Define a port/adapter for a dependency with only one implementation. Just indirection.
✅ **Right:** **One adapter = hypothetical seam. Two adapters = real seam.**

### Skipping the deletion test

❌ **Wrong:** Declare a module necessary because it "encapsulates X".
✅ **Right:** **Apply the deletion test.** Delete it mentally. If complexity vanishes, it was pass-through.

### Re-litigating prior decisions

❌ **Wrong:** Propose refactor contradicting an ADR without evidence.
✅ **Right:** Only flag ADR-contradicting candidates when friction is real enough to warrant revisit.

## What the skill does (step by step)

### Phase 1 — Explore

Walk the codebase looking for shallow modules. Apply the deletion test to each suspect (`references/architecture-language.md`).

Read `docs/adr/*.md` if present — extract titles to avoid proposing already-decided-against refactors.

### Phase 2 — Present candidates

Numbered list. For each candidate:

- **Files** — which modules.
- **Problem** — concrete symptoms (mocks count, ripple radius, etc.).
- **Sketch of the deepening** — what changes, where the new seam sits.
- **Benefits** — locality, leverage, testability.

Use vocabulary from `references/architecture-language.md` consistently — no drift into "service" / "component" / "boundary".

Surface as a numbered TUI prompt: "Which would you like to explore? <numbers> + Skip."

### Phase 3 — (Optional) Design It Twice — 3 parallel `codex exec -`

If user picks a candidate, run 3 parallel sub-agents per `references/parallel-interface-design.md`:

```bash
# Write 3 different briefs to temp files
echo "$BRIEF_MINIMAL"   > /tmp/deepen-A.txt   # min interface, max leverage
echo "$BRIEF_FLEXIBLE"  > /tmp/deepen-B.txt   # flexibility, extension points
echo "$BRIEF_COMMON"    > /tmp/deepen-C.txt   # optimise common caller

# 3 concurrent codex exec - invocations
{ codex exec - < /tmp/deepen-A.txt > /tmp/deepen-A.out & } 2>&1
{ codex exec - < /tmp/deepen-B.txt > /tmp/deepen-B.out & } 2>&1
{ codex exec - < /tmp/deepen-C.txt > /tmp/deepen-C.out & } 2>&1
wait
```

Each brief contains: file paths, coupling details, dependency category from `references/deepening-patterns.md`, what sits behind the seam, the design constraint.

Each sub-agent returns: interface (types + invariants + error modes + ordering), usage example, what's hidden, dependency strategy + adapters, trade-offs.

Present sequentially (A → B → C), compare in prose by depth / locality / seam placement, recommend one or a hybrid. Be opinionated.

Cap at 3 sub-agents. If user wants a 4th angle, re-run.

### Phase 4 — Capture and hand off

After candidate (and optional design) chosen:

- **If hard-to-reverse + surprising + real trade-off** — offer to create `docs/adr/NNNN-slug.md` per the shared ADR format (clarify's `references/adr-format.md`, also symlinked in this skill if both installed). Three-line ADR is enough.
- **Print a summary** to stdout: chosen candidate + the design. The user takes it downstream (`mattpocock:tdd`, `codex exec`-driven build, manual).

The skill does not edit code itself.

## Outputs

- Candidate list (Phase 2 stdout).
- Optional 3 interface designs + recommendation (Phase 3 stdout).
- Optional ADR (Phase 4 user-approved).

No file edits to the codebase itself.

## Rules

### Commonality (vocabulary is the shared artifact)
The Ousterhout vocabulary is opinionated for consistency between engineers. Drifting defeats the skill.

### Prior commitment (apply the deletion test)
Skipping the deletion test means proposing on vibes, not evidence.

### Authority (ADRs are user decisions)
Only contradict an ADR when the friction is genuine and you'd defend reopening it.

### Social proof (Design It Twice)
Per Ousterhout: first idea is rarely best. Parallel exploration with different constraints exposes blind spots.

## Self-check before delivering candidates

- Did each candidate pass the **deletion test**?
- Did you use `architecture-language.md` vocabulary consistently?
- Were existing ADRs read and respected?
- Can a reader sketch the new shape from your description?
- If Phase 3 ran, did the 3 designs differ **radically**?

If "no" on any item — redo.
