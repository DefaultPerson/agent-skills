# Questioner — Phase 2 clarifying questions pattern

Это не subagent — это format-контракт, как clarify сам генерирует вопросы пользователю через AskUserQuestion в Phase 2. Held в отдельном файле, чтобы можно было править формат без перечитывания всего SKILL.md.

## Когда задаются вопросы

Phase 2, hard gate. Не proceed'ить к Phase 3 (декомпозиция) пока ambiguous points не resolved.

## Триггеры для вопроса

Генерируй вопрос только если есть РЕАЛЬНАЯ амбивалентность:
- Item помечен `[NEEDS CLARIFICATION]` в Phase 1
- Requirement может быть интерпретирован двумя способами
- Constraint отсутствует (performance target, scale, auth, persistence)
- Priority conflict между фичами (которая важнее?)

НЕ генерируй вопрос ради вопроса:
- ❌ "А какой backend использовать?" если spec уже указывает stack
- ❌ "Хотите тесты?" — default YES, спрашивать только если есть основания думать иначе
- ❌ Стилистические preferences ("какой naming convention?") — выбери одну, поставь в Constraints

## Формат вопроса (через AskUserQuestion)

Максимум 4 вопроса за раз (Anthropic AskUserQuestion limit). Каждый вопрос:

- **Question**: конкретный, без "пожалуйста" / "если вам интересно", заканчивается `?`
- **Header**: 1-3 слова, displayed как chip/tag (max 12 chars)
- **Options**: 2-4 mutually exclusive choices. Recommended option — первым в списке + `(Recommended)` суффикс. Описание per option — что произойдёт при выборе + trade-off в одну фразу.
- multiSelect: `false` обычно. `true` только если choices не взаимоисключающие (например, "которые features добавить?").

## Пример вопроса

```
Question: What auth method should the API use?
Header: Auth method
Options:
  - label: "JWT tokens (Recommended)"
    description: "Stateless, standard for REST APIs. Easy horizontal scaling. Trade-off: revoking sessions requires denylist."
  - label: "Session-based"
    description: "Server-side sessions in Redis/DB. Easier to revoke. Trade-off: stateful, harder to scale."
  - label: "API keys"
    description: "Simple, for internal services. No user concept. Trade-off: not suitable for end-user auth."
```

## Антипаттерны

❌ Спрашивать про вещи, уже описанные в spec.  
❌ Сваливать на пользователя default'ы (auth method для CLI tool без users — JWT не нужен).  
❌ Опции без описания trade-off'а.  
❌ Открытые вопросы ("какой stack?") — давай 2-4 конкретных варианта.  
❌ Больше 5 вопросов суммарно за Phase 2 — это знак, что spec слишком сырой, отправь на cleanup или к пользователю с feedback.

## После ответов

Каждый ответ обновляет соответствующую секцию spec'а в памяти (Constraints, scope, FR-NNN). Перепроверь — все ли `[NEEDS CLARIFICATION]` маркеры закрыты? Если нет — следующая итерация Phase 2 (но не больше 2-х итераций суммарно).
