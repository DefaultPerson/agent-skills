# Anti-patterns: bug-hunt / QA

Layered on top of `base.md` when `/goal-prep` classifies the goal as QA.

- Hunt-before-fix discipline: log issues; do not fix them in the same task.
- Do not log duplicates — read existing `issues.md` (or prior notes/) before adding.
- Do not investigate root cause beyond the "proposed fix" paragraph in the issue record.
- Do not log nitpicks below the agreed severity threshold (default: P3+).
- Every issue must include: repro steps, expected, actual, proposed_fix, evidence (screenshot path / log excerpt / file pointer).
- Do not pause the hunt to refactor unrelated code. Track refactor candidates separately for a future `/goal-prep refactor` run.
- Stop the hunt at `stop_after_N_issues`; do not silently keep going past the agreed count.
