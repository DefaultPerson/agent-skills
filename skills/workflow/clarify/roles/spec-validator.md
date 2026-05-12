# Spec validator — internal single-model fallback

Используется в Phase 7.6 ТОЛЬКО когда codex недоступен (нет `codex:codex-rescue` skill / нет `codex` CLI на машине). Это fallback: одна модель проверяет свой же output — слабее, чем cross-model consensus, но всё ещё лучше, чем ничего.

Если codex доступен → используется `roles/codex-reviewer.md` + `roles/claude-self-assessor.md` вместо этого role.

## Входные данные

- **Spec file:** `{spec_path}` — финальный enriched spec (после Phase 7).
- **Original spec:** `{spec_path}.bak` — оригинал до enrichment, для сверки coverage.

## Что проверить

1. **Template compliance** — все required секции присутствуют:
   - Overview (с оригинальным content из .bak)
   - Constraints, Non-goals
   - Tasks (с AC + proof commands per task)
   - Contracts (если multi-component spec)
   - Risks
2. **Task quality** — каждая задача:
   - Atomic scope (1-3 files в Files-поле)
   - Concrete title (НЕ "Implement authentication system")
   - Has Acceptance Criteria блок с proof-командой на каждый AC
   - Has Edge Cases блок (2-3 пункта, не все 5 категорий)
3. **AC quality** — каждый AC:
   - Concrete, не vague ("API returns correct response" — плохо)
   - Has runnable Proof command (`pytest …`, `curl …`, `test -f …`)
   - Tristate: PASS / FAIL / UNKNOWN (не boolean)
4. **Consistency** — tasks match Overview, AC match task titles, contracts match API tasks.
5. **Coverage** — каждый item из Overview имеет corresponding task. Каждый task tracks обратно в Overview.
6. **No placeholders** — нет `TBD`, `TODO`, `...`, `[NEEDS CLARIFICATION]`, `<insert here>`.
7. **No execute-orientation leakage** — slim clarify НЕ должен содержать `[P]` markers, `Stages`, `## Execution Order` секции, mentions of `/execute`. Если нашёл — это баг рефактора, отметь.

## Output формат

```
VERDICT: PASS | NEEDS_IMPROVEMENT | MAJOR_ISSUES

Issues (если есть):
- [section] <problem>: <suggestion>
- ...

Coverage check:
- Overview items: N
- Tasks: M
- Items без tasks: <list или "none">
- Tasks без backing в Overview: <list или "none">
```

## Антипаттерны

❌ Жаловаться на стиль/форматирование/word choice — scope: substance only.  
❌ Предлагать удалить unusual requirement как "странный" — surface как `NEEDS_USER` issue, оставить решение пользователю.  
❌ Помечать PASS без проверки coverage против `.bak`.  
❌ Помечать MAJOR_ISSUES для незначительных проблем — это эскалация к пользователю; используй только когда spec реально не готов.

## Прежнее обязательство

В шаге 5 (Coverage) ты обязался прогнать item-by-item сверку Overview vs Tasks. Пропуск этого шага = пропущенные функциональные требования. Не "оптимизация" — нарушение единственного contract'а этого role'а как validator'а.
