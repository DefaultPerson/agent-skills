---
name: cleanup
description: >
  Use when you have a messy notes/plan/chat dump (50+ lines, mixed topics,
  no clear structure) that needs lossless reorganization into a clean
  sectioned markdown file. Slow and thorough — overkill for files under
  30 lines or already-sectioned docs. Triggers: "cleanup", "/cleanup",
  "почисти", "реорганизуй", "clean up", "rewrite plan", "sort plan",
  "plan-rewrite", "/plan-rewrite".
when_to_use: >
  The input is unstructured (chat exports, dumped notes, brainstorm), >50
  lines, and the user wants the content cleaned without losing ideas. Works
  on multiple input files — produces one cleaned output per input, NOT one
  merged file. Do NOT use for already-structured docs, files under 30 lines,
  or when the user wants summarization (cleanup preserves everything; it
  doesn't compress ideas).
allowed-tools: [Bash, Glob, Grep, Read, Edit, Write, Agent, EnterPlanMode, ExitPlanMode, AskUserQuestion]
---

# Cleanup

Losslessly reorganize a messy notes/plan/chat dump into a clean sectioned markdown file, with three-level gap detection to prove nothing was lost.

> **Буква = дух.** Если правило мешает достичь цели, ради которой оно
> написано — правило ошибочно, а не цель. Не ищи лазейку в формулировке —
> спроси, что правило защищает, и защищай это.

## Usage

```
/cleanup <file> [file2] [file3] ...
```

Multi-file: each input is processed independently end-to-end. Output is N cleaned files, NOT one merged file. (Opt-in `--merge` flag preserves legacy single-output behavior for back-compat.)

## Слабые стороны и когда НЕ использовать

- **Медленный и тщательный — оверкилл для коротких файлов.** Если файл уже структурирован по `## ` секциям и короче 30 строк — потеря времени, ручное редактирование быстрее.
- **Расход контекста линеен по размеру входа.** Phase 4 (gap detection) спавнит фоновых агентов на больших файлах — следи за бюджетом. Для файлов >2000 строк подумай, можно ли разбить вход.
- **Не работает с не-markdown форматами.** JSON/YAML/code dumps — другой инструмент.
- **Не извлекает контент из ссылок** (YouTube, Telegram). Для этого — отдельный `/extract` перед `/cleanup`.
- **Не суммирует.** Скилл preservation-first; если хочется сократить идеи — другой инструмент (например, mattpocock:to-prd для PRD-style summarization).

## Как делать неправильно vs правильно

### Multi-file input

❌ **Плохо:** 3 файла на вход → конкатенирую в один merged-файл с `<!-- from: X -->` маркерами, прогоняю pipeline на merged → один output.
- Source-provenance теряется после Phase 0.
- Phase 4b keyword grep ловит keyword из file2 в file1 → ложное COVERED, замаскированный пропуск.
- `<50-line skip` срабатывает по merged size, хотя per-source файлы могут быть тривиально малы или огромны независимо.

✅ **Хорошо:** 3 файла → 3 независимых pipeline'а Phase 1-8 → 3 cleaned output'а. Per-source backup, per-source gap detection, per-source verify. Final report aggregates метрики.
- Provenance сохраняется end-to-end.
- 4b скоупится по реальной секции реального source.
- Опционально `--merge` flag для тех, кто полагался на merged output.

### Phase 4 gap detection rigor

❌ **Плохо:** Файл <50 строк — пропустил Phase 4b целиком, доверился только 4c fuzzy-match.
- 4c выдаёт только TRUE_MISSING. PARTIAL и REVERSED не ловятся.
- Если в multi-file mode размер каждого источника <50 — все три проверки фактически деградируют.

✅ **Хорошо:** Skip 4b только в single-file mode + <50 lines. В multi-file mode — 4b ВСЕГДА, минимум 1 агент на каждый source. Per-source keyword grep строго ограничен диапазоном строк своего источника.

### Standalone framing

❌ **Плохо:** В конце Phase 9 report подсовываю `Recommend: /clear then /clarify <file>`. Это пресуппозиция — пользователь, может, идёт в mattpocock:tdd, может в свой goal-feature, может вообще никуда.

✅ **Хорошо:** Заканчиваю одной строкой: `Cleanup done. Run /clear before continuing.` Не рекомендую downstream-скиллы. Пользователь решает сам, что дальше.

## Роли

Скилл спавнит подагентов в Phase 4 и Phase 10. Шаблоны промптов:

- `roles/gap-detector.md` — Phase 4b semantic compare per section
- `roles/coverage-verifier.md` — Phase 4c и Phase 8 fuzzy-match verification
- `roles/split-planner.md` — Phase 10 split plan (опционально)

Подстановки:

| Переменная | Источник |
|---|---|
| `{sorted_path}`, `{rewritten_path}` | Phase 1-3 output |
| `{sections}` | per-agent assignment (1-2 sections) |
| `{uncovered_tmp_path}` | Phase 4c/8 script output |
| `{source_kind}` | `sorted` (4c) / `backup` (8) |
| `{mode}` | `strict` (default, batches of 100) / `loose` (Phase 8 optimization) |
| `{cleaned_path}`, `{total_lines}`, `{section_list}` | Phase 10 input |

Спавн: `Agent(subagent_type="Explore", run_in_background=true, prompt=substitute("roles/<role>.md", vars))`.

## Что делает скилл (по шагам)

Каждый input-файл проходит через эти шаги независимо. Multi-file — N параллельных pipeline'ов.

1. **Понять что на входе.** Single или multi-file. Validate markdown. Backup каждого источника (`<file>.bak`).
2. **Привести секции в порядок.** Semantic sort: парсить `## ` секции, переносить misplaced строки в правильные секции, БЕЗ переписывания. Сохранять каждую оригинальную строку байт-в-байт. (Unicode caveat: Write-tool может нормализовать non-breaking spaces — если verify-sort валится, использовать Python для byte-copy.)
3. **Проверить sort.** `python3 scripts/verify-sort.py <bak> <sorted>` — superset check. FAIL → restore + abort.
4. **Переписать чисто.** Grammar, dedup точных копий, restructure через `### ` подсекции, clean chat artifacts (timestamps, emoji) в "Key takeaways" блоки. Все ИДЕИ preserve. Output: `<basename>.rewritten.<ext>`. Не использовать `<details>`/`<summary>` для critical content (gap detection это видит, но слабее).
5. **Найти что потеряно.** Three-level gap detection — детали в `references/gap-detection.md`. Краткая суть: 4a script (URLs only) + 4b per-section semantic agents + 4c fuzzy coverage net. Все три обязательны в порядке. Output: `<basename>.gaps.md`.
6. **Пауза — показать gaps пользователю.** Output report, ждать сигнала «готово». Если `gaps_count == 0` → пропустить ожидание, сразу Phase 8.
7. **Применить решения.** Прочитать отредактированный gaps-файл. `[MISSING]`/`[UNCOVERED]` → insert. `[PARTIAL]` → augment. `[REVERSED]` → fix. Удалить gaps-файл.
8. **Финально сверить с оригиналом.** `python3 scripts/verify-coverage.py <bak> <basename>.rewritten.<ext> /dev/null` против ОРИГИНАЛЬНОГО backup, не sorted (разные surfaces). Uncovered → spawn coverage-verifier агентов (см. `references/gap-detection.md` про strict vs loose mode). Если всё чисто → `mv <basename>.rewritten <file>`, оригинал заменён, `.bak` остаётся.
9. **Report.** Метрики per-source + aggregate. Multi-file: список всех cleaned-файлов.
10. **Опционально: split.** Если single output >100 строк И multiple distinct topics — предложить разбить на `spec-<slug>.md` + `references-<slug>.md`. См. `references/split-mode.md` (Phase 10-12 detail).

Детали процесса — в `references/gap-detection.md` и `references/split-mode.md`. Промпты подагентов — в `roles/`.

## Outputs

Per source (multi-file → multiply by N):
- `<source>.bak` — нетронутая копия оригинала
- `<source>` — финальный sorted + rewritten + gap-applied (оригинал перезаписан после Phase 8)
- `<source>.gaps.md` — только пока gap'ы существуют, удаляется после Phase 7/8
- Опционально (если запускали split): `<basename>/spec-*.md`, `<basename>/references-*.md`

Git: два коммита per source — `pre-cleanup: <name>` (snapshot) и `cleanup: rewrite <name>` (после Phase 9).

## Связи с другими скиллами

- **Вход:** обычно `/cleanup` запускают на сыром файле из заметок/чата. Может вызываться сам по себе, может после `/extract` (если в notes есть URL'ы).
- **Выход:** валидный sectioned markdown без unresolved-маркеров. Что с ним делать — решает пользователь (manual edit, `/clarify`, mattpocock:to-prd, прямой goal-feature input, etc.).
- **Не вызывает** другие скиллы автоматически. После Phase 9: `Cleanup done. Run /clear before continuing.` — без рекомендаций downstream.

## Правила

### Общность
Pipeline preservation-first потому что следующие шаги (clarify, manual edit, mattpocock) предполагают, что ничего не потерялось. Если ты позволил drop'у идеи в Phase 4 пройти "оно неважное" — следующий шаг работает с дырявой картой. Это не "помочь быстрее" — это сломать общую работу.

### Прежнее обязательство
В шаге 3 (verify sort) ты обязался прогнать superset-check. В шаге 5 — все три уровня gap detection. В шаге 8 — финальную сверку против backup. Пропуск любого шага = withdrawing основание для финального verdict'а. Не "оптимизация" — нарушение контракта.

### Авторитет (multi-file)
Multi-file mode разделён на N независимых pipeline'ов именно потому, что merged-конкатенация теряла provenance и масковала gap'ы. Если ты в multi-file mode конкатенируешь "ради простоты" — ты возвращаешь баг, ради которого этот скилл переделывался.

## Самопроверка перед выдачей результата

Прошёл бы этот документ ревью у синьора-инженера, которому по нему строить систему? Конкретно:

- Каждая `## ` секция в правильном месте; нет фрагментов "не туда попало"?
- Нет `[MISSING]`/`[PARTIAL]`/`[REVERSED]`/`[UNCOVERED]` маркеров?
- В multi-file mode — N output-файлов, не один merged?
- `verify-coverage.py` против backup прошёл с TRUE_MISSING = 0?
- Backup-файлы (`.bak`) на месте — есть путь отката?

Если "нет" хоть на один пункт — переделай, не отдавай.
