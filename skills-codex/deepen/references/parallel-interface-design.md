# Parallel interface design ("Design It Twice")

> Adapted from mattpocock/skills `improve-codebase-architecture/INTERFACE-DESIGN.md` (MIT). The "Design It Twice" principle is from Ousterhout — your first idea is rarely your best.

When the user has picked a deepening candidate (Phase 2) and wants alternative interfaces explored, spawn sub-agents in parallel with different design constraints.

Uses the vocabulary in `architecture-language.md` — **module**, **interface**, **seam**, **adapter**, **leverage**.

## Process

### 1. Frame the problem space

Before spawning sub-agents, write a user-facing explanation of the problem space for the chosen candidate:

- The constraints any new interface would need to satisfy
- The dependencies it would rely on, and which category they fall into (see `deepening-patterns.md`)
- A rough illustrative code sketch to ground the constraints — not a proposal, just a way to make the constraints concrete

Show this to the user, then immediately proceed to Step 2. The user reads and thinks while the sub-agents work in parallel.

### 2. Spawn sub-agents

Spawn **3 sub-agents in parallel** using the Agent tool (`subagent_type="general-purpose"`). Each must produce a **radically different** interface for the deepened module.

Prompt each sub-agent with a separate technical brief (file paths, coupling details, dependency category from `deepening-patterns.md`, what sits behind the seam). The brief is independent of the user-facing problem-space explanation in Step 1. Give each agent a different design constraint:

- **Agent A:** "Minimise the interface — aim for 1-3 entry points max. Maximise leverage per entry point."
- **Agent B:** "Maximise flexibility — support many use cases and extension points (hooks, callbacks, optional config)."
- **Agent C:** "Optimise for the most common caller — make the default case trivial. Push complexity to opt-in paths."

(Optional Agent D, only if applicable:) "Design around ports & adapters because at least two cross-seam adapters are justified."

Include `architecture-language.md` vocabulary in each brief so all 3 sub-agents name things consistently.

Each sub-agent outputs:

1. **Interface** — types, methods, params, plus invariants, ordering, error modes.
2. **Usage example** showing how callers use it.
3. **What the implementation hides** behind the seam.
4. **Dependency strategy and adapters** (see `deepening-patterns.md`).
5. **Trade-offs** — where leverage is high, where it's thin.

### 3. Present and compare

Present designs sequentially so the user can absorb each one, then compare them in prose. Contrast by:

- **Depth** — leverage at the interface
- **Locality** — where change concentrates
- **Seam placement** — where the boundary sits

After comparing, give your own **recommendation**: which design you think is strongest and why. If elements from different designs would combine well, propose a hybrid. **Be opinionated** — the user wants a strong read, not a menu.

## Why three (and not one or ten)

- **One agent design = anchored on first idea.** That's the trap Design-It-Twice exists to prevent.
- **Two agents = tempting to pick the "better" one without thinking about what each constraint missed.**
- **Three diverges enough** that the contrast forces real comparison.
- **Four or more = diminishing returns and slow.** Output gets noisy; the user can't hold all of them in head.

Cap at 3 sub-agents per Phase 3 invocation. If the user wants a 4th angle, they can re-run.
