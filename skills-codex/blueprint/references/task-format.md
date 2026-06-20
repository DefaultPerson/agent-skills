# Task format by spec type

In step 3, blueprint decomposes the spec into tasks. The format adapts to the spec type detected in step 1. Three formats — product, technical, small. They differ in mandatory fields and grouping, NOT in the proof style (always the same: a **`Done when:` line with a runnable shell command**).

> **Readable, not ceremonial.** Write tasks like a plan a teammate can act on, not a compliance document. The rigor lives in the `Done when:` shell proof — not in scaffolding words. No `AC-N.N` numbering, no `Given/When/Then` boilerplate, no `Proof:` label. One plain sentence + one command.

## Output: two files (tasks + reference)

blueprint writes the plan as **two** files (step 6), for context economy — executors / per-stage sub-agents / `/verify-done` / goal-prep load only the lean tasks file:

- **`<spec>.md` — tasks file (PRIMARY):** a `> Context: see <spec>.reference.md` pointer line, an optional `## Open questions` block (blocking `❓ NEEDS YOU` only), and `## Tasks`. Each task is **self-sufficient** — executable from this file alone (`Done when:` IS the acceptance). This is the downstream contract.
- **`<spec>.reference.md` — reference:** `## Overview`, full `## Requirements`, Terminology, `## Assumptions & open questions`, `## Risks`, ADR links. Read-once "why".

A task cites a requirement by light id (`R1`) only when it genuinely depends on one — don't add IDs for their own sake. Trivial / single-component specs may stay one file (fold the reference sections into `<spec>.md`); downstream resolves by preferring `<spec>.md` and treating it as both when no `<spec>.reference.md` exists.

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
- **`**Status**`** (optional) — `todo` / `done` / `blocked` / `failed`. Add only if the user or `mattpocock:tdd` wants tracking; absence implies `todo`.
- **`**Mode**`** (optional) — add `HITL` only when the task needs human judgment (architecture call, design review, external access, manual verification). Absence implies an autonomous agent can close it.

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

## Edge cases — which categories to include

Pick 2-3 categories per task, not all 5. Write each as an inline `Edge:` line (concrete input → expected output), not a separate ceremony block:

- **Input**: empty, null, oversized, unicode, special chars
- **Boundaries**: min/max, single element, empty collection
- **Errors**: network failure, timeout, partial failure, invalid state
- **Concurrency**: race conditions, duplicate processing
- **Security**: auth bypass, injection, rate limiting

Relevance depends on the task. User model — Input + Boundaries + Security. Logging — Errors + Concurrency. CLI parser — Input + Boundaries.

## What is NOT in blueprint output

- ❌ `[P]` parallel markers, `Stages`, `## Execution Order` — the execute orchestration was removed in v2.0; these are meaningless. If you see them, it's a bug.
- ❌ `AC-N.N` numbering, `Given:/When:/Then:` scaffolding, `Proof:` labels — replaced by the single `Done when:` line.
- ❌ RFC-2119 `MUST/SHOULD/MAY` prose in tasks — priority lives in `## Requirements` tags (`[must]/[nice]/[later]`), see `references/contracts.md`.

If the spec is consumed by `mattpocock:tdd` or a human, they build their own workflow on top; the `### TASK-{N}` headers + `Done when:` lines are enough to act on and to track.
