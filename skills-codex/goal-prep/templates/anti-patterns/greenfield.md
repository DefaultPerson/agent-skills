# Anti-patterns: greenfield / new product

Layered on top of `base.md` when `/goal-prep` classifies the goal as greenfield.

- Do not commit to a heavy ORM / framework before milestone 2. Build core logic as plain functions taking plain data first.
- Do not write README/docs before milestone 2 — document what actually survived milestone 1.
- Do not ignore the listed `reference_projects` for visual or interaction language. Pull from them; do not invent from scratch.
- Define `who_is_NOT_user` explicitly. If you cannot name a persona you are deliberately excluding, the user definition is too broad.
- Enumerate `creative_freedom_areas` (e.g. color palette, route shapes, copy tone). Anything not enumerated is a hard constraint, not free.
- Do not add features for hypothetical edge cases. Add when the first real failure is observed.
- Tests at the boundary only until milestone 2. Internal helpers are likely to change shape.
- Milestone = vertical slice the user can exercise end-to-end. A milestone that requires another milestone to be useful is not a milestone.
