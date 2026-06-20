# Anti-patterns: refactor / behavior preservation

Layered on top of `base.md` when `/goal-prep` classifies the goal as refactor.

- Do not extract an abstraction for 2 call sites — wait for the 3rd. If the 3rd has a different shape, the abstraction was wrong.
- Do not rename symbols across module boundaries in a single commit; split per-module.
- Do not mix refactor with bug fix. If you find a bug, log it to `bugs-found.md` and continue the refactor.
- Do not touch test files unless they are explicitly inside `scope_globs`.
- Behavior preservation is binding: run the agreed test/baseline command before and after the refactor; the output diff must be empty (or in the allowed-diff list). Non-empty diff = revert that commit.
- Do not delete code marked "// kept for compatibility" without explicit user approval.
- Do not introduce new dependencies during a refactor.
