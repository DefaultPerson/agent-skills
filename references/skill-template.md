# Canonical SKILL.md template for agent-skills

Copy verbatim when creating a new skill, then fill in the placeholders. Body sections must appear in this order — see `references/principles.md` for the reasoning behind each.

## Frontmatter constraints

- `description` + `when_to_use` combined: ≤1536 characters (Anthropic hard limit)
- `description`: ≤500 characters, third-person, formula `"Use when ..."`. Triggers in EN + RU.
- `when_to_use`: ≤700 characters. Concrete scenarios + at least one `Do NOT use when ...` clause.
- `disable-model-invocation: true` only for destructive gating skills.
- `allowed-tools`: smallest set that works.

## Body section order (mandatory)

1. Intent (H1 + outcome sentence + canonical «буква = дух» block)
2. Слабые стороны и когда НЕ использовать (3-5 bullets)
3. Контрастные пары ❌ → ✅ (3-5 pairs, from real failure modes)
4. Роли (optional, only if the skill spawns subagents)
5. Что делает скилл (goal-language, ≤30 lines, overflow → references/)
6. Outputs (concrete artifacts)
7. Связи с другими скиллами
8. Правила (Cialdini-framed — authority / commitment / commonality; never liking / reciprocity)
9. Самопроверка перед выдачей результата (last gate before commit)

## Template

```markdown
---
name: <slug>
description: >
  Use when ... Tradeoff: ... Triggers: "<slug>", "/<slug>", "<ru-1>",
  "<ru-2>", "<en-1>", "<en-2>".
when_to_use: >
  <concrete scenarios>. Do NOT use when <anti-scenarios>.
disable-model-invocation: false
allowed-tools: [<minimal set>]
---

# <Skill Name>

<Одна фраза: user-facing outcome.>

> **Буква = дух.** Если правило мешает достичь цели, ради которой оно
> написано — правило ошибочно, а не цель. Не ищи лазейку в формулировке —
> спроси, что правило защищает, и защищай это.

## Слабые стороны и когда НЕ использовать

- **<weakness 1>**: <reason + alternative>
- **<weakness 2>**: <reason + alternative>
- **<weakness 3>**: <reason + alternative>

## Как делать неправильно vs правильно

### <Aspect 1>

❌ **Плохо:** <example input + bad response>
- <why bad>

✅ **Хорошо:** <same input + good response>
- <why good>

### <Aspect 2>

❌ ...
✅ ...

## Роли (если есть подагенты)

Шаблоны промптов: `roles/<role>.md`. Подстановки:

| Переменная | Источник |
|---|---|
| `{var_1}` | <where from> |
| `{var_2}` | <where from> |

Вызов:
\```
Agent(prompt=substitute("roles/<role>.md", vars))
\```

## Что делает скилл (по шагам)

1. <goal-language step — не algorithm-language>
2. <...>

Детали — в `references/process.md` и `scripts/*`.

## Outputs

- `<file 1>` — <description>
- `<file 2>` — <description>

## Связи с другими скиллами

- **Вход:** <typical caller>
- **Выход:** <typical next step — но не auto-chain'ить>
- **Не вызывает** другие скиллы автоматически.

## Правила

### Общность
<framing — мы (агент + пользователь + downstream) работаем над одним
артефактом>

### Прежнее обязательство
<framing — в шаге N выше ты согласился на X; это не повод для оптимизации>

### Авторитет (для дисциплинарных скиллов)
<framing — этот скилл существует именно потому что …; если делаешь иначе,
теряется само основание для его существования>

## Самопроверка перед выдачей результата

Прошёл бы этот <артефакт> ревью у синьора? Конкретно:
- <check 1 — конкретный, не «всё ли OK»>
- <check 2>
- <check 3>

Если "нет" хоть на один пункт — переделай, не отдавай.
```

## Anti-pattern reminders

- Don't write description as algorithm narration ("does X, Y, Z"). Use "Use when ..." instead.
- Don't use all-caps imperatives (ALWAYS, NEVER). Explain the reason so the model generalizes.
- Don't write contrast pairs from theory — only from real failure modes.
- Don't substitute Cialdini terms mechanically. Each rule must answer "why does this rule exist?" first.
- Don't dump multi-paragraph role prompts inline in SKILL.md. Move them to `roles/<name>.md`.
