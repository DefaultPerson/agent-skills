# Principles canon

Shared across every SKILL.md in agent-skills. Read once, internalize, don't re-paste body content into individual skills — they should reference back here.

## Letter = spirit

Every SKILL.md embeds this block right after the H1:

> **Буква = дух.** Если правило мешает достичь цели, ради которой оно
> написано — правило ошибочно, а не цель. Не ищи лазейку в формулировке —
> спроси, что правило защищает, и защищай это.

### Why this matters (anti-example)

**Rule:** «не редактируй файлы вне поля Files задачи».

**Letter loophole:** «Я не редактирую — я создаю новый файл, его в Files нет, значит запрет не действует».

**Spirit of the rule:** задача атомарна; изоляция воркеров обеспечивается тем, что каждый трогает заранее объявленные файлы. Создание нового файла, который другие задачи могут начать читать — нарушение изоляции, даже если буква запрета его не описывает.

**Correct response:** остановиться → «что правило защищает?» → «атомарность задачи и независимость воркеров» → «создание файла вне Files ломает это?» → «да» → не делать.

**Wrong response:** «формально нарушения нет, делаю».

## Contrast pairs ❌ → ✅

Every SKILL.md has 3-5 contrast pairs. Rules:

- Always pairs, never solo "good" examples.
- ❌ first, then ✅ (Superpowers data: framing this way pushes compliance 33% → 72%).
- Both halves use the same input — only the response differs.
- Pull from real failure modes, not theory. If you can't think of a real failure mode, the skill is undertested.
- 3-5 pairs total. More dilutes; fewer leaves gaps.

## Honest weaknesses

Every SKILL.md lists 3-5 honest weaknesses up front. Purpose: reduce false-positive triggering. If you can't think of three weaknesses, the skill is over-scoped or under-tested.

What does NOT go in the weakness section:
- Generic LLM limitations
- "User might misuse it" — that's the calling model's problem
- Platitudes

What does:
- Concrete failure modes on this skill's specific input class
- Resource costs (time, agents, context)
- Cases where a simpler tool wins

## Cialdini framing for rules

Use these levers. The first three are the ones authorized for agent-skills:

- **Authority** — appeal to the reason behind the design. *"This skill exists precisely because X. If you do Y, the very basis for its existence collapses."*
- **Prior commitment** — appeal to something earlier in the skill the agent already accepted. *"In step N you agreed to do X. Skipping it isn't optimization; it's withdrawing the basis for trusting the result."*
- **Commonality** — appeal to shared work. *"Downstream skills/users/sessions act on your output. Producing a shortcut that locally feels faster but breaks the shared workflow is a bad trade."*

**Forbidden levers:**

- ❌ **Liking** — *"I like X"*, *"this is a clean pattern"*. Manipulative, not evidence-based, collapses on first counterexample.
- ❌ **Reciprocity** — *"I gave you tools, you owe me X"*. Fake debt dynamic.
- ❌ **Weak social proof** — *"all good skills do this"* without actual data. Specific data points (like the 33%→72% one) are fine; vague gestures aren't.

Mapping by skill type:
- **Disciplinary** (verify-style, refusal-heavy) → authority + prior commitment dominate.
- **Collaborative** (cleanup, clarify) → commonality + social proof (where backed by data).
- **Multi-step orchestration** → prior commitment dominates (every step lands a commitment that later steps draw on).

## Senior-review self-check

Last gate before the skill commits output. Three variants:

**Code-producing:**
> Прошёл бы этот код ревью у синьора-инженера? Конкретно: нет заглушек/`TODO`/`console.log`/`print(`; использованы существующие паттерны из codebase (grep сделан); тесты/AC прогнаны на текущем состоянии файлов. Если "нет" — переделай, не отдавай.

**Spec/note-producing:**
> Прошёл бы этот документ ревью у синьора-инженера, которому по нему строить систему? Конкретно: каждый AC имеет proof-команду (не «это работает»); нет `TBD`/`...`/placeholder'ов; каждая задача выполнима независимым воркером без вопросов. Если "нет" — переделай.

**Read-only / side-effect:**
> Прошёл бы этот результат ревью у синьора? Конкретно: проверка-1; проверка-2; проверка-3. Если "нет" — переделай, не отдавай.

Placement: right before the Outputs section in SKILL.md. Reasoning — it's the last thing the model reads in its execution mental model, so it catches the commit-time omission rather than the planning-time omission.

## Role files vs SKILL.md

When a skill spawns subagents, separate the invocation contract from the role's content:

- `SKILL.md` contains: when the role is spawned, table of substituted variables, how to consume the response.
- `roles/<name>.md` contains: the literal text the subagent reads as its prompt — character, framing, input contract, output contract, anti-patterns.

This separation lets you edit role behavior without re-reading orchestration logic, and vice versa. Also forces explicit variable contracts, which catches "I forgot to substitute X" bugs.

Substitution helper (recommended): `scripts/substitute.py` reads `roles/<name>.md` + JSON variables → fully formed prompt. Removes manual substitution errors.

## Length budgets

- `SKILL.md`: target 150-250 lines. Hard ceiling 500 (Anthropic guidance). Overflow goes to `references/<topic>.md` or `scripts/`.
- `roles/<name>.md`: target 50-150 lines. Overflow probably means the role is doing two things — split.
- `references/<name>.md`: no hard limit, but if a reference exceeds 500 lines, audit whether it's actually one topic.
