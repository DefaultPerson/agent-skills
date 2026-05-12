# Coverage verifier — fuzzy-match safety net

Ты проверяешь список строк, которые fuzzy-matching скрипт НЕ смог найти в rewritten-файле. Многие из них — FALSE POSITIVES (контент в файле есть, но перефразирован, отформатирован иначе, или с исправленными опечатками). Твоя задача — отделить TRUE_MISSING от false positives.

Это Phase 4c (после per-section gap detection) или Phase 8 (final verification против оригинального backup). Один и тот же контракт, разные `{source_kind}` (sorted vs backup).

## Входные данные

- **Источник истины:** `{source_kind}` (`sorted` или `backup`)
- **Список uncovered кандидатов:** `{uncovered_tmp_path}` — строки, не найденные fuzzy-скриптом
- **Целевой rewritten-файл:** `{rewritten_path}`
- **Режим:** `{mode}` — `strict` (батч до 100 строк, обычная проверка) или `loose` (batch на весь uncovered, expect mostly false positives — используется только если sorted ≈ backup + headers, см. Phase 8 optimization)

## Что делать

Для КАЖДОЙ строки в uncovered-файле:

1. Поиск по ВСЕМУ rewritten-файлу контента с тем же смыслом.
2. Если найден (даже перефразирован, переформатирован, с исправленными опечатками, суммаризован) → **FALSE POSITIVE**, пропускай.
3. Если truly не найден нигде → **TRUE_MISSING**, репорти.

## Важно: HTML-блоки

Rewritten-файл может содержать `<details>`, `<summary>`, `<table>` и другие HTML-элементы. Контент ВНУТРИ этих тегов присутствует — ищи внутри них. Много false positives из-за того, что контент переехал в `<details>`-блоки.

## Правило chat summarization

Rewritten-файл намеренно суммаризует raw chat logs (timestamped сообщения вида `☀️, [date]`, `Ivan KOLESNIKOV` и т.п.) в структурированные "Key takeaways" секции. Если **substantive facts** из chat-сообщения (numbers, prices, names, conclusions) присутствуют в summary — это COVERED, не MISSING.

Конкретно:
- Timestamps, emoji-маркеры, неформальные приветствия → всегда **FALSE POSITIVE**.
- Conversational fragments (`Ну хз`, `Ага`, `Потом конечная`) → **FALSE POSITIVE**.
- Back-and-forth debate, сжатый до conclusion → **COVERED**.
- Specific numbers/facts, сохранённые в summary → **COVERED**.

Репорти TRUE_MISSING только если substantive ИДЕЯ не имеет эквивалента нигде в файле.

## Output формат

Только TRUE MISSING строки, по одной на строку:

```
TRUE_MISSING: "<exact line from uncovered file>"
```

Если все строки — false positives:
```
ALL COVERED — no true gaps found.
```

## Антипаттерны

❌ Репортить chat-timestamp `☀️, [Mar 12]` как TRUE_MISSING — это никогда не идея.  
❌ Репортить conversational filler как TRUE_MISSING.  
❌ Пропустить grep внутри `<details>` блока.  
❌ Считать MISSING строку, у которой substantive fact есть в summary.

## Общность

Следующий шаг pipeline'а — пользователь редактирует gaps-файл и решает, что применить. Если ты залажаешь tons of false positives — пользователь ручную работу делает за тебя, доверие к скиллу падает. Если ты пропустишь TRUE_MISSING — данные потеряны в финальном файле. Баланс: жёсткий filter false positives, но НИЧЕГО substantive не пропускать.
