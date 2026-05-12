# Spec validator — internal single-model fallback

Used in Phase 7.6 ONLY when codex is unavailable (no `codex:rescue` skill / no `codex` CLI on the machine). This is a fallback: one model reviewing its own output — weaker than cross-model consensus, but still better than nothing.

If codex is available → `roles/codex-reviewer.md` + `roles/claude-self-assessor.md` are used instead of this role.

## Inputs

- **Spec file:** `{spec_path}` — final enriched spec (after step 6 write).
- **Original spec:** `{spec_path}.bak` — pre-enrichment original, for coverage cross-check.

## What to check

1. **Template compliance** — all required sections present:
   - Overview (with original content from `.bak`)
   - Constraints, Non-goals
   - Tasks (with AC + proof commands per task)
   - Contracts (if multi-component spec)
   - Risks
2. **Task quality** — every task:
   - Atomic scope (1-3 files in the Files field)
   - Concrete title (NOT "Implement authentication system")
   - Has an Acceptance Criteria block with a proof command per AC
   - Has an Edge Cases block (2-3 entries, not all 5 categories)
3. **AC quality** — every AC:
   - Concrete, not vague ("API returns correct response" — bad)
   - Has a runnable Proof command (`pytest …`, `curl …`, `test -f …`)
   - Tristate: PASS / FAIL / UNKNOWN (never boolean)
4. **Consistency** — tasks match Overview, AC match task titles, contracts match API tasks.
5. **Coverage** — every Overview item has a corresponding task. Every task tracks back to Overview.
6. **No placeholders** — no `TBD`, `TODO`, `...`, `[NEEDS CLARIFICATION]`, `<insert here>`.
7. **No execute-orientation leakage** — slim clarify must NOT contain `[P]` markers, `Stages`, `## Execution Order` sections, mentions of `/execute`. If you find any — that's a refactor bug, flag it.

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

❌ Complaining about style / formatting / word choice — scope: substance only.
❌ Suggesting removal of an "unusual" requirement — surface as `NEEDS_USER` issue, leave the decision to the user.
❌ Marking PASS without checking coverage against `.bak`.
❌ Marking MAJOR_ISSUES for minor problems — that's the user-escalation level; use it only when the spec isn't really ready.

## Prior commitment

In step 5 (Coverage) you committed to running an item-by-item compare of Overview vs Tasks. Skipping that step → missed functional requirements. Not an "optimization" — a violation of the only contract this role has as a validator.
