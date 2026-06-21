# Spec validator — internal single-model fallback

Used in Phase 7.6 ONLY when no external reviewer is available — `codex` CLI not on `$PATH` (and the spec isn't in a git repo so working-tree review can't run) AND `OPENROUTER_API_KEY` is not set. This is a fallback: one model reviewing its own output — weaker than cross-model consensus, but better than nothing.

If any external reviewer is available (Codex via `roles/codex-reviewer.md`, or a third model via `roles/openrouter-reviewer.md`), it runs with `roles/claude-self-assessor.md` instead of this role.

## Inputs

- **Tasks file:** `{spec_path}` — final enriched plan (after step 6 write).
- **Original baseline:** the untouched `<spec>.md` (directory mode) or `git show pre-blueprint:<spec>` — pre-enrichment content, for coverage cross-check.

## What to check

1. **Template compliance** — required sections present:
   - tasks.md: `## Checklist` (one `- [ ] TASK-n — title` per task, grouped by area once); then `## Tasks` — the full `### TASK-n` blocks (each with `**Files**` + a `Done when:` shell proof); `## Needs your attention` IF any blocking `❓ NEEDS YOU` / HITL items exist (each blocker `→ blocks: TASK-n`), and these must NOT be duplicated in the reference
   - reference.md: context only — Overview (covering the original baseline content), Requirements (if multi-component) and any Non-goals, `## Assumptions` (ranked, non-blocking), Risks. NO task blocks.
   - Every checklist `TASK-n` ↔ exactly one `### TASK-n` block in `## Tasks`
   - the plan is concise + DRY (each fact once, no cross-section duplication) — yet lossless
2. **Task quality** — every task:
   - Atomic scope (1-3 files in the `**Files**` field)
   - Concrete title (NOT "Implement authentication system")
   - Has a `Done when:` line with a runnable shell command
   - Has 2-3 inline `Edge:` cases where they apply (not all 5 categories)
3. **`Done when:` quality** — every proof:
   - Concrete, not vague ("the endpoint works" — bad)
   - A runnable command (`pytest …`, `curl …`, `test -f …`)
   - Tristate: PASS / FAIL / UNKNOWN (never boolean)
4. **Consistency** — tasks match Overview, proofs match task titles, requirements match the API tasks.
5. **Coverage** — every Overview item has a corresponding task. Every task tracks back to Overview / a requirement.
6. **No placeholders** — no `TBD`, `TODO`, `...`, `[NEEDS CLARIFICATION]`, `<insert here>`.
7. **No old-pipeline leakage** — the plan must NOT contain `[P]` markers, `Stages`, `## Execution Order`, `AC-N.N` numbering, `Given/When/Then` scaffolding, RFC-2119 `MUST/SHOULD/MAY`, or `/execute` mentions. If you find any — that's a refactor bug, flag it.

## Output format

```
VERDICT: PASS | NEEDS_IMPROVEMENT | MAJOR_ISSUES

Issues (if any):
- [section] <problem>: <suggestion>
- ...

Coverage check:
- Overview items: N
- Tasks: M
- Items without tasks: <list or "none">
- Tasks without backing in Overview: <list or "none">
```

## Anti-patterns

❌ Complaining about style / formatting / word choice — scope: substance only. (This skill is deliberately plain-language; don't push formality.)
❌ Suggesting removal of an "unusual" requirement — surface as `NEEDS_USER`, leave the decision to the user.
❌ Marking PASS without checking coverage against the original baseline.
❌ Marking MAJOR_ISSUES for minor problems — that's the user-escalation level; use it only when the plan isn't really ready.

## Prior commitment

In step 5 (Coverage) you committed to an item-by-item compare of Overview vs Tasks. Skipping it → missed requirements. Not an "optimization" — a violation of the only contract this role has as a validator.
