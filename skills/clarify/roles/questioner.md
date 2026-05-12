# Questioner — Phase 2 clarifying-questions pattern

This is not a subagent — it's a format contract for how clarify itself generates user questions via AskUserQuestion in step 2. Kept in a separate file so the format can be edited without re-reading the whole SKILL.md.

## When to ask

Step 2, hard gate. Do NOT proceed to step 3 (decomposition) while ambiguous points are unresolved.

## Triggers for asking

Generate a question only if there is REAL ambiguity:
- Item flagged `[NEEDS CLARIFICATION]` in step 1
- Requirement can be interpreted two ways
- Constraint is missing (performance target, scale, auth, persistence)
- Priority conflict between features (which one matters more?)

DO NOT generate a question just for the sake of it:
- ❌ "Which backend should we use?" if the spec already names the stack
- ❌ "Do you want tests?" — default YES, ask only if there's a reason to think otherwise
- ❌ Stylistic preferences ("which naming convention?") — pick one, put it in Constraints

## Question format (via AskUserQuestion)

Maximum 4 questions per call (Anthropic AskUserQuestion limit). Each question:

- **Question:** concrete, no "please" / "if you're curious", ends with `?`
- **Header:** 1-3 words, displayed as a chip/tag (max 12 chars)
- **Options:** 2-4 mutually exclusive choices. Recommended option first, with `(Recommended)` suffix. Description per option — what happens on selection + trade-off in one line.
- multiSelect: usually `false`. `true` only if choices are not mutually exclusive (e.g. "which features to enable?").

## Question example

```
Question: What auth method should the API use?
Header: Auth method
Options:
  - label: "JWT tokens (Recommended)"
    description: "Stateless, standard for REST APIs. Easy horizontal scaling. Trade-off: revoking sessions requires a denylist."
  - label: "Session-based"
    description: "Server-side sessions in Redis/DB. Easier to revoke. Trade-off: stateful, harder to scale."
  - label: "API keys"
    description: "Simple, for internal services. No user concept. Trade-off: not suitable for end-user auth."
```

## Anti-patterns

❌ Asking about things already specified in the spec.
❌ Pushing defaults onto the user (a CLI tool without users doesn't need JWT).
❌ Options without trade-off descriptions.
❌ Open-ended questions ("which stack?") — give 2-4 concrete options.
❌ More than 5 questions total in step 2 — a sign that the spec is too raw; send it back to cleanup or to the user with feedback.

## After the answers

Each answer updates the relevant in-memory spec section (Constraints, scope, FR-NNN). Re-check — are all `[NEEDS CLARIFICATION]` markers closed? If not — one more iteration of step 2 (but no more than 2 iterations total).
