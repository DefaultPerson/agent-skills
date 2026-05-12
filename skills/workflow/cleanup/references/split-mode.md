# Split mode (Phase 10-12) — optional decomposition into spec + references

After Phase 9 (Report), offer to split the cleaned file into structured `spec-*.md` + `references-*.md` files. Not always needed — only when the file contains multiple distinct topics.

## When to offer split

After Phase 9 report, ask the user:

> Файл объединяет несколько тем (`<list>`). Разбить на отдельные spec + references файлы? (yes / no)

Don't auto-trigger. Don't push.

## Phase 10 — Split analysis (plan mode)

1. **Quick check:** if total lines <100 OR sections feel like one tight topic → output `NO_SPLIT_NEEDED`, suggest user just run their next step manually.
2. **If multiple distinct topics:** enter plan mode (`EnterPlanMode`) and invoke a Plan agent or your own planning with the prompt from `roles/split-planner.md`. Substitutions: `{cleaned_path}`, `{total_lines}`, `{section_list}`.
3. **Output** is a split plan markdown with list of output files, sections going into each, cross-references, line counts.
4. **ExitPlanMode** — user reviews. If they reject → ask what to change, revise.

## Phase 11 — Execute split

1. Create output directory: `<basename>/` (sibling to input file).
2. For each output file from the plan:
   - `spec-<topic-slug>.md` — main content (tasks, goals, requirements, decisions, AC)
   - `references-<topic-slug>.md` — links, research notes, external refs, raw data
3. Add cross-references at top of each spec:

   ```markdown
   > References: [references-<topic>.md](references-<topic>.md)
   ```

4. **Preserve every source line.** Each `## ` section from cleaned file lands in exactly one output file. No line dropped, no line duplicated.

## Phase 12 — Verify split

```bash
python3 scripts/verify-split.py <cleaned-file> <output-dir>
```

The script concatenates all `.md` files in output dir and checks that every line from the cleaned file is present (fuzzy match). New lines (TOC headers, cross-references) are OK.

- If FAIL → report uncovered lines. Don't delete the cleaned file.
- If PASS → split is complete.

## Handoff after split

```
=== SPLIT COMPLETE ===

Files:
  <list of created files with line counts>

Recommend: /clear before continuing work.
```

Stay standalone — don't suggest `/clarify` or any other downstream skill. User decides next step.
