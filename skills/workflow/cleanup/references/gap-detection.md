# Gap detection (Phase 4) — design rationale and detailed mechanics

Three-level gap detection — deterministic, semantic, fuzzy. All three are mandatory in order. Each catches a different class of misses; substituting one for another loses coverage.

## Why three levels

- **4a (script, URL-only):** deterministic. If a URL string disappeared in rewrite — that's data loss, no judgment needed. Cheap, fast, catches the most common preservable signal.
- **4b (per-section semantic agents):** catches idea-level loss the script can't see. URL preserved but its description rephrased away? Number dropped? Reversal? Agent reads both sides and judges.
- **4c (fuzzy coverage net):** catches what 4b missed because 4b only checks sections it was assigned, AND agents can hallucinate "found" matches. 4c does brute-force fuzzy match on every line, then spawns agents to verify the candidates.

Skipping 4b and relying on 4c alone → loses PARTIAL/REVERSED detection (4c only outputs TRUE_MISSING).

Skipping 4c and trusting 4b alone → 4b assigns sections to different agents; if a line moved cross-section in rewrite, the section-restricted agent might miss it.

## Phase 4a — script, URLs only

```bash
python3 scripts/verify-rewrite.py <sorted> <rewritten>
```

Extracts URLs (with normalization for trailing slashes, query params, http/https equivalence) from both files. Reports URLs present in sorted but absent in rewritten.

Output: list of missing URLs → goes into gaps file as `[MISSING]` items.

## Phase 4b — per-section semantic agents

**Small-file optimization:** if sorted file has <50 non-empty content lines AND single-file input → skip 4b. Rely on 4c + small-batch agent verification. In **multi-file mode**, this skip does NOT apply per-source — run 4b regardless of per-source size, because multi-file gap classes (PARTIAL/REVERSED across boundaries) are exactly what 4b catches.

**Step 1 — Pre-filter via Grep (reduces agent load by ~60-80%):**

1. For each `## ` section in sorted, collect non-empty content lines.
2. For each line, extract 2-3 unique keywords (prefer proper nouns, numbers, technical terms, domain fragments from URLs).
3. Grep each keyword in rewritten.
4. If ANY grep finds the line's meaning → COVERED, skip.
5. If NO grep finds it → add to UNFOUND list for that section.

**Step 2 — Spawn agents** (1-2 sections per agent) using `roles/gap-detector.md` template. Substitutions: `{sorted_path}`, `{rewritten_path}`, `{sections}` (list).

Subagent type: `Explore`. Run in background. No limit on agent count.

**Step 3 — Collect results.** Wait for all agents. Merge their findings into `<basename>.gaps.md` as `[MISSING]`/`[PARTIAL]`/`[REVERSED]` items.

## Phase 4c — fuzzy coverage net

**Step 1 — Script:**

```bash
python3 scripts/verify-coverage.py <sorted> <rewritten> <gaps>
```

Fuzzy-matches every sorted line against rewritten AND against gaps file. Lines not found → written to `<basename>.uncovered.tmp`.

**Step 2 — Agent verification.** If `.uncovered.tmp` is non-empty, split into batches of 100 lines. Spawn one agent per batch in parallel using `roles/coverage-verifier.md`. Substitutions: `{uncovered_tmp_path}`, `{rewritten_path}`, `{source_kind} = "sorted"`, `{mode} = "strict"`.

**Step 3 — Merge.** Only TRUE_MISSING lines from agents get added to gaps file as `[UNCOVERED]` items. Delete `.uncovered.tmp`.

## Multi-file mode adjustments

When cleanup runs on N source files (Phase 0 created `sources = [file1, file2, ...]`):

- Phase 4a/4b/4c run **per source** — each source has its own sorted, rewritten, gaps file, .uncovered.tmp.
- 4b agent count: minimum 1 agent per source, regardless of section count per source.
- 4b grep step (Step 1): keyword search scoped to the source's sorted file only, NOT the merged file (prevents cross-source keyword fluke-matches that mask real gaps).
- 4c uncovered batching is per-source.
- Final gaps file is per-source: `<source>.gaps.md`.

This is the core fix for multi-file laziness — without per-source scoping, keywords from file2 fluke-match in file1's grep, suppressing real gap detection.

## Phase 8 — final verification against original backup

After user applies gaps (Phase 7), run final coverage check against the ORIGINAL backup (not the sorted intermediate):

```bash
python3 scripts/verify-coverage.py <file>.bak <basename>.rewritten.<ext> /dev/null
```

If uncovered candidates exist → spawn agent(s) using `roles/coverage-verifier.md`. Substitutions: `{source_kind} = "backup"`, `{mode}` depends:
- If Phase 4c found 0 TRUE_MISSING items AND sorted differs from backup only by added `## ` headers → `{mode} = "loose"`, single agent on whole uncovered list, expect mostly false positives.
- Otherwise → `{mode} = "strict"`, batches of 100 like Phase 4c.

Different source (backup vs sorted) = different gaps surface. Don't reuse Phase 4c results.
