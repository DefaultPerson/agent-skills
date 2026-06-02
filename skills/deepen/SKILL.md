---
name: deepen
description: >
  Find shallow modules (interface nearly as complex as their implementation)
  and propose deepening refactors — bigger implementations behind smaller
  interfaces. Optionally explores 2-3 interface variants in parallel via
  the Agent tool ("Design It Twice"). Use for architectural friction:
  hard-to-test modules, tangled callers, refactors that feel obvious but
  the right shape isn't. Triggers: "deepen", "/deepen", "improve
  architecture", "refactor this module", "make X more testable".
when_to_use: >
  An existing codebase where some modules feel wrong — tests have to mock
  too much, changes ripple across many callers, naming feels off. Output
  is a small list of deepening opportunities + (on demand) 2-3 parallel
  interface designs. Do NOT use for green-field code (no architecture
  yet) or for one-off bug fixes (use /diagnose).
allowed-tools: [Bash, Glob, Grep, Read, Edit, Write, Agent, Workflow, AskUserQuestion]
---

# Deepen

Surface architectural friction and propose **deepening opportunities** — refactors that turn shallow modules into deep ones. Aim: testability + the next reader's ability to navigate.

> Adapted from mattpocock/skills `improve-codebase-architecture` (MIT). Vocabulary is Ousterhout-derived.

> **Letter = spirit.** If a rule blocks you from reaching the goal it was
> written for, the rule is wrong, not the goal. Don't look for a wording
> loophole — ask what the rule is protecting, and protect that.

## Weaknesses and when NOT to use

- **Not for green-field code.** Architectural friction only manifests when there are callers, tests, and history. On a blank slate, just write the first version.
- **Not for one-off bug fixes.** `/diagnose` owns the bug loop; if a bug surfaces architectural pain, `/diagnose` Phase 6 hands off here.
- **Doesn't refactor for you.** Output is candidates + (optional) interface designs. Actually executing the refactor is downstream (manual / `mattpocock:tdd` / goal feature).
- **Vocabulary is opinionated.** Module / Interface / Seam / Adapter (not "component" / "service" / "API" / "boundary"). Stick to it — drift defeats the point. Full glossary in `references/architecture-language.md`.

## How to do it wrong vs right

### Module depth

❌ **Wrong:** Extract every pure function into its own file "for testability"; tests are easy to write but bugs hide in how the functions compose at the callers. No **locality**.

✅ **Right:** Group functions that change together behind one small interface. Tests cross the **interface as the test surface**; refactors inside the module don't break tests.

### Seam discipline

❌ **Wrong:** Define a port/adapter for a dependency that has only one implementation (production HTTP client). The "seam" is just indirection that costs reading.

✅ **Right:** **One adapter = hypothetical seam. Two adapters = real seam.** Introduce a port only when at least two implementations are justified (typically production + test, or two transports).

### Skipping the deletion test

❌ **Wrong:** Declare a module necessary because it "encapsulates X". Never check whether the complexity actually concentrates here.

✅ **Right:** **Apply the deletion test.** Imagine deleting the module. If complexity vanishes, it was a pass-through (delete it). If complexity reappears across N callers (multiple places start handling the same problem), the module was earning its keep.

### Re-litigating prior decisions

❌ **Wrong:** Propose a refactor that contradicts an existing ADR because "I think the ADR is wrong". The next person rejects, re-decides, writes another ADR.

✅ **Right:** **ADR conflicts:** only surface a candidate that contradicts an ADR when the friction is real enough to warrant revisiting. Mark it clearly ("contradicts ADR-0007 — but worth reopening because…"). Skip theoretical refactors an ADR forbids.

## What the skill does (step by step)

### Phase 1 — Explore

Walk the codebase via `Agent(subagent_type="Explore", ...)` with a brief like: "Identify candidates for deepening in `<path>`. For each, note: which modules, what makes it shallow (interface nearly as complex as the implementation, or tests have to mock too much, or change ripples across many callers), and which dependency category it falls into (`references/deepening-patterns.md`)."

Also read `docs/adr/*.md` if it exists — extract titles to avoid proposing refactors already decided against.

Apply the **deletion test** to anything suspected shallow. Pass = candidate. Fail = leave it.

### Phase 2 — Present candidates

Numbered list. For each candidate:

- **Files** — which modules are involved.
- **Problem** — why the current shape produces friction (specific symptoms: "tests need 5 mocks", "every caller re-implements the retry loop", etc.).
- **Sketch of the deepening** — plain English: what would change, where the new seam would sit, what would move inside the deep module.
- **Benefits** — locality (where change concentrates) + leverage (what callers gain) + testability (interface as test surface).

For ADR-conflicting candidates: mark explicitly with the ADR number and the case for revisit.

**Use `references/architecture-language.md` vocabulary throughout.** Don't drift into "service" / "boundary" / "component".

Then AskUserQuestion: "Which would you like to explore?" — options are the numbered candidates + Skip.

### Phase 3 — (Optional) Design It Twice

If the user picks a candidate, offer parallel interface exploration via `references/parallel-interface-design.md`:

1. Spawn 3 sub-agents in parallel via `Agent(subagent_type="general-purpose", ...)`, each with a different design constraint:
   - Agent A: "Minimise the interface — 1-3 entry points max, maximise leverage per entry point."
   - Agent B: "Maximise flexibility — support many use cases, extension points."
   - Agent C: "Optimise for the most common caller — make the default case trivial."
2. Each returns: interface (types + invariants + error modes + ordering), usage example, what's hidden behind the seam, dependency strategy + adapters, trade-offs.
3. Present sequentially, then compare in prose. Recommend one (or a hybrid).

**Fast path (optional).** If the `Workflow` tool is available, run the same parallel fan-out (step 1) via `Workflow({scriptPath: "workflows/design-twice.workflow.js", args: {briefs}})`, where `briefs = [{label, prompt}, ...]` are rendered from `references/parallel-interface-design.md` plus the chosen candidate. It returns the five-field design output (interface / usage / hidden / dependencies / trade-offs) schema-validated. The `Agent(subagent_type="general-purpose")` spawn above is the **default and fallback** — use it whenever `Workflow` is unavailable (it is research-preview and plan-gated, so the `Agent` path is what most runs use). If fewer than `briefs.length` designs come back (an agent failed), note the count and synthesise from what returned (≥2 is enough); with <2, retry the briefs once or fall back to the `Agent` path. Steps 2-3 (the output contract and the compare/recommend synthesis) are identical on both paths. If `scriptPath` does not resolve at runtime, pass the script via `script:` instead.

Skip Phase 3 if the user wants only the candidate list, or if the shape of the deepening is already obvious.

### Phase 4 — Capture and hand off

After candidate (and optional design) is chosen:

- **If hard-to-reverse and surprising and a real trade-off** (mattpocock's ADR criteria) — offer to create `docs/adr/NNNN-slug.md` per `/clarify`'s `references/adr-format.md` (shared file). Three-line ADR is enough.
- **Print a summary** to stdout: chosen candidate + the design (if Phase 3 ran). The user takes it to `mattpocock:tdd`, manual implementation, or Claude Code goal.

The skill does not edit code itself. It surfaces and shapes; the actual refactor is downstream.

## Outputs

- A numbered candidate list (Phase 2 stdout).
- Optionally, 2-3 interface designs and a recommendation (Phase 3 stdout).
- Optionally, a new ADR in `docs/adr/` (Phase 4 user-approved).

No file edits to the codebase itself.

## Rules

### Commonality (vocabulary is the shared artifact)

The Ousterhout vocabulary (Module / Interface / Seam / Adapter / Depth / Locality / Leverage) is opinionated for a reason — consistency lets two engineers discuss the same refactor without re-defining terms. Drifting into "service" / "boundary" / "component" defeats the whole skill.

### Prior commitment (apply the deletion test)

In Phase 1 you committed to applying the deletion test to suspected shallow modules. Skipping it means proposing refactors based on vibes ("feels too thin") rather than evidence ("delete this and complexity reappears in N callers").

### Authority (ADRs are user decisions)

Existing ADRs were written by the user (or their team) for a reason. Contradicting them is a heavy claim. Only surface ADR-conflicting candidates when the friction is genuine and you'd defend reopening the decision in front of the original author.

### Social proof (Design It Twice)

Per Ousterhout: your first idea for an interface is rarely your best. Parallel exploration with different constraints exposes blind spots that single-agent design hides.

## Self-check before delivering candidates

- Did each candidate pass the **deletion test** (complexity actually concentrates here)?
- Did you use `references/architecture-language.md` vocabulary consistently — no "service" / "boundary" / "component"?
- Were existing ADRs read and respected (or contradictions explicitly flagged)?
- For each candidate, can a reader sketch the new shape from your description without asking what "the seam" means?
- If Phase 3 ran, did the 3 designs differ **radically** (constraint-wise), not just trivially?

If "no" on any item — redo, don't ship the candidate list.
