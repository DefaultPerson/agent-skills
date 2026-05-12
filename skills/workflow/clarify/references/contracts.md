# Contracts — step 4 detail (FR-NNN format)

Step 4 in clarify defines contracts: interfaces between components. Skip when the spec is small or single-component technical. Otherwise mandatory, so downstream work (manual / `mattpocock:tdd` / goal feature) doesn't trip on ambiguous boundaries.

## What goes into contracts

- **API endpoints** — method, path, request schema, response schema, types
- **Type definitions** — interfaces, structs, enums
- **Event contracts** — pub/sub topics, payload schemas
- **CLI contracts** — args, flags, exit codes (for CLI tools)

## FR-NNN format (functional requirements)

Every contract item gets the label `FR-{NNN}` (spec-kit convention):

```markdown
- FR-001: System MUST return 401 for unauthenticated requests
- FR-002: System SHOULD cache responses for 5 minutes
- FR-003: System MAY support batch operations in v2
```

## MUST / SHOULD / MAY levels (RFC 2119)

- **MUST** — required for compliance. Implementation without it is broken.
- **SHOULD** — strongly recommended. Implementation may deviate with justification.
- **MAY** — optional. Build at will, does not block acceptance.

Use them precisely — don't write "should" when you mean "MUST". If it's required — MUST.

## Example: REST API contract

```markdown
## Contracts

### API: User CRUD

- FR-101: `POST /api/users` MUST accept JSON body `{email, password}` and return 201 with `{id, email}`.
- FR-102: `POST /api/users` MUST return 400 when email is empty or password is <8 characters.
- FR-103: `GET /api/users/:id` MUST return 200 with `{id, email, created_at}` for an existing user.
- FR-104: `GET /api/users/:id` MUST return 404 for a non-existing id.
- FR-105: `GET /api/users` SHOULD support pagination via `?page=N&limit=M` (defaults: page=1, limit=20).
- FR-106: `DELETE /api/users/:id` MAY require admin role (deferred to v2).
```

## Example: Type definitions

```markdown
### Types

- FR-201: User struct MUST contain fields `id: UUID`, `email: string`, `password_hash: string`, `created_at: timestamp`.
- FR-202: Session struct MUST contain `user_id: UUID`, `token: string`, `expires_at: timestamp`.
- FR-203: `password_hash` MUST use bcrypt with cost ≥10.
```

## Linking contracts ↔ tasks

In a task, the `Requirements: FR-101, FR-103` field points to the FRs that task fulfills. This is the back-reference — the Phase 7.6 validator checks that every FR has a backing task and that every task verifies some FR.

❌ Task without a `Requirements:` field in a product/technical spec — a gap.
✅ One FR can be covered by multiple tasks. One task can cover multiple FRs.

## Anti-patterns

❌ Describing a contract in free form without FR-NNN labels — traceability is lost.
❌ "Should support X" meaning MUST — confuses RFC 2119 levels.
❌ Contracts without runnable verification — every FR must be verifiable by at least one AC from the tasks.
❌ Contracts not referenced by any task — orphaned requirement.
