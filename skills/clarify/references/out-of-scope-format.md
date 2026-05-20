# `.out-of-scope/` knowledge base

> Adapted from mattpocock/skills `triage/OUT-OF-SCOPE.md` (MIT).

The `.out-of-scope/` directory in a repo stores durable records of rejected feature requests. Two purposes:

1. **Institutional memory** — why a feature was rejected, so the reasoning isn't lost when the spec / issue is closed.
2. **Deduplication** — when a similar idea returns, surface the prior decision instead of re-litigating.

## When /clarify writes here

Only when the **Scope-cut audit** (Phase 5) resolves a deferral as **"Drop entirely (firm)"** — not a `MAY (v2)` tag, not a "later" — and the user explicitly opts into recording the rejection. Treat firm drops as durable; tentative deferrals stay in spec metadata.

## Directory layout

```
.out-of-scope/
├── dark-mode.md
├── plugin-system.md
└── graphql-api.md
```

One file per **concept**, not per spec. Multiple specs that requested the same thing get listed under the file's "Prior requests" section.

## File format

```markdown
# {Concept name}

{1-2 sentence summary of what the project will NOT do.}

## Why this is out of scope

{Substantive reason: project scope, technical constraint, strategic decision. NOT "we're too busy right now" — that's a deferral, not a rejection.}

## Prior requests

- spec `2026-04-12-billing-rewrite.md` — section "Multi-currency support" was dropped
- spec `2026-05-03-payment-overhaul.md` — section "Auto-detect currency from IP" was dropped
```

## Naming

Short kebab-case for the concept: `dark-mode.md`, `multi-currency.md`, `graphql-api.md`. Must be recognizable from the file name alone.

## When /clarify reads `.out-of-scope/`

In Phase 1 (read+analyze), if `.out-of-scope/*.md` exists, read all files. If the input spec mentions a concept matching one of these files (by concept similarity, not just keyword), surface in Phase 2 questioner: "Spec mentions X; this was previously rejected per `.out-of-scope/X.md` for reason Y. Reconsider, or confirm the rejection still stands?"

If the user says "rejection still stands" → drop the section from spec scope.
If the user says "reconsider" → the `.out-of-scope/` file gets deleted as a side effect (the spec proceeds with the feature in scope).

## What this is NOT

- Not a TODO list for v2 work — use the spec's own `MAY (deferred)` tagging for that.
- Not a backlog — issue tracker is for that.
- Not bug rejections — only enhancement / scope rejections.
