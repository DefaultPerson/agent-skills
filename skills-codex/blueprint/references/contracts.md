# Requirements & contracts — step 4 detail

Step 4 in blueprint pins down the **interfaces between components** so downstream work (manual / `mattpocock:tdd` / goal feature) doesn't trip on ambiguous boundaries. Skip when the spec is small or a single-component technical change.

> **Plain sentences, not RFC ceremony.** Write each requirement as one clear sentence a human reads in a second, tagged by priority. No `MUST`/`SHOULD`/`MAY` shouting, no mandatory `FR-NNN` numbering. The point is an unambiguous boundary, not a compliance document.

## Priority tags (replaces RFC-2119 MUST/SHOULD/MAY)

- **`[must]`** — required. Without it the change is broken / incomplete.
- **`[nice]`** — wanted if cheap; the change still ships without it.
- **`[later]`** — explicitly deferred. **Deferring is a scope decision — gated** (see below).

```markdown
## Requirements
- [must]  The API returns 401 for tokens that are missing, expired, or wrongly signed.
- [nice]  Responses to GET /users are cached for ~5 min.
- [later] Bulk user import.
```

That's it — readable at a glance, and the priority is unmissable.

## IDs are optional

For a **large** spec where tasks need to point back at requirements, add lightweight IDs — `R1`, `R2`, … (or keep `FR-001` if you genuinely prefer it). For everything else, skip IDs: a task's `**Covers**:` field can name the requirement in plain words. Don't add an ID just to have one.

```markdown
## Requirements
- [must] (R1) POST /api/users accepts JSON `{email, password}` → 201 `{id, email}`.
- [must] (R2) POST /api/users → 400 when email is empty or password < 8 chars.
- [must] (R3) GET /api/users/:id → 200 `{id, email, created_at}`, or 404 if absent.
- [nice] (R4) GET /api/users supports `?page=N&limit=M` (defaults 1 / 20).
- [later] (R5) DELETE /api/users/:id restricted to admins.
```

## What goes into contracts

Describe the shape precisely (this is where precision *earns* its keep):

- **API endpoints** — method, path, request shape, response shape, status codes.
- **Types** — fields + types (`id: UUID`, `email: string`, `created_at: timestamp`).
- **Events** — pub/sub topics, payload shape.
- **CLI** — args, flags, exit codes.

```markdown
### Types
- [must] User has `id: UUID`, `email: string`, `password_hash: string`, `created_at: timestamp`.
- [must] `password_hash` is bcrypt, cost ≥ 10.
```

## Scope-cut user gate (hard rule)

Tagging something `[later]`, moving an input-mentioned feature to a `Non-goals` / `Out of scope` section, or dropping an edge case the input named — these are **scope decisions, not cleanup**. Each one MUST be confirmed by the user via the step 5 Scope-cut audit **before** the spec is written to disk. The user wrote the input on purpose; opting things out of v1 is their call, never the model's silent demotion. (Phrases like `(v2)`, `(future)`, `(deferred)`, `(later)`, `(MVP only)` on a requirement are the trigger signal the audit scans for.)

## Linking requirements ↔ tasks

A task's `**Covers**:` field names the requirement(s) it fulfils (by ID if you used them, else in words). The step 7 check walks both directions: every `[must]` requirement has a backing task, every task ties back to a requirement or the Overview.

❌ A `[must]` requirement no task covers — a gap.
❌ A task that maps to nothing in Overview/Requirements — orphaned work.
✅ One requirement can span several tasks; one task can cover several requirements.

## Anti-patterns

❌ `MUST`/`SHOULD`/`MAY` prose — use `[must]`/`[nice]`/`[later]` tags instead.
❌ Forcing `FR-NNN` IDs onto a small spec — adds bureaucracy, buys nothing.
❌ A requirement with no way to verify it — every `[must]` must be checkable by some task's `Done when:`.
❌ A vague boundary ("handle users properly") — name the exact shape and status codes.
