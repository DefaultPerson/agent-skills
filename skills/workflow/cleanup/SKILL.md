---
name: cleanup
description: >
  Use when you have a messy notes/plan/chat dump (50+ lines, mixed topics,
  no clear structure) that needs lossless reorganization into a clean
  sectioned markdown file. Slow and thorough — overkill for files under
  30 lines or already-sectioned docs. Triggers: "cleanup", "/cleanup",
  "почисти", "реорганизуй", "clean up", "rewrite plan", "sort plan",
  "plan-rewrite", "/plan-rewrite".
when_to_use: >
  The input is unstructured (chat exports, dumped notes, brainstorm), >50
  lines, and the user wants the content cleaned without losing ideas. Works
  on multiple input files — produces one cleaned output per input, NOT one
  merged file. Do NOT use for already-structured docs, files under 30 lines,
  or when the user wants summarization (cleanup preserves everything; it
  doesn't compress ideas).
allowed-tools: [Bash, Glob, Grep, Read, Edit, Write, Agent, EnterPlanMode, ExitPlanMode, AskUserQuestion]
---

# Cleanup

Losslessly reorganize a messy notes/plan/chat dump into a clean sectioned markdown file, with three-level gap detection to prove nothing was lost.

> **Letter = spirit.** If a rule blocks you from reaching the goal it was
> written for, the rule is wrong, not the goal. Don't look for a wording
> loophole — ask what the rule is protecting, and protect that.

## Usage

```
/cleanup <file> [file2] [file3] ...
```

Multi-file: each input is processed independently end-to-end. Output is N cleaned files, NOT one merged file. (Opt-in `--merge` flag preserves legacy single-output behavior for back-compat.)

## Weaknesses and when NOT to use

- **Slow and thorough — overkill for short files.** If the file is already structured with `## ` sections and shorter than 30 lines, manual editing is faster.
- **Context cost grows linearly with input size.** Phase 4 (gap detection) spawns background agents on large files — watch your budget. For files >2000 lines, consider splitting the input.
- **Does not work with non-markdown formats.** JSON/YAML/code dumps — use a different tool.
- **Does not extract content from links** (YouTube, Telegram). For that, run `/extract` before `/cleanup`.
- **Does not summarize.** This skill is preservation-first; if you want to shrink ideas, use a different tool (e.g. `mattpocock:to-prd` for PRD-style summarization).

## How to do it wrong vs right

### Multi-file input

❌ **Wrong:** 3 input files → concatenate into one merged file with `<!-- from: X -->` markers, run the pipeline on the merged file → one output.
- Source provenance is lost after Phase 0.
- Phase 4b keyword grep finds a keyword from file2 inside file1 → false COVERED, real gap masked.
- The `<50-line skip` triggers on merged size even when per-source files are trivially small or huge independently.

✅ **Right:** 3 files → 3 independent Phase 1-8 pipelines → 3 cleaned outputs. Per-source backup, per-source gap detection, per-source verify. The final report aggregates metrics.
- Provenance preserved end-to-end.
- 4b is scoped to the real section of a real source.
- Optional `--merge` flag for users who relied on merged output.

### Phase 4 gap-detection rigor

❌ **Wrong:** File under 50 lines — skip Phase 4b entirely, trust 4c fuzzy-match alone.
- 4c only emits TRUE_MISSING. PARTIAL and REVERSED are not caught.
- In multi-file mode, if every source is under 50 lines, all three checks effectively degrade.

✅ **Right:** Skip 4b only in single-file mode with <50 lines. In multi-file mode, 4b ALWAYS runs, minimum 1 agent per source. Per-source keyword grep is strictly scoped to the source's own line range.

### Standalone framing

❌ **Wrong:** Phase 9 report ends with `Recommend: /clear then /clarify <file>`. That's a presupposition — the user might be going to `mattpocock:tdd`, to a goal feature, or nowhere at all.

✅ **Right:** End with one line: `Cleanup done. Run /clear before continuing.` Don't recommend downstream skills. The user decides what's next.

## Roles

The skill spawns subagents in Phase 4 and Phase 10. Prompt templates:

- `roles/gap-detector.md` — Phase 4b semantic compare per section
- `roles/coverage-verifier.md` — Phase 4c and Phase 8 fuzzy-match verification
- `roles/split-planner.md` — Phase 10 split plan (optional)

Substitutions:

| Variable | Source |
|---|---|
| `{sorted_path}`, `{rewritten_path}` | Phase 1-3 output |
| `{sections}` | per-agent assignment (1-2 sections) |
| `{uncovered_tmp_path}` | Phase 4c/8 script output |
| `{source_kind}` | `sorted` (4c) / `backup` (8) |
| `{mode}` | `strict` (default, batches of 100) / `loose` (Phase 8 optimization) |
| `{cleaned_path}`, `{total_lines}`, `{section_list}` | Phase 10 input |

Spawn: `Agent(subagent_type="Explore", run_in_background=true, prompt=substitute("roles/<role>.md", vars))`.

## What the skill does (step by step)

Each input file goes through these steps independently. Multi-file means N parallel pipelines.

1. **Understand the input.** Single or multi-file. Validate it's markdown. Backup every source (`<file>.bak`).
2. **Sort sections.** Semantic sort: parse `## ` sections, move misplaced lines to the correct sections WITHOUT rewriting. Preserve every original line byte-for-byte. (Unicode caveat: the Write tool may normalize non-breaking spaces — if `verify-sort` fails, use Python for a byte-level copy.)
3. **Verify sort.** `python3 scripts/verify-sort.py <bak> <sorted>` — superset check. FAIL → restore and abort.
4. **Rewrite cleanly.** Fix grammar, dedupe exact copies, restructure with `### ` subsections, clean chat artifacts (timestamps, emoji) into "Key takeaways" blocks. Preserve every IDEA. Output: `<basename>.rewritten.<ext>`. Do not use `<details>`/`<summary>` for critical content (gap detection can see inside, but less reliably).
5. **Find what was lost.** Three-level gap detection — details in `references/gap-detection.md`. Short version: 4a script (URLs only) + 4b per-section semantic agents + 4c fuzzy coverage net. All three are mandatory and ordered. Output: `<basename>.gaps.md`.
6. **Pause — show gaps to the user.** Emit a report, wait for the "ready" signal. If `gaps_count == 0` → skip the wait and jump straight to step 8.
7. **Apply decisions.** Read the edited gaps file. `[MISSING]`/`[UNCOVERED]` → insert. `[PARTIAL]` → augment. `[REVERSED]` → fix. Delete the gaps file.
8. **Final compare against the original.** `python3 scripts/verify-coverage.py <bak> <basename>.rewritten.<ext> /dev/null` against the ORIGINAL backup, not sorted (different surfaces). Uncovered → spawn coverage-verifier agents (see `references/gap-detection.md` for strict vs loose mode). If everything is clean → `mv <basename>.rewritten <file>`, the original is replaced, `.bak` remains.
9. **Report.** Per-source metrics plus aggregate. Multi-file: list every cleaned output.
10. **Optional: split.** If a single output is >100 lines AND contains multiple distinct topics — offer to split into `spec-<slug>.md` + `references-<slug>.md`. See `references/split-mode.md` (Phase 10-12 detail).

Process details — in `references/gap-detection.md` and `references/split-mode.md`. Subagent prompts — in `roles/`.

## Outputs

Per source (multi-file → multiply by N):
- `<source>.bak` — untouched copy of the original
- `<source>` — final sorted + rewritten + gap-applied (the original is overwritten after step 8)
- `<source>.gaps.md` — exists only while gaps remain, deleted after step 7/8
- Optional (if split ran): `<basename>/spec-*.md`, `<basename>/references-*.md`

Git: two commits per source — `pre-cleanup: <name>` (snapshot) and `cleanup: rewrite <name>` (after step 9).

## Connections to other skills

- **Input:** typically a raw file from notes/chat. Can be invoked standalone, or after `/extract` if the notes contain URLs.
- **Output:** valid sectioned markdown without unresolved markers. What to do with it is the user's call (manual edit, `/clarify`, `mattpocock:to-prd`, direct goal-feature input, etc.).
- **Does not call** other skills automatically. After step 9: `Cleanup done. Run /clear before continuing.` — no downstream recommendation.

## Rules

### Commonality
The pipeline is preservation-first because the next steps (clarify, manual edit, mattpocock) assume nothing was lost. If you let a dropped idea pass through Phase 4 as "probably unimportant", the next step works from a holey map. That is not "helping faster" — it is breaking the shared work.

### Prior commitment
In step 3 (verify sort) you committed to running the superset check. In step 5 — all three gap-detection levels. In step 8 — the final compare against backup. Skipping any step withdraws the basis for the final verdict. Not "optimization" — contract violation.

### Authority (multi-file)
Multi-file mode was split into N independent pipelines specifically because merged concatenation lost provenance and masked gaps. If you concatenate "for simplicity" in multi-file mode, you are reintroducing the bug this skill was rewritten to fix.

## Self-check before delivering the result

Would this document pass review by a senior engineer who has to build the system from it? Concretely:

- Every `## ` section in the right place; no fragments "stuck in the wrong place"?
- No `[MISSING]`/`[PARTIAL]`/`[REVERSED]`/`[UNCOVERED]` markers left?
- In multi-file mode — N output files, not one merged?
- `verify-coverage.py` against backup passed with TRUE_MISSING = 0?
- Backup files (`.bak`) in place — there's a path to roll back?

If "no" on any item — redo, don't ship.
