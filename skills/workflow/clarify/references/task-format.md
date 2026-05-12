# Task format by spec type

В Phase 3 clarify декомпозирует spec на tasks. Формат адаптируется к типу spec'а, определённому в Phase 1. Три формата — product, technical, small. Они отличаются количеством обязательных полей и группировкой, НЕ форматом AC (тот всегда один: Given/When/Then + Proof command).

## Product spec format

Группировка по user story (US-N). Каждая story = independently testable deliverable.

```markdown
### TASK-{N}: {title}

**Story**: US-{M} — {story title}
**Status**: todo
**Depends on**: TASK-X, TASK-Y (или "none")
**Files**: {точные пути файлов для create/modify}
**Leverage**: {existing code to reuse — пути к моделям, utils, паттернам; или "none"}
**Requirements**: {FR-001, FR-003 — какие requirements task fulfills}

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

Группировка по concern area (AREA-N). Без Story/Requirements полей.

```markdown
### TASK-{N}: {title}

**Area**: AREA-{M} — {concern area, например "Database", "Auth", "Monitoring"}
**Status**: todo
**Depends on**: TASK-X (или "none")
**Files**: {точные пути}
**Leverage**: {existing code to reuse, или "none"}

**Acceptance Criteria**:
- [ ] AC-{N}.1: {criterion}
  Proof: `{command}`

**Edge Cases**:
- {relevant edge case only}
```

## Small spec format

Flat numbered list, минимальные поля.

```markdown
### TASK-{N}: {title}

**Files**: {paths}
**Leverage**: {existing code, или "none"}
**AC**: {criterion} — Proof: `{command}`
```

## Что во ВСЕХ форматах

- `**Status**` поле — `todo` (default), пользователь/mattpocock:tdd обновит на `done` / `blocked` / `failed` по ходу работы.
- `**Files**` — точные пути, не "auth module", не "user-related files".
- `**Leverage**` — обязательно. Заставляет искать reusable код перед написанием с нуля. "none" допустимо если действительно с нуля.
- Acceptance criteria — каждый с runnable proof command. PASS / FAIL / UNKNOWN tristate. Никогда не boolean.

## Чего НЕТ в slim clarify (отличие от старого pipeline)

- ❌ `[P]` parallel markers — execute orchestration больше нет в скиллах, parallel-флаги бессмысленны.
- ❌ Stages (Stage 1 / 2 / 3) — multi-stage orchestration убран.
- ❌ Checkpoints — were для execute fix-loop'а, не нужны без него.
- ❌ "Worker prompt template" в Phase 6 — execute spawn pattern мёртв.

Если spec будет потребляться mattpocock:tdd или человеком — он строит свой workflow поверх. Status поля достаточно, чтобы tracking сработал.

## Atomic scope правило

Каждый task = 1-3 related files. Если больше — split:

❌ "Implement authentication system" — задевает много файлов, multiple purposes.  
❌ "Add user management" — vague scope, no file paths.

✅ "Create User model в `src/models/user.py` с полями email/password".  
✅ "Add password hashing utility в `src/utils/auth.py` через bcrypt".  
✅ "Create LoginForm component в `src/components/LoginForm.tsx`".

## Edge cases — какие категории включать

Выбирай 2-3 категории per task, не все 5:

- **Input**: empty, null, oversized, unicode, special chars
- **Boundaries**: min/max values, single element, empty collection
- **Errors**: network failure, timeout, partial failure, invalid state
- **Concurrency**: race conditions, duplicate processing
- **Security**: auth bypass, injection, rate limiting

Релевантность зависит от задачи. User model — Input + Boundaries + Security. Logging system — Errors + Concurrency. CLI argument parser — Input + Boundaries.
