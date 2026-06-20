# Intake Compiler

The Intake Compiler is **silent** machinery inside `/goal-prep`. It
translates raw user input into a structured intake the rest of the skill
uses to shape the first board.

Adapted from `tolibear/goalbuddy` `$goal-prep` Intake Compiler.

## Privacy

Do **not** dump the intake to the user. The user sees the goal.md and the
diagnostic ladder questions, not the 11-field internal record.

## The 11 fields

For every `/goal-prep` invocation, extract:

1. **original_request** — the shortest faithful copy of the user's wording.
   Preserve user-provided plan details verbatim if present.

2. **interpreted_outcome** — one-sentence statement of what must become true.
   This is your interpretation; the user sees it back in the first
   diagnostic ladder question for confirmation.

3. **input_shape** — `vague | specific | existing_plan | recovery | audit`.

   - `vague`: "improve auth", "make it faster", "fix issues".
   - `specific`: "find 5 P1 bugs in checkout before May 13", "add OAuth2
     login button to /signin".
   - `existing_plan`: user provided a plan / spec / checklist / file path
     to a plan.
   - `recovery`: user wants to fix a broken/failing/red state.
   - `audit`: user wants a read-only review (no execution implied).

4. **audience** — who consumes the result. PR reviewer? End-user? CI? You
   tomorrow? Default: "unknown".

5. **authority** — `requested | approved | inferred | needs_approval | blocked`.

   - `requested`: user asked but hasn't confirmed authority for destructive
     actions.
   - `approved`: user has authority and is approving execution.
   - `inferred`: small local task; authority assumed.
   - `needs_approval`: external approval required (e.g. production, money).
   - `blocked`: cannot proceed without authority resolution.

6. **proof_type** — `test | demo | artifact | metric | review | source_backed_answer | decision`.

   What kind of evidence proves the outcome?

7. **completion_proof** — the observable signal that the *full* original
   outcome is complete. Not the slice; the whole goal.

8. **likely_misfire** — the closest "succeeds at the wrong thing" failure.
   How could `/goal` look done while actually missing the user's intent?
   Examples:

   - User wants "fix flaky tests" → misfire: model fixes them by deleting
     the assertions.
   - User wants "improve performance" → misfire: model optimizes the wrong
     code path.

9. **blind_spots_considered** — risks, unstated choices, or success
   dimensions the user may not have named yet. List 2-3.

10. **existing_plan_facts** — verbatim user-provided steps, files,
    constraints, sequencing. Preserve verbatim for the user to validate during the diagnostic ladder.

11. **non_goals** — explicit exclusions ("don't touch billing", "no schema
    changes"). If the user didn't name any, leave empty; the diagnostic
    ladder Q3 will surface them.

## Process

1. Read the raw `$ARGUMENTS` to `/goal-prep`.
2. Classify `input_shape` based on signals listed above.
3. Extract verbatim text for `original_request` and `existing_plan_facts`.
4. **Interpret** to derive `interpreted_outcome` and `likely_misfire`. These
   are model inferences — they should be falsifiable, so the user can correct
   them in the ladder.
5. Default `audience` and `authority` to safe values; the ladder will
   confirm or override.
6. Write all 11 fields into `goal.md ## Intake Summary` and also surface
   them in the preamble block at Phase 9 exit (so they enter conversation
   context where native /goal's evaluator can see them).

## Use in subsequent phases

- **Diagnostic ladder Q1** reads `interpreted_outcome` back to the user
  for confirmation.
- **Classify** uses `input_shape`.
- **Anti-patterns seed** uses keyword match in `interpreted_outcome`.
- **Adversarial Review block** (in goal.md and preamble) references
  `likely_misfire` so the main model under native /goal remembers what
  failure mode to watch for.

## What this is NOT

- Not an open-ended interview. It's deterministic field extraction.
- Not a chance to start work. Reading implementation files to "better
  understand" violates the invocation boundary.
- Not user-facing prose. Keep the intake terse; goal.md is what the user
  reads.
