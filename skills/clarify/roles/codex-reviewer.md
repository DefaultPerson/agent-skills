# Codex adversarial reviewer — focus brief for `codex:adversarial-review`

This file is NOT the full prompt. `codex:adversarial-review` (from `openai/codex-plugin-cc`) owns the adversarial role, attack-surface heuristics, JSON output schema, and grounding rules. We only pass `USER_FOCUS` text to tell Codex what to look for in THIS particular review.

The orchestrator reads this file, substitutes nothing (no `{vars}` here — it's a static brief), and passes the text as the focus argument to `/codex:adversarial-review`.

## The focus brief (passed verbatim as USER_FOCUS)

```
Adversarial review of an enriched markdown spec file (NOT code). Apply your
attack-surface skepticism by analogy to a spec instead of an implementation.

Look for:
- Acceptance Criteria without a runnable shell proof command, or with vague
  "it works" / "manual check" phrasing.
- Tasks that aren't atomic — touching many files at once, multiple purposes
  mixed, no clear single deliverable.
- Ambiguous task descriptions that two builders would interpret differently.
- Contradictions between Functional Requirements (FR-NNN entries).
- Coverage gaps — Overview items with no backing task, or tasks with no
  Overview reference.
- Missing edge cases for input validation, boundaries, error paths,
  concurrency, or security where they clearly apply to the task domain.
- Placeholders: TBD, TODO, "...", [NEEDS CLARIFICATION], <insert here>.
- Inconsistent dependencies — TASK-N references TASK-X that doesn't exist.

User-intent preservation rule (critical):
- If a requirement looks unusual or under-justified, do NOT recommend
  removing or normalizing it. The user added it on purpose. Surface as
  a finding with confidence ≤0.5 and recommendation "ask user".
- Never propose deleting or "fixing" a user-stated requirement just
  because it looks unconventional.

Scope NOT to review:
- Style, formatting, word choice, section ordering, markdown syntax,
  variable naming. These are not material findings.
- Length — long but purposeful is fine.

Stay grounded: every finding must be defensible from the spec text.
Quote the exact spec line in each finding. Use `needs-attention` if
there's any material risk; use `approve` only if you cannot defend a
substantive finding.
```

## Why we use codex:adversarial-review

The built-in `codex:adversarial-review` command (from `openai/codex-plugin-cc`) provides:
- A pre-baked adversarial role ("break confidence, not validate")
- Structured JSON output (file, line_start, line_end, confidence, recommendation)
- Background-mode execution for long reviews
- Working-tree scope so it sees the current spec edit (uncommitted is fine)

The trade-off: the built-in attack-surface list is code-oriented (auth, data loss, race conditions). Our focus brief above maps it to spec concerns. The Codex model is smart enough to translate the spirit ("adversarial scrutiny applied to this artifact") to spec review when the focus text is explicit.

If `codex-plugin-cc` is not installed, clarify falls back to `roles/spec-validator.md` — same goal (find substantive issues in the spec), weaker model (single-model Claude self-review).
