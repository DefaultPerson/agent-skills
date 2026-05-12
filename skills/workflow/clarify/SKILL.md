---
name: clarify
description: >
  Use when you have a clean spec/notes file that needs to be made
  implementation-ready: decomposed into atomic tasks with verifiable
  acceptance criteria (Given/When/Then + shell proof commands),
  constraints, edge cases, and risk surface. Output is suitable for
  human implementation, mattpocock:tdd, or Claude Code goal feature.
  Tradeoff: slow and thorough — overkill for tasks under 1 hour. For
  freeform PRD use mattpocock:to-prd instead. Triggers: "clarify",
  "/clarify", "уточни спеку", "enrich spec", "обогати спеку",
  "decompose spec".
when_to_use: >
  The input is a cleaned-up markdown spec/notes file (probably after
  /cleanup) that captures the WHAT but not the HOW. You want to turn it
  into atomic tasks with shell-verifiable AC before handing to a builder
  (human, mattpocock:tdd, or goal feature). Do NOT use for raw chat
  exports (run /cleanup first), for already-decomposed specs, or for
  product-management-style PRDs (mattpocock:to-prd is better suited).
allowed-tools: [Bash, Glob, Grep, Read, Edit, Write, Agent, AskUserQuestion, WebSearch, WebFetch]
---

# Clarify

Turn a clean spec into an implementation-ready document with atomic tasks, verifiable acceptance criteria, contracts, edge cases, and risks.

> **Буква = дух.** Если правило мешает достичь цели, ради которой оно
> написано — правило ошибочно, а не цель. Не ищи лазейку в формулировке —
> спроси, что правило защищает, и защищай это.

## Usage

```
/clarify <spec.md> [--consensus-rounds N]
```

`--consensus-rounds` default 3. Set to 0 to skip cross-model consensus loop (Phase 7.6) — only internal validation runs.

## Слабые стороны и когда НЕ использовать

- **Медленный и тщательный — оверкилл для часовых задач.** Декомпозиция + AC + edge cases + 3 раунда консенсуса (если codex доступен) занимают 10-15 минут. Если задача меньше — пиши AC от руки.
- **Не работает с сырыми chat-экспортами или unstructured notes.** Spec на входе должен быть уже sectioned по `## ` (после `/cleanup`). Если нет — abort.
- **Не подходит для product-style PRD.** Скилл force'ит test-first AC с proof-командами; для product-management PRD используй `mattpocock:to-prd` (freeform success metrics).
- **Phase 7.6 consensus loop требует codex CLI.** Без него — fallback на internal validation (одна модель проверяет свой output, слабее).
- **Не для autonomous orchestration.** В output'е нет `[P]` markers, Stages, dependency graphs — execute pipeline удалён из этого репо в v2.0. Output под mattpocock:tdd или ручную работу.

## Как делать неправильно vs правильно

### AC формат

❌ **Плохо:** `AC-1.1: API returns correct response`
- "Correct" — кто решит?
- Нет proof-команды
- Boolean (works / doesn't) — нет UNKNOWN

✅ **Хорошо:** `AC-1.1: GET /api/users returns 200, JSON with {id,name,email}, <200ms`
- Конкретные числа и поля
- Proof: `curl -w '%{time_total}' localhost:8080/api/users | jq '.[].id'`
- Tristate: PASS / FAIL / UNKNOWN (если сервер не запущен)

### Task scope

❌ **Плохо:** `TASK-1: Implement authentication system`
- Затрагивает много файлов
- Множественные цели смешаны
- Невозможно verify одной командой

✅ **Хорошо:** `TASK-1: Create User model в src/models/user.py с полями email/password`
- 1 файл, чёткие границы
- Atomic — одна testable деливерабл
- AC: `python -c "from src.models.user import User; User(email='a@b', password='x')"` без error'ов

### Cross-model consensus disagreement

❌ **Плохо:** Codex выдал NEEDS_IMPROVEMENT с issue "requirement X выглядит unusual, предлагаю удалить". Применяю — удаляю.
- Пользователь поставил requirement намеренно.
- Удалением я "помог себе быстрее", а пользователю — заминусовал его intent.

✅ **Хорошо:** Issue type = NEEDS_USER (либо Codex его сам так пометил, либо Claude self-assessor reclassified). AskUserQuestion с обоими взглядами. Пользователь решает.

## Роли

Step 2 (questioner pattern) и Phase 7.6 consensus loop (с fallback validator) — все шаблоны в `roles/`:

- `roles/questioner.md` — format-контракт для AskUserQuestion в Step 2 (не subagent — format spec)
- `roles/spec-validator.md` — fallback internal validation, используется в Phase 7.6 если codex недоступен
- `roles/codex-reviewer.md` — Phase 7.6 Codex cross-model review (через `codex:rescue`)
- `roles/claude-self-assessor.md` — Phase 7.6 Claude self-assess fresh subprocess (`claude -p`)

Подстановки:

| Переменная | Источник |
|---|---|
| `{spec_path}` | spec-файл после Phase 7 write |
| `{round}` | счётчик раундов в Phase 7.6 (1, 2, 3) |
| `{spec_path}.bak` | original spec (pre-enrichment) для coverage check |
| `{spec_path}.critique.<round-1>.md` | prior critique (для round > 1) |

Спавн codex review: `Agent(subagent_type="codex:rescue", prompt=substitute("roles/codex-reviewer.md", vars))`.
Спавн claude self-assess: bash subprocess `claude -p` с prompt из `roles/claude-self-assessor.md`.
Fallback validator (без codex): `Agent(subagent_type="Explore", prompt=substitute("roles/spec-validator.md", vars))`.

## Что делает скилл (по шагам)

1. **Прочесть и проанализировать spec.** Validate (markdown, есть `## ` headers, нет cleanup markers `[MISSING]`/etc), classify тип (product / technical / small), scan codebase если есть, отметить `[NEEDS CLARIFICATION]` markers.
2. **Спросить пользователя что неясно** (hard gate). Max 5 вопросов через AskUserQuestion — формат в `roles/questioner.md`. Если spec уже clear — skip.
3. **Декомпозировать на atomic tasks.** Формат адаптируется к типу — детали в `references/task-format.md`. Главное: каждый task — 1-3 файла, AC с Given/When/Then + Proof shell-команда (НИКАКИХ `[P]` markers и Stages — execute удалён).
4. **Определить contracts** (FR-NNN format, MUST/SHOULD/MAY). Skip если spec small или single-component. Детали в `references/contracts.md`.
5. **Self-review checklist.** Placeholder scan, internal consistency, scope check, ambiguity check. Фиксы — loop назад на нужный phase.
6. **Записать enriched spec.** Backup оригинала (`<spec>.bak`), записать enriched в исходный путь. Структура шаблонов: см. `references/task-format.md`.
7. **Mechanical validation.** `python3 scripts/verify-spec.py <spec>`. FAIL → fix and re-run.
8. **Cross-model consensus loop (Phase 7.6).** Codex review + Claude self-assess, итеративно до CONSENSUS или max rounds. Детали — следующая секция. Можно skip через `--consensus-rounds 0`.
9. **Approval gate.** Сводный отчёт + AskUserQuestion (Approve / Modify / Questions). После approval: `"Spec approved. /clear before continuing."` — без рекомендаций downstream-скиллов.

Старая «Execution Order» секция (Stages, [P] markers, dependency graph для parallel spawn) — УДАЛЕНА в v2.0. Была для execute orchestration, которого больше нет.

## Phase 7.6 — Cross-model consensus loop

После Step 6-7 (write enriched spec + verify-spec.py mechanical check) запускается convergence loop. Step 8 в общем walkthrough — это и есть Phase 7.6.

```
MAX_ROUNDS = consensus_rounds_flag (default 3, 0 disables)
round = 0

if not has_codex():
  log WARNING "codex not installed, falling back to single-model validation"
  run roles/spec-validator.md (fallback)
  → CONSENSUS or NEEDS_FIX (single round only)
  goto Step 9 (approval gate)

while round < MAX_ROUNDS:
  round += 1

  # Codex review
  critique = Agent(subagent_type="codex:rescue",
                   prompt=substitute("roles/codex-reviewer.md",
                                     {spec_path, round}))
  save → <spec>.critique.<round>.md

  # Claude self-assessment в fresh subprocess
  assessment = bash: claude -p < substitute("roles/claude-self-assessor.md",
                                            {spec_path, round})

  # Exit?
  if critique.verdict == PASS and assessment.verdict == AGREE_PASS:
    → CONSENSUS, exit loop

  # Process issues
  for each issue in critique.issues:
    cat = assessment.categorization[issue.id]
    if cat == ACCEPT: apply suggestion to spec
    elif cat == REJECT_PETTY: log to <spec>.critique.<round>.rejected.md
    elif cat == NEEDS_USER: queue для AskUserQuestion

  if queue not empty:
    AskUserQuestion с issues
    apply user decisions

  # Oscillation detection
  if hash(critique.issues) == hash_round_minus_2:
    → ESCALATE user: "модели зациклились, твой call"
    break

if round == MAX_ROUNDS and no CONSENSUS:
  ESCALATE user: "(A) approve as-is, (B) abort, (C) one more round"
```

Failure modes:
- **Codex unavailable** → fallback к `roles/spec-validator.md` (single-model), workflow продолжает.
- **Models gang up on user intent** → `roles/codex-reviewer.md` явно запрещает proposing removal of unusual requirements (surface as NEEDS_USER instead). `roles/claude-self-assessor.md` дублирует правило.
- **Petty disagreements** → REJECT_PETTY категория, logged в rejected.md с reasoning, не применяется.
- **Oscillation** → hash comparison rounds N and N-2, escalation.

## Outputs

- `<spec>.bak` — оригинал до enrichment
- `<spec>` — перезаписан enriched-версией
- `<spec>.critique.1.md`, `<spec>.critique.2.md`, ... — Codex critiques per round (если consensus loop запускался)
- `<spec>.critique.<round>.rejected.md` — петля отказа от petty issues с reasoning (если были)

Git: `pre-clarify: <name>` (snapshot before) и `clarify: enrich <name>` (после Phase 7).

## Связи с другими скиллами

- **Вход:** обычно после `/cleanup` (sectioned markdown без `[MISSING]` markers). Может быть и manual-составленный spec, если он structurally валиден.
- **Выход:** enriched spec с AC + proof commands, пригодный для:
  - mattpocock:tdd (тест-first implementation)
  - Claude Code goal feature (для измеримых критериев)
  - ручной реализации
  - independent `claude -p` verify для AC проверки после implementation
- **Не вызывает** другие скиллы автоматически. После Step 9 (approval): `Spec approved. /clear before continuing.` — без рекомендаций.
- **Cross-model dependency**: Phase 7.6 использует `codex:rescue` если установлен. Без него — graceful fallback.

## Правила

### Общность
Spec — shared artifact. Downstream работа (mattpocock:tdd, goal feature, manual builder) принимает решения по нему. Если ты пропустил placeholder, vague AC, или contradictory FR — следующий шаг работает с дырявой картой. Не "помог быстрее" — сломал общую работу.

### Прежнее обязательство
В шаге 5 (self-review) ты обязался прогнать placeholder scan + consistency + ambiguity check. В шаге 7 — `verify-spec.py`. В шаге 8 — consensus loop (или fallback). Пропуск любого шага = withdrawing основание для финального verdict'а пользователя.

### Социальное доказательство (cross-model rationale)
Phase 7.6 существует, потому что single-model self-review слабее. По данным консенсус-исследований (AltimateAI/claude-consensus, ARIS — adversarial cross-model review), независимая вторая модель ловит issues, которые первая bias-ит мимо. Если ты "пропускаешь" Phase 7.6 при наличии codex — теряется единственное реальное основание доверять spec'у больше, чем "Claude себя похвалил".

## Самопроверка перед выдачей результата

Прошла бы эта спека ревью у синьора-инженера, которому по ней строить систему? Конкретно:

- Каждый AC имеет конкретную proof-команду (не "это работает", не "manual check")?
- Нет placeholder'ов (`TBD`, `...`, `[NEEDS CLARIFICATION]`, `<insert here>`)?
- Каждая задача atomic — 1-3 файла, single purpose, выполнима независимым воркером без вопросов к автору?
- Phase 7.6 прошёл (или явно skipped с reasoning)?
- Coverage: каждый item из Overview имеет хотя бы один task? Каждый task tracks обратно в Overview / FR?
- Backup `<spec>.bak` существует — пользователь может откатиться?

Если "нет" хоть на один пункт — переделай, не отдавай.
