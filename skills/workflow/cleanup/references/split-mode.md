# Split mode (Phase 10-12) — optional decomposition into spec + references

After step 9 (Report), offer to split the cleaned file into structured `spec-*.md` + `references-*.md` files. Not always needed — only when the file contains multiple distinct topics.

## When to offer split

After step 9 report, ask the user:

> The file mixes several topics (`<list>`). Split into separate spec + references files? (yes / no)

Don't auto-trigger. Don't push.

## Phase 10 — Split analysis (plan mode)

1. **Quick check:** if total lines <100 OR the sections feel like one tight topic → output `NO_SPLIT_NEEDED`, suggest the user just run their next step manually.
2. **If multiple distinct topics:** enter plan mode (`EnterPlanMode`) and invoke a Plan agent or your own planning using the prompt from `roles/split-planner.md`. Substitutions: `{cleaned_path}`, `{total_lines}`, `{section_list}`.
3. **Output** is a split-plan markdown with the list of output files, sections going into each, cross-references, and line counts.
4. **ExitPlanMode** — the user reviews. If they reject → ask what to change, revise.

## Phase 11 — Execute split

1. Create the output directory: `<basename>/` (sibling to the input file).
2. For each output file from the plan:
   - `spec-<topic-slug>.md` — main content (tasks, goals, requirements, decisions, AC)
   - `references-<topic-slug>.md` — links, research notes, external refs, raw data
3. Add cross-references at the top of each spec:

   ```markdown
   > References: [references-<topic>.md](references-<topic>.md)
   ```

4. **Preserve every source line.** Each `## ` section from the cleaned file lands in exactly one output file. No line dropped, no line duplicated.

## Phase 12 — Verify split

```bash
python3 scripts/verify-split.py <cleaned-file> <output-dir>
```

The script concatenates every `.md` file in the output directory and checks that every line from the cleaned file is present (fuzzy match). New lines (TOC headers, cross-references) are OK.

- If FAIL → report uncovered lines. Don't delete the cleaned file.
- If PASS → split is complete.

## Handoff after split

```
=== SPLIT COMPLETE ===

Files:
  <list of created files with line counts>

Recommend: /clear before continuing work.
```

Stay standalone — don't suggest `/clarify` or any other downstream skill. The user picks the next step.
