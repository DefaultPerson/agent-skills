# Principles canon

Shared across every SKILL.md in agent-skills. Read once, internalize, don't re-paste body content into individual skills — they should reference back here.

## Letter = spirit

Every SKILL.md embeds this block right after the H1:

> **Letter = spirit.** If a rule blocks you from reaching the goal it was
> written for, the rule is wrong, not the goal. Don't look for a wording
> loophole — ask what the rule is protecting, and protect that.

### Why this matters (anti-example)

**Rule:** "do not edit files outside the task's Files field".

**Letter loophole:** "I'm not editing — I'm creating a new file; it's not in Files, so the ban doesn't apply".

**Spirit of the rule:** the task is atomic; worker isolation is guaranteed by each one touching pre-declared files. Creating a new file that other tasks may start reading breaks isolation, even if the literal ban doesn't describe it.

**Correct response:** stop → "what is the rule protecting?" → "task atomicity and worker independence" → "does creating a file outside Files break that?" → "yes" → don't do it.

**Wrong response:** "no formal violation, going ahead".

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
> Would this code pass review by a senior engineer? Concretely: no stubs / `TODO` / `console.log` / `print(`; existing patterns from the codebase reused (grep done); tests / AC run against current file state. If "no" — redo, don't ship.

**Spec/note-producing:**
> Would this document pass review by a senior engineer who has to build the system from it? Concretely: every AC has a proof command (not "it works"); no `TBD` / `...` / placeholders; every task is executable by an independent worker without questions. If "no" — redo.

**Read-only / side-effect:**
> Would this result pass review by a senior? Concretely: check 1; check 2; check 3. If "no" — redo, don't ship.

Placement: last section in SKILL.md, after Rules. Reasoning — it's the last thing the model reads in its execution mental model, so it catches the commit-time omission rather than the planning-time omission. See `references/skill-template.md` for the canonical section order.

## Role files vs SKILL.md

When a skill spawns subagents, separate the invocation contract from the role's content:

- `SKILL.md` contains: when the role is spawned, table of substituted variables, how to consume the response.
- `roles/<name>.md` contains: the literal text the subagent reads as its prompt — character, framing, input contract, output contract, anti-patterns.

This separation lets you edit role behavior without re-reading orchestration logic, and vice versa. Also forces explicit variable contracts, which catches "I forgot to substitute X" bugs.

Substitution today is manual: Claude reads `roles/<name>.md` via the Read tool, substitutes `{var}` placeholders inline before passing the result as a subagent prompt. A future enhancement could add `bin/substitute.sh` (read template + JSON vars → stdout) to reduce missed-variable errors — currently relies on the calling SKILL.md providing an explicit substitutions table.

## Length budgets

- `SKILL.md`: target 150-250 lines. Hard ceiling 500 (Anthropic guidance). Overflow goes to `references/<topic>.md` or `scripts/`.
- `roles/<name>.md`: target 50-150 lines. Overflow probably means the role is doing two things — split.
- `references/<name>.md`: no hard limit, but if a reference exceeds 500 lines, audit whether it's actually one topic.
