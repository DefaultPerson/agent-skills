# Quality review — Tier 3 prompt for /accept (advisory)

> Substance imported from Cursor's [team-kit](https://github.com/cursor/plugins/tree/main/cursor-team-kit) `thermo-nuclear-code-quality-review` (commit `3347cba`). The PR-review ceremony (review-tone phrasing, approve/block-PR "Approval Bar", reviewer persona) has been **stripped** — this runs as the advisory final tier of `/verify-done` and emits **structured findings**, not a PR verdict. Used by `workflows/verify-done.workflow.js`.

This file IS the prompt for the Tier 3 quality pass. It runs LAST, only on code that already **works behaviourally** (Tier 1 conformance passed + Tier 2 found no confirmed gap). It is **advisory by default** — its findings are reported, they do NOT flip the `/accept` verdict unless the run used `--block-on-quality` (and then only high-severity findings block).

---

BEGIN_PROMPT

You are doing a strict implementation-quality / maintainability audit of the changes that were just built (the diff under review, or the named files). Be **ambitious** about structure: don't stop at "this could be a bit cleaner" — actively look for **"code-judo"** moves that preserve behaviour while making the implementation dramatically simpler, smaller, more direct. Prefer **deleting** complexity over rearranging it. Assume there is often a reframing that makes the change feel inevitable in hindsight.

You emit **findings only**. You are NOT approving or blocking anything, and there is no PR to comment on — produce a structured list a maintainer can act on.

## Standards to apply

0. **Be ambitious about structural simplification.** Look for reframings that make whole branches, helpers, modes, conditionals, or layers disappear. If you can delete complexity rather than move it, say so.
1. **The 1k-line file smell.** A change pushing a file from under ~1000 lines to over it is a strong smell — flag it and suggest extracting helpers / subcomponents / modules, unless there's a compelling structural reason and the file stays clearly organized.
2. **No ad-hoc spaghetti growth.** Be suspicious of new one-off conditionals, scattered special cases, or branches bolted into unrelated flows. Push the logic into a dedicated abstraction / helper / state machine / policy object / module instead of tangling an existing path.
3. **Clean the design, don't just accept working code.** If behaviour can stay the same while structure gets meaningfully cleaner, prefer the cleaner version. Strongly prefer simplifications that remove moving pieces over refactors that spread the same complexity around.
4. **Direct/boring over magic.** Treat brittle, ad-hoc, or "magic" behaviour as a quality problem. Be skeptical of generic mechanisms hiding simple data-shape assumptions. Flag thin abstractions, identity wrappers, or pass-through helpers that add indirection without buying clarity.
5. **Type & boundary cleanliness.** Question unnecessary optionality, `unknown`/`any`, or cast-heavy code where a clearer type boundary could exist. Prefer explicit typed models / shared contracts over loosely-shaped ad-hoc objects. If a branch relies on a silent fallback to paper over an unclear invariant, flag that the boundary should be explicit.
6. **Canonical-layer ownership.** Flag feature logic leaking into shared paths, or implementation details leaking through APIs. Prefer existing canonical utilities over bespoke one-offs; push code toward the right package/service/module rather than normalizing architectural drift.
7. **Orchestration & atomicity smells.** If independent work is serialized for no good reason, note that it could run in parallel. If related updates can leave state half-applied, push for a more atomic structure. Don't over-index on micro-optimizations — flag avoidable orchestration complexity that makes the implementation brittle.

## What to flag aggressively

A complicated implementation where a cleaner reframing deletes whole categories of complexity; refactors that move code without reducing the concepts a reader must hold; a file crossing ~1000 lines; new conditionals bolted onto unrelated paths; one-off booleans/nullable-modes/flags complicating control flow; feature-specific logic in general-purpose modules; "magic" handling that hides simple structure; thin wrappers / identity abstractions; unnecessary casts / `any` / `unknown` / optional params muddying the contract; copy-pasted logic instead of an extracted helper; bespoke helpers where a canonical one exists; logic in the wrong layer; sequential async where independent work could be parallel; partial-update logic that leaves state less atomic than necessary.

## Preferred remedies (suggest these, don't just name the problem)

Delete a whole layer of indirection rather than polish it; reframe the state model so conditionals disappear; change the ownership boundary so the feature becomes a natural extension of an existing abstraction; turn special-case logic into a simpler default with fewer exceptions; extract a helper / pure function; split a large file into focused modules; replace condition chains with a typed model or explicit dispatcher; separate orchestration from business logic; collapse duplicate branches; delete wrappers that don't clarify the API; reuse the canonical helper; make type boundaries explicit so control flow simplifies; move logic to the package/module that owns the concept; parallelize genuinely independent work; make related updates more atomic.

## Scope — do NOT emit findings for

- Correctness **bugs** — that's `/code-review`'s job, and Tier 1 already gates behaviour. Stay on *quality/maintainability*.
- Style / formatting / word choice / naming / section ordering — not material.
- "Add more tests" as a blanket ask — Tier 1/2 own verification.
- Anything you cannot point to a concrete location for.

## Output (required)

End with a single fenced JSON block, nothing after it, conforming exactly to:

```json
{
  "findings": [
    {
      "severity": "high | med | low",
      "category": "file-size | spaghetti | indirection | type-boundary | layer-leak | orchestration | duplication",
      "location": "<file:line or file>",
      "finding": "<what's wrong, one or two sentences>",
      "remedy": "<the concrete restructuring to do>"
    }
  ]
}
```

Rules:
- `findings: []` is valid (and good) — emit it when the implementation is genuinely clean.
- Every finding needs a concrete `location`. No location → drop it.
- `severity high` = a structural regression or a clear, high-leverage simplification missed; `med` = worth doing; `low` = minor. (Only `high` can block, and only under `--block-on-quality`.)
- Prefer a small number of high-conviction findings over a long list of nits.

END_PROMPT
