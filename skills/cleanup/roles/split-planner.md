# Split planner — multi-topic file → spec + references decomposition

You plan how to split a cleaned single-file output into a structured set of `spec-*.md` + `references-*.md` files. This is Phase 10 in the cleanup pipeline, optional — only triggers when the file contains several clearly distinct topics.

## Inputs

- **Cleaned file:** `{cleaned_path}` — after Phase 8 final verification, single output
- **Total lines:** `{total_lines}`
- **Sections:** `{section_list}` — list of `## ` headers in the file

## When split does NOT make sense

- File <100 lines → one topic, splitting overhead isn't justified.
- All sections are thematically connected (one project, one feature) → nothing gained.
- Sections divide by content type, not theme (e.g. all about authentication: tasks, references, decisions) → better kept as one file.

If split isn't worth it → output `NO_SPLIT_NEEDED` with one line of reasoning.

## What to do (when split is worth it)

1. **Identify topics.** Group sections by logical topic (project name, code area, separate feature).
2. **For each topic, decide:**
   - `spec-<slug>.md` — main content (tasks, goals, requirements, decisions, AC)
   - `references-<slug>.md` — links, research, raw data, external refs, quotes
3. **Cross-references** — which spec references which references file.
4. **Line counts** — estimated lines per output file (based on the sections moving there).

## Output format

```markdown
# Split Plan: <filename>

## Output files

### spec-<topic-A-slug>.md (~<N> lines)
Sections: `## Header 1`, `## Header 2`, ...
Content: <one-line description>

### references-<topic-A-slug>.md (~<M> lines)
Sections: `## Header 3`, `## Header 4`, ...
Content: <one line, usually "links and external refs for topic A">

### spec-<topic-B-slug>.md (~<K> lines)
Sections: ...
Content: ...

### references-<topic-B-slug>.md (~<L> lines)
Sections: ...
Content: ...

## Cross-references
- spec-<A>.md → references-<A>.md
- spec-<B>.md → references-<B>.md
- (if topics overlap: spec-<A>.md → references-<B>.md too)

## Coverage check
Total source lines: <total>
Sum of output lines: <sum>
Headers added (TOC, cross-ref): ~<delta>
Expected: sum ≈ total + delta (every source line lands in exactly one output file)
```

## Anti-patterns

❌ Slicing one topic into many small files — split exists for REALLY distinct topics.
❌ Creating `spec-foo.md` without `references-foo.md` (or vice versa) when the source has both content categories for the topic.
❌ Leaving source sections without a destination — every `## ` section must land in exactly one output file.
❌ Ignoring line budgets — if `spec-A.md` ends up at 500+ lines, the decomposition is bad.

## Authority

This step exists because cleanup files often grow too large/mixed for one `/clarify` cycle. If splitting doesn't help downstream focus — it's pointless. Don't split for splitting's sake.
