# Task format by spec type

In step 3, blueprint decomposes the spec into tasks. The format adapts to the spec type detected in step 1. Three formats — product, technical, small. They differ in mandatory fields and grouping, NOT in the proof style (always the same: a **`Done when:` line with a runnable shell command**).

> **Readable, not ceremonial.** Write tasks like a plan a teammate can act on, not a compliance document. The rigor lives in the `Done when:` shell proof — not in scaffolding words. No `AC-N.N` numbering, no `Given/When/Then` boilerplate, no `Proof:` label. One plain sentence + one command.

## Output: tasks.md (checklist + blocks) + reference.md (context)

blueprint writes the plan as **two** files (step 6). **More than one file ⇒ a flat directory `<spec-stem>/`** (no nested subdirs); a trivial spec stays a single `<spec>.md`. **No `.bak`** — in directory mode the original `<spec>.md` is left untouched (it IS the backup); the git `pre-blueprint` snapshot covers both modes.

- **`<spec-stem>/tasks.md` — the plan (checklist on top, blocks below).** In order: a `> Context (the "why"): see reference.md` pointer line; **`## Needs your attention`** (only if it has content); **`## Checklist`** (one `- [ ] TASK-n — short title` line per task); then **`## Tasks`** — the full `### TASK-n` blocks (`**Files**`, `**Leverage**`, `Done when:` proof, inline `Edge:`), grouped by `▸ AREA-n` in the same order. **`Done when:` (the acceptance contract) lives in the blocks — `/verify-done` and goal-prep read the proofs from `## Tasks`.** (See "The navigation layer" below.)
- **`<spec-stem>/reference.md` — context only (the "why", read once).** `## Overview`, full `## Requirements`, Terminology, **`## Assumptions`** (ranked, non-blocking only), `## Risks`, `## Non-goals`. **NO task blocks.** Blocking `❓ NEEDS YOU` do NOT live here either.

Single-file fallback: a trivial `<spec>.md` holds `## Needs your attention` (if any), `## Checklist`, `## Tasks`, and the context sections folded in. Downstream readers resolve the tasks file as `<spec-stem>/tasks.md` (or `<spec>.md`) and read the `### TASK-n` blocks + `Done when:` from its `## Tasks`. A task cites a requirement by light id (`R1`) only when it genuinely depends on one.

### Keep the plan concise + DRY — lossless

Keep it tight: each fact in exactly ONE place, cross-reference instead of repeating; cut filler and merge near-duplicate prose/risks — but **never drop a fact** (every requirement, decision, assumption, risk, edge, code-pointer survives somewhere). A fact lives in exactly one of `## Overview`/`## Requirements`/`## Assumptions`/`## Risks`/`## Non-goals` (reference) or a task's `### TASK-n` block (tasks); the `## Checklist` line is just a pointer + title. Structured facts → a table, one row each. Lossless check: every distinct fact from the original notes is still findable.

## The navigation layer (`## Needs your attention` + the `## Checklist`)

A thin, scannable header sits above the detail blocks. The `## Tasks` `### TASK-n` blocks are the single source of truth for *how*; the `## Checklist` is the at-a-glance map + tracker. Keep them in sync — one `- [ ] TASK-n` per `### TASK-n`.

### `## Needs your attention` (omit the heading on a clean plan)

The ONE place for anything that needs the reader. Two kinds of line:

```markdown
## Needs your attention

- ❓ NEEDS YOU [decision]: is DELETE admin-only? (input was ambiguous) → blocks: TASK-11
- ❓ NEEDS YOU [unknown]: spike — does the queue hold 10k msg/s at our payload? → blocks: all
- HITL: TASK-3 — auth design call (decide session vs bearer before building)
```

- **Blocking forks** — `❓ NEEDS YOU` with a light tag (`[decision]` / `[question]` / `[unknown]`), ending in **`→ blocks: TASK-n[, TASK-m]`** (or `→ blocks: all`). Every blocking item the model can't decide alone goes here — and ONLY here (not also in reference.md).
- **HITL tasks** — `HITL: TASK-n — title (why)`, one per task carrying `**Mode**: HITL`, so the reader sees up front what they can't delegate.

### `## Checklist` (the at-a-glance map + tracker)

```markdown
## Checklist

**▸ AREA-1 — Realtime**
- [ ] TASK-1 — push instant-ness spike  · HITL · ❓
- [ ] TASK-2 — tag-classifier hardening
- [ ] TASK-3 — realtime delivery  · after TASK-1

**▸ AREA-2 — Account Manager**
- [ ] TASK-4 — probe AM capabilities  · HITL · ❓
```

- One line per task: **`- [ ] TASK-n — short title`** (≤ ~6 words). GFM checkbox = progress tracking.
- **Bare `TASK-n`, never `### TASK-n`** — the `### TASK-n` blocks live below in `## Tasks`.
- Grouped under `**▸ AREA-n**` / `**US-n**` headers, **each group exactly once**, foundations-first.
- Light flags only: `· after TASK-x` (real prerequisite), `· HITL`, `· ❓` (gated by a `## Needs your attention` item). No graph, no `[P]`, no Stages.

## Task detail blocks (the `### TASK-n` blocks under `## Tasks`)

The `### TASK-{N}` blocks below are the **detail**, written under `## Tasks` in `tasks.md` (below the `## Checklist`), one per checklist line, grouped by the same `▸ AREA-n` / `US-n` order. The format adapts to spec type — product / technical / small.

## Product spec format

Grouped by user story (US-N). Each story = an independently demoable deliverable.

```markdown
### TASK-{N}: {title}

**Story**: US-{M} — {story title}
**Files**: {exact file paths to create/modify}
**Leverage**: {existing code to reuse — paths to models, utils, patterns; or "none"}
**Covers**: {which requirements this fulfils — plain refs, or skip if obvious}

Done when: `{exact shell command}` — {what a passing run shows, in plain words}.

Edge: {boundary/error scenario} → {expected behaviour}.
Edge: {another, only if it genuinely applies}.
```

## Technical spec format

Grouped by concern area (AREA-N). No Story/Covers fields.

```markdown
### TASK-{N}: {title}

**Area**: AREA-{M} — {concern, e.g. "Database", "Auth", "Monitoring"}
**Files**: {exact paths}
**Leverage**: {existing code to reuse, or "none"}

Done when: `{command}` — {what passing looks like}.

Edge: {relevant edge case only}.
```

## Small spec format

Flat numbered list, minimal fields.

```markdown
### TASK-{N}: {title}

**Files**: {paths}  ·  **Leverage**: {existing code, or "none"}
Done when: `{command}` — {what passing looks like}.
```

## Common to ALL formats

- **`Done when:`** — one plain sentence ending in a runnable shell/test command in backticks. It must return **PASS / FAIL / UNKNOWN** (UNKNOWN when the env isn't up — e.g. server not running), never a vague "it works". This replaces the old `AC` / `Given/When/Then` / `Proof:` block.
- **`**Files**`** — exact paths, not "auth module", not "user-related files".
- **`**Leverage**`** — required. Forces a look for reusable code before writing from scratch. "none" is fine if genuinely from scratch.
- **`**Status**`** (optional) — execution state only: `todo` / `done` / `failed`; absence implies `todo`. The checklist `- [ ]`/`- [x]` box in tasks.md is the usual tracker. Do NOT scatter `blocked-on-TASK-x` lines across blocks — a real prerequisite is the checklist's `· after TASK-x`, and a human-gated blocker is a `## Needs your attention` item (`→ blocks: TASK-n`).
- **`**Mode**`** (optional) — add `HITL` only when the task needs human judgment (architecture call, design review, external access, manual verification). Absence implies an autonomous agent can close it. Every HITL task is also aggregated once in `## Needs your attention`.

## Behaviour, not procedure

`Done when:` describes what the system DOES (observable through its interface), not HOW it does it. The next reader writes the test from it; they shouldn't need to read implementation prose.

❌ **Procedural:** `Done when: middleware extracts the token, calls validateJWT(), returns 401.`
✅ **Behavioural:** `Done when: \`curl -s -H 'Auth: <expired>' :8080/me\` → \`401 {error:"token_expired"}\`.`

❌ **Vague:** `Done when: the endpoint works.` (who decides "works"? no command.)
✅ **Concrete:** `Done when: \`curl -sw '%{http_code}' :8080/api/users -o /dev/null\` prints \`200\` in <200ms.`

## Atomic scope rule

Each task = 1-3 related files AND a **thin vertical slice** through every layer it needs (schema → API → UI → tests, or whichever subset applies). A finished slice is demoable or verifiable on its own. If a task only touches one layer and isn't observable end-to-end, it's the wrong shape — split differently.

❌ "Implement authentication system" — touches many files, multiple purposes.
❌ "Add user management" — vague scope, no file paths.
❌ "Add DB columns for user profile" — horizontal slice; nothing demoable until API + UI land.

✅ "Add `phone` to User: column in `src/models/user.py` + accept in `POST /users` (`src/routes/users.py`) + render in `src/components/UserForm.tsx` + test in `tests/test_users.py`" — vertical slice; demoable on its own.
✅ "Create User model in `src/models/user.py` with email/password fields" — also fine when the model is the whole feature this task is about.

## Foundations first — the first task, and no buried scaffold

The first task must leave the project **runnable and verifiable**, so every later `Done when:` has something to run against — a plan should never read like it starts half-built.

- **Greenfield** (no runner / build / entrypoint yet): the first task creates the minimal skeleton + a smoke test. `Done when:` proves a fresh clone goes green, e.g. `` `npm ci && npm test` exits 0 with ≥1 passing test `` or `` `uv run pytest -q` collects and passes one test ``.
- **Brownfield** (already builds): the first task is a one-line **baseline proof** the existing build/test is green (`` `make test` exits 0 ``). It pins the starting state `/verify-done` re-checks first. If truly trivial, note the starting state in the `> Context` line instead.

**No buried scaffold.** The test harness, fixtures, and CI entrypoint live in that first task; later tasks reuse them via `**Leverage**: <foundation task> harness`. A feature task must NOT create the test runner as a side effect — if scaffolding is missing, it belongs earlier. The first *feature* task's `Done when:` must run assuming only the foundation has landed.

**Order, don't graph.** Group by area; each area appears exactly once; order tasks (and areas) so a genuine prerequisite sits above what needs it. The only sequencing artifacts are this ordering + the checklist's inline `· after TASK-x`. No Stages, `[P]`, or dependency graph.

## Edge cases — which categories to include

Pick 2-3 categories per task, not all 5. Write each as an inline `Edge:` line (concrete input → expected output), not a separate ceremony block:

- **Input**: empty, null, oversized, unicode, special chars
- **Boundaries**: min/max, single element, empty collection
- **Errors**: network failure, timeout, partial failure, invalid state
- **Concurrency**: race conditions, duplicate processing
- **Security**: auth bypass, injection, rate limiting

Relevance depends on the task. User model — Input + Boundaries + Security. Logging — Errors + Concurrency. CLI parser — Input + Boundaries.

## What is NOT in blueprint output

- ❌ `[P]` parallel markers, `Stages`, `## Execution Order`, a dependency graph / edge list (`TASK-a -> TASK-b`, a `## Dependencies` section) — the execute orchestration was removed in v2.0. Sequencing is area order + the checklist's inline `· after TASK-x` only. If you see the rest, it's a bug.
- ❌ `AC-N.N` numbering, `Given:/When:/Then:` scaffolding, `Proof:` labels — replaced by the single `Done when:` line.
- ❌ RFC-2119 `MUST/SHOULD/MAY` prose in tasks — priority lives in `## Requirements` tags (`[must]/[nice]/[later]`), see `references/contracts.md`.
- ❌ A plan that starts in mid-air — a first task that is a blocked spike with no green baseline before it; or the test runner / CI set up as a side effect of a feature task (buried scaffold). Foundations come first.
- ❌ Blocking `❓ NEEDS YOU` items duplicated in both `tasks.md` and `reference.md`, or scattered `Status: blocked-on-…` lines across task blocks. One attention surface: `## Needs your attention`.

If the plan is consumed by a human or the goal feature, they build their own workflow on top; the `### TASK-{N}` headers + `Done when:` lines are enough to act on and to track.
