# Task format by spec type

In step 3, clarify decomposes the spec into tasks. The format adapts to the spec type detected in step 1. Three formats — product, technical, small. They differ in mandatory fields and grouping, NOT in the AC format (which is always one: Given/When/Then + Proof command).

## Product spec format

Grouped by user story (US-N). Each story = independently testable deliverable.

```markdown
### TASK-{N}: {title}

**Story**: US-{M} — {story title}
**Status**: todo
**Depends on**: TASK-X, TASK-Y (or "none")
**Files**: {exact file paths to create/modify}
**Leverage**: {existing code to reuse — paths to models, utils, patterns; or "none"}
**Requirements**: {FR-001, FR-003 — which requirements the task fulfills}

**Acceptance Criteria**:
- [ ] AC-{N}.1: {concrete, verifiable criterion}
  Given: {initial state}
  When: {action}
  Then: {expected outcome}
  Proof: `{exact shell command to verify}`
- [ ] AC-{N}.2: ...

**Edge Cases**:
- {boundary condition}: {expected behavior}
- {error scenario}: {expected handling}
```

## Technical spec format

Grouped by concern area (AREA-N). No Story/Requirements fields.

```markdown
### TASK-{N}: {title}

**Area**: AREA-{M} — {concern area, e.g. "Database", "Auth", "Monitoring"}
**Status**: todo
**Depends on**: TASK-X (or "none")
**Files**: {exact paths}
**Leverage**: {existing code to reuse, or "none"}

**Acceptance Criteria**:
- [ ] AC-{N}.1: {criterion}
  Proof: `{command}`

**Edge Cases**:
- {relevant edge case only}
```

## Small spec format

Flat numbered list, minimal fields.

```markdown
### TASK-{N}: {title}

**Files**: {paths}
**Leverage**: {existing code, or "none"}
**AC**: {criterion} — Proof: `{command}`
```

## Common to ALL formats

- `**Status**` field — `todo` (default). The user or `mattpocock:tdd` updates it to `done` / `blocked` / `failed` as work proceeds.
- `**Files**` — exact paths, not "auth module", not "user-related files".
- `**Leverage**` — required. Forces a look for reusable code before writing from scratch. "none" is fine if genuinely from scratch.
- Acceptance criteria — each with a runnable proof command. PASS / FAIL / UNKNOWN tristate. Never boolean.

## What is NOT in slim clarify (difference from the old pipeline)

- ❌ `[P]` parallel markers — execute orchestration no longer ships in the skills, parallel flags are meaningless.
- ❌ Stages (Stage 1 / 2 / 3) — multi-stage orchestration removed.
- ❌ Checkpoints — were for the execute fix-loop, not needed without it.
- ❌ "Worker prompt template" in step 6 — execute spawn pattern is dead.

If the spec is consumed by `mattpocock:tdd` or a human, they build their own workflow on top. The Status field is enough for tracking.

## Atomic scope rule

Each task = 1-3 related files. If more — split:

❌ "Implement authentication system" — touches many files, multiple purposes.
❌ "Add user management" — vague scope, no file paths.

✅ "Create User model in `src/models/user.py` with email/password fields".
✅ "Add password hashing utility in `src/utils/auth.py` using bcrypt".
✅ "Create LoginForm component in `src/components/LoginForm.tsx`".

## Edge cases — which categories to include

Pick 2-3 categories per task, not all 5:

- **Input**: empty, null, oversized, unicode, special chars
- **Boundaries**: min/max values, single element, empty collection
- **Errors**: network failure, timeout, partial failure, invalid state
- **Concurrency**: race conditions, duplicate processing
- **Security**: auth bypass, injection, rate limiting

Relevance depends on the task. User model — Input + Boundaries + Security. Logging system — Errors + Concurrency. CLI argument parser — Input + Boundaries.
