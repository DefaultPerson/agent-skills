# Contracts — Phase 4 detail (FR-NNN format)

Phase 4 в clarify определяет contracts: interfaces между компонентами. Skip если spec — small или single-component technical. Иначе обязателен, чтобы downstream работа (manual / mattpocock:tdd / goal feature) не споткнулась на ambiguous boundaries.

## Что входит в contracts

- **API endpoints** — method, path, request schema, response schema, types
- **Type definitions** — interfaces, structs, enums
- **Event contracts** — pub/sub topics, payload schemas
- **CLI contracts** — args, flags, exit codes (для CLI tools)

## FR-NNN формат (functional requirements)

Каждый contract item получает label `FR-{NNN}` (spec-kit convention):

```markdown
- FR-001: System MUST return 401 для unauthenticated requests
- FR-002: System SHOULD cache responses for 5 minutes
- FR-003: System MAY support batch operations в v2
```

## MUST / SHOULD / MAY уровни (RFC 2119)

- **MUST** — обязательно для compliance. Implementation без этого = неработающая.
- **SHOULD** — strongly recommended. Implementation может deviate с обоснованием.
- **MAY** — optional. Реализация по желанию, не блокирует acceptance.

Используй чётко — не "should" в смысле "обязательно". Если обязательно — MUST.

## Пример: REST API contract

```markdown
## Contracts

### API: User CRUD

- FR-101: `POST /api/users` MUST accept JSON body `{email, password}` и return 201 с `{id, email}`.
- FR-102: `POST /api/users` MUST return 400 если email пуст или password <8 символов.
- FR-103: `GET /api/users/:id` MUST return 200 с `{id, email, created_at}` для existing user.
- FR-104: `GET /api/users/:id` MUST return 404 для несуществующего id.
- FR-105: `GET /api/users` SHOULD support pagination через `?page=N&limit=M` (defaults: page=1, limit=20).
- FR-106: `DELETE /api/users/:id` MAY require admin role (deferred to v2).
```

## Пример: Type definitions

```markdown
### Types

- FR-201: User struct MUST содержать поля `id: UUID`, `email: string`, `password_hash: string`, `created_at: timestamp`.
- FR-202: Session struct MUST содержать `user_id: UUID`, `token: string`, `expires_at: timestamp`.
- FR-203: `password_hash` MUST использовать bcrypt cost ≥10.
```

## Связь contracts ↔ tasks

В task'е поле `Requirements: FR-101, FR-103` указывает, какие FR'ы задача fulfills. Это обратная ссылка — Validator в Phase 7.6 проверяет, что все FR имеют backing task, и каждый task проверяет какой-то FR.

❌ Task без `Requirements:` поле в product/technical spec — гэп.  
✅ Один FR может быть covered несколькими tasks. Один task может cover несколько FR.

## Антипаттерны

❌ Описывать contract в свободной форме без FR-NNN labels — теряется traceability.  
❌ "Should support X" в смысле MUST — путаница RFC 2119 уровней.  
❌ Contracts без runnable verification — каждый FR должен быть verifiable хотя бы одной AC из tasks.  
❌ Contracts которые не упомянуты в tasks — orphaned requirement.
