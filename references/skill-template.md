# Canonical SKILL.md template for agent-skills

Copy verbatim when creating a new skill, then fill in the placeholders. Body sections must appear in this order — see `references/principles.md` for the reasoning behind each.

## Frontmatter constraints

- `description` + `when_to_use` combined: ≤1536 characters (Anthropic hard limit)
- `description`: ≤500 characters, third person, formula `"Use when ..."`. Triggers in EN + RU.
- `when_to_use`: ≤700 characters. Concrete scenarios + at least one `Do NOT use when ...` clause.
- `disable-model-invocation: true` only for destructive gating skills.
- `allowed-tools`: smallest set that works.

## Body section order (mandatory)

1. Intent (H1 + outcome sentence + canonical "letter = spirit" block)
2. Weaknesses and when NOT to use (3-5 bullets)
3. How to do it wrong vs right — contrast pairs ❌ → ✅ (3-5 pairs, from real failure modes)
4. Roles (optional, only if the skill spawns subagents)
5. What the skill does (goal-language, ≤30 lines, overflow → references/)
6. Outputs (concrete artifacts)
7. Connections to other skills
8. Rules (Cialdini-framed — authority / commitment / commonality; never liking / reciprocity)
9. Self-check before delivering the result (last gate before commit)

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

<One sentence: user-facing outcome.>

> **Letter = spirit.** If a rule blocks you from reaching the goal it was
> written for, the rule is wrong, not the goal. Don't look for a wording
> loophole — ask what the rule is protecting, and protect that.

## Weaknesses and when NOT to use

- **<weakness 1>**: <reason + alternative>
- **<weakness 2>**: <reason + alternative>
- **<weakness 3>**: <reason + alternative>

## How to do it wrong vs right

### <Aspect 1>

❌ **Wrong:** <example input + bad response>
- <why bad>

✅ **Right:** <same input + good response>
- <why good>

### <Aspect 2>

❌ ...
✅ ...

## Roles (if there are subagents)

Prompt templates: `roles/<role>.md`. Substitutions:

| Variable | Source |
|---|---|
| `{var_1}` | <where from> |
| `{var_2}` | <where from> |

Invocation:
\```
Agent(prompt=substitute("roles/<role>.md", vars))
\```

## What the skill does (step by step)

1. <goal-language step — not algorithm-language>
2. <...>

Details — in `references/process.md` and `scripts/*`.

## Outputs

- `<file 1>` — <description>
- `<file 2>` — <description>

## Connections to other skills

- **Input:** <typical caller>
- **Output:** <typical next step — but don't auto-chain>
- **Does not call** other skills automatically.

## Rules

### Commonality
<framing — we (agent + user + downstream) work on one artifact>

### Prior commitment
<framing — in step N above you agreed to X; this isn't a reason to optimize>

### Authority (for disciplinary skills)
<framing — this skill exists precisely because …; if you do otherwise,
the very basis for its existence collapses>

## Self-check before delivering the result

Would this <artifact> pass review by a senior? Concretely:
- <check 1 — concrete, not "is everything OK">
- <check 2>
- <check 3>

If "no" on any item — redo, don't ship.
```

## Anti-pattern reminders

- Don't write description as algorithm narration ("does X, Y, Z"). Use "Use when ..." instead.
- Don't use all-caps imperatives (ALWAYS, NEVER). Explain the reason so the model generalizes.
- Don't write contrast pairs from theory — only from real failure modes.
- Don't substitute Cialdini terms mechanically. Each rule must answer "why does this rule exist?" first.
- Don't dump multi-paragraph role prompts inline in SKILL.md. Move them to `roles/<name>.md`.
