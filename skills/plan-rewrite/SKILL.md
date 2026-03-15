---
name: plan-rewrite
description: >
  Rewrite and reorganize a plan file: semantic sort, AI rewrite, 100% verified gap detection.
  Use when user asks to clean up, reorganize, rewrite, or sort a plan/todo file.
  Triggers: "перепиши план", "реорганизуй план", "plan-rewrite", "sort plan",
  "очисти план", "rewrite plan", "/plan-rewrite"
allowed-tools: [Bash, Glob, Grep, Read, Edit, Write, Agent]
---

# Plan Rewrite Skill

Reorganize and rewrite a plan file with **100% verified** gap detection.

## Usage

```
/plan-rewrite <file path>
```

## Algorithm

$ARGUMENTS

Arguments: `<file path>`

### Phase 1: Sort

1. **Validate**: If no argument — ask for file path (AskUserQuestion).
2. **Backup**: `cp <file> <file>.bak`
3. **Semantic sort** (AI — you do this directly):
   - Parse sections by `## ` headers.
   - Orphan lines before first header → create a header for them.
   - **Semantic audit**: go through EVERY non-empty line in EVERY section. If a line's topic doesn't match its section — move it to the correct section. If no suitable section exists — create a new one.
   - Insert moved lines before the first `### ` subsection in the target section. Respect code block boundaries (``` ... ```).
   - Collapse consecutive blank lines (max 1).
   - Preserve frontmatter at the top.
   - Preserve every original line exactly as-is — no rewording, no reformatting. You MAY add new `## ` headers for organization, but NEVER delete or rename existing lines. Header cleanup happens in Phase 3.
4. **Write** sorted version to original file path.
   - **Unicode caution**: Write tool может нормализовать Unicode (потерять non-breaking spaces U+00A0 и пр.). Если verify-sort.py показывает missing lines — проверь `repr()` строк на `\xa0` и подобные символы, затем используй Python для byte-for-byte копирования из оригинала.

### Phase 2: Verify Sort

Run the verification script:

```bash
python3 ~/.claude/skills/plan-rewrite/scripts/verify-sort.py <file>.bak <file>
```

- The script checks that ALL original lines are present in sorted (superset check). New lines (added headers) are OK.
- If FAIL (original lines missing) → restore from backup, ABORT, report error.
- If PASS → continue.

### Phase 3: Rewrite

Rewrite the sorted file into a clean, well-structured document. Create `<basename>.rewritten.<ext>`:

- Fix grammar, punctuation, style, typos.
- Remove exact duplicates (same meaning — keep the more detailed version).
- Restructure: add `## ` section summaries, create `### ` subsections where logical.
- Clean up chat artifacts: timestamps (☀️, Ivan KOLESNIKOV), informal fragments → integrate into structured items.
- Rephrase unclear/broken sentences for clarity.
- Convert unstructured notes into actionable items where possible.
- Consolidate related items within the same section.

**Chat log handling:**
- Extract and PRESERVE: specific numbers, prices, URLs, actionable insights, named entities.
- Summarize back-and-forth debate into key positions with attribution.
- If a chat section has >50 lines, create a "Key takeaways" subsection + keep raw data points as bullets.
- NEVER reduce a chat section to <20% of its original line count.

Constraints:
- MUST preserve ALL ideas, tasks, links, URLs, references — every distinct thought must survive.
- DO NOT merge DIFFERENT tasks that seem related but are distinct.
- DO NOT drop informal notes/questions — they may contain important context. Rephrase but keep.
- The gap detection pipeline will catch any losses, so focus on producing a CLEAN readable plan.
- ИЗБЕГАЙ использования `<details>` / `<summary>` HTML-блоков для критического контента. Агенты и скрипты gap detection ищут по raw-тексту и могут пропустить контент внутри HTML-тегов. Если используешь `<details>`, дублируй ключевые факты вне коллапсируемого блока (например, в строке summary над ним).

### Phase 4: Gap Detection (three levels)

#### 4a: Deterministic check (script)

```bash
python3 ~/.claude/skills/plan-rewrite/scripts/verify-rewrite.py <sorted> <rewritten>
```

Extracts and compares URLs (only). Report missing URLs.

#### 4b: Semantic check (pre-filter + background agents) — MANDATORY

> **GATE CHECK**: 4b и 4c — РАЗНЫЕ проверки. ОБЕ обязательны, по порядку.
> - **4b** = посекционное семантическое сравнение → MISSING / PARTIAL / REVERSED
> - **4c** = safety net скрипт fuzzy-match → только TRUE_MISSING
> НЕ пропускай 4b. НЕ подменяй 4b на 4c.

**Шаг 1 — Pre-filter через Grep** (снижает нагрузку на агентов на ~60-80%):

1. Для каждой `## ` секции в sorted файле собери все непустые контентные строки.
2. Для каждой строки извлеки 2-3 уникальных ключевых слова (предпочитай имена собственные, числа, технические термины).
   - **Для строк с URL**: извлеки domain/path как keyword (напр. из `https://t.me/foo/123` → `foo/123`; из `https://github.com/user/repo` → `repo`).
   - **Для строк, содержащих ТОЛЬКО URL**: grep по domain+path фрагменту.
3. `Grep` каждое ключевое слово в rewritten файле.
4. Если ЛЮБОЙ grep находит смысл строки → помечай COVERED, пропускай.
5. Если НИ ОДИН grep не находит → добавляй в список UNFOUND для этой секции.

Пример:
- Sorted строка: `Автоматизация отработки фандингов https://t.me/automaker_main/43`
- Ключевые слова: `фандинг`, `automaker`
- Grep `automaker` в rewritten → найдено на строке 85 → COVERED, пропускаем.

**Шаг 2 — Запуск агентов для секций с ненайденными строками**:

Назначай 1-2 секции (по заголовкам) на агента (только секции, в которых остались unfound строки после Шага 1). Без ограничений на количество агентов.

- `subagent_type`: `Explore`
- `run_in_background`: true

**Agent prompt** (use this for each agent, replacing SECTIONS and FILE_PATHS):

```
You are a gap detector. Compare SORTED file vs REWRITTEN file for these sections: [SECTIONS].

Files:
- Sorted: [SORTED_PATH]
- Rewritten: [REWRITTEN_PATH]

CRITICAL: Use Grep tool to search for key phrases from each sorted line. Do NOT rely on manual reading for large files. For each line, grep 3-5 unique words in the rewritten file.

IMPORTANT: The rewritten file may contain HTML blocks (<details>, <summary>, <table>).
Content inside these tags IS valid — search INSIDE them with Grep. A line found inside
<details>...</details> counts as present.

For EACH non-empty line in your assigned sections of the SORTED file:
1. Search for a semantic equivalent in the REWRITTEN file (search the ENTIRE file, not just the same section)
2. If found with same meaning → SKIP
3. If found but details lost → PARTIAL (quote both lines + what was lost)
4. If meaning changed/reversed → REVERSED (quote both lines)
5. If NOT found anywhere → MISSING (quote the sorted line)

RULES:
- Grammar/formatting changes are NOT gaps. "setup nginx" → "Set up Nginx" is fine.
- PARTIAL only when a SPECIFIC IDEA, DETAIL, or CONTEXT is lost — not formatting.
- These are NOT gaps: bullet→checkbox, case changes, typo fixes, punctuation, link text changes.
- If the core idea and all details are preserved, it's a SKIP regardless of formatting.
- You MUST quote exact text from both files. If you cannot quote the rewritten equivalent — it IS missing.
- Output format per finding:
  SECTION: <header>
  TYPE: MISSING|PARTIAL|REVERSED
  SORTED_LINE: "<exact quote>"
  REWRITTEN_LINE: "<exact quote or NOT_FOUND>"
  LOST_DETAIL: "<what was lost>" (PARTIAL only)
```

**4b завершена когда**: Все секционные агенты вернули результаты. Теперь переходи к 4c.

#### 4c: Coverage safety net (script + agent verification)

**Step 1**: Run the coverage script:
```bash
python3 ~/.claude/skills/plan-rewrite/scripts/verify-coverage.py <sorted> <rewritten> <gaps>
```

The script checks every sorted line against rewritten (fuzzy match) and gaps. Lines not found → written to `<basename>.uncovered.tmp`.

**Step 2**: If uncovered candidates exist, split into batches of 100 lines. Spawn one agent per batch in parallel. **No limit on agent count** — use as many as needed. NEVER skip this step.

- `subagent_type`: `Explore`
- Each agent reads its batch from `.uncovered.tmp`, plus the rewritten file
- For each candidate, the agent determines: is this truly missing from rewritten, or just rephrased/reformatted?

**Agent prompt**:
```
You are a coverage verifier. You have a list of lines that a fuzzy-matching script
could not find in the rewritten file. Many of these are FALSE POSITIVES — the content
IS in the rewritten file but was rephrased, reformatted, or had typos fixed.

IMPORTANT: The rewritten file may use <details><summary>...</summary>...</details> blocks.
Content inside these blocks IS present — search the raw file text, not rendered output.
Many false positives come from content moved into <details> blocks.

CHAT SUMMARIZATION RULE: The rewritten file intentionally summarizes raw chat logs
(timestamped messages like "☀️, [date]") into structured "Key takeaways" sections.
If a chat message's substantive facts (numbers, prices, names, conclusions) appear
in summarized form — it is COVERED, not MISSING. Specifically:
- Timestamps, emoji markers, informal greetings → always FALSE POSITIVE
- Conversational fragments ("Ну хз", "Ага", "Потом конечная") → FALSE POSITIVE
- Back-and-forth debate condensed to conclusion → COVERED
- Specific numbers/facts preserved in summary → COVERED
Only report TRUE_MISSING if the substantive IDEA has no equivalent anywhere in the file.

Files:
- Uncovered candidates: [UNCOVERED_TMP_PATH]
- Rewritten: [REWRITTEN_PATH]

For EACH line in the uncovered file:
1. Search the ENTIRE rewritten file for content with the same meaning
2. If found (even rephrased, reformatted, typo-fixed, summarized) → FALSE POSITIVE, skip it
3. If truly NOT found anywhere → TRUE MISSING, report it

Output ONLY the TRUE MISSING lines, one per line, with format:
TRUE_MISSING: "<exact line from uncovered file>"

If all lines are false positives, output: "ALL COVERED — no true gaps found."
```

**Step 3**: Only TRUE MISSING lines from the agent get added to the gaps file as `[UNCOVERED]`. Delete the `.uncovered.tmp` file.

### Phase 5: Gaps File

1. Wait for all background agents to complete.
2. Merge results from script (4a) + agents (4b).
3. Write initial `<basename>.gaps.md`.
4. Run coverage check (4c) — script finds candidates, agent verifies, only true gaps added.
5. Delete `.uncovered.tmp`.
6. Deduplicate.

**Gaps file format:**

```markdown
# Gaps: <filename>
<!-- Delete lines you don't need. Keep lines to apply to rewritten. -->
<!-- Summary: N MISSING, M PARTIAL, K REVERSED, L UNCOVERED -->

## <Section Name>

- [MISSING] `<exact sorted line>`
- [PARTIAL] `<sorted line>` → rewritten: `<rewritten line>` | Lost: <detail>
- [REVERSED] `<sorted line>` → rewritten: `<rewritten line>`
- [UNCOVERED] `<sorted line>`
```

### Phase 6: PAUSE

Output a report:

```
=== PLAN-REWRITE COMPLETE (Phases 1-5) ===

Files:
  Backup:    <path>.bak          (<N> lines)
  Sorted:    <path>              (<N> lines, verified)
  Rewritten: <path>.rewritten    (<N> lines)
  Gaps:      <path>.gaps.md      (<N> items: X missing, Y partial, Z reversed, W uncovered)

Next: edit .gaps.md, delete what you don't need. Write me when you're ready to continue. 
```

**STOP. Do not continue until the user indicates they are ready.**

### Phase 7: Apply

When the user indicates they are ready:

1. Read the edited gaps file.
2. For each remaining item:
   - `[MISSING]` / `[UNCOVERED]` → insert the original line into the appropriate section in rewritten.
   - `[PARTIAL]` → augment the rewritten line with the lost detail.
   - `[REVERSED]` → fix the meaning in rewritten.
3. Delete the gaps file.
4. Output: "Applied N items. Final: <path>.rewritten (<N> lines)"

### Phase 8: Final Verification

Verify the final rewritten file against the original backup:

```bash
# All URLs from original present in final?
python3 ~/.claude/skills/plan-rewrite/scripts/verify-rewrite.py <file>.bak <basename>.rewritten.<ext>

# Every original line covered in final?
python3 ~/.claude/skills/plan-rewrite/scripts/verify-coverage.py <file>.bak <basename>.rewritten.<ext> /dev/null
```

- If uncovered candidates found → **MANDATORY**: spawn NEW agents (batches of 100).
  Do NOT reuse Phase 4c results — Phase 4c compared **sorted → rewritten**,
  Phase 8 compares **backup (original) → rewritten**. Different source = different gaps.
  **Optimization**: Если Phase 4c не выявила TRUE_MISSING items, И sorted файл
  отличается от backup только добавленными `## ` headers (что проверено в Phase 2),
  то допустимо запустить 1 агент на ВЕСЬ список uncovered (вместо батчей по 100),
  с инструкцией "expect mostly false positives, report only truly unique content".
  Use this prompt:
  ```
  You are a final coverage verifier. Lines from the ORIGINAL BACKUP were not fuzzy-matched
  in the FINAL rewritten file. Many are FALSE POSITIVES (rephrased, reformatted, reorganized).

  IMPORTANT: The rewritten file may contain <details>, <summary> and other HTML elements.
  Content inside these tags IS present — search inside them.

  CHAT SUMMARIZATION RULE: The rewritten file intentionally summarizes raw chat logs
  (timestamped messages like "☀️, [date]") into structured "Key takeaways" sections.
  If a chat message's substantive facts (numbers, prices, names, conclusions) appear
  in summarized form — it is COVERED, not MISSING. Specifically:
  - Timestamps, emoji markers, informal greetings → always FALSE POSITIVE
  - Conversational fragments → FALSE POSITIVE
  - Back-and-forth debate condensed to conclusion → COVERED
  - Specific numbers/facts preserved in summary → COVERED
  Only report TRUE_MISSING if the substantive IDEA has no equivalent anywhere.

  Files:
  - Uncovered candidates: [UNCOVERED_TMP_PATH]
  - Final rewritten: [REWRITTEN_PATH]

  For EACH line:
  1. Search ENTIRE rewritten file for same meaning
  2. Found (even rephrased, inside <details>, summarized) → FALSE POSITIVE, skip
  3. Truly not found → TRUE MISSING

  Output: TRUE_MISSING: "<exact line>" or "ALL COVERED — no true gaps found."
  ```
- If TRUE MISSING found → report them, DO NOT delete backup.
- If all clear → "✅ Final verification passed. Safe to delete backup."

### Phase 9: Report

Output a final report:

```
=== PLAN-REWRITE REPORT ===

Metrics:
  Original:  <N> lines
  Rewritten: <N> lines (<ratio>% compression)
  Gaps found: <N> (X applied, Y dismissed by user)
  URLs: <N> original, <M> preserved, <K> missing (user-approved)

Issues encountered:
- <any verification failures, skipped steps, agent errors, or anomalies>

Fixes (brief, only if issues found):
- <concrete action to resolve each issue, e.g. "Re-run Phase 4c with batch size 30" or "Add missing URL X to section Y">

Recommendations:
- <suggestions for the file or future rewrites>
```

## Scaling

The skill must handle files of any size. Scale resources proportionally:
- Phase 4b (semantic check): 1 agent per 1-2 sections. No limit on agent count.
- Phase 4c (coverage): batch uncovered into groups of 100. 1 agent per batch. No limit.
- Phase 8 (final): same scaling as Phase 4c (or 1 agent if Phase 4c was clean — see optimization).
Never skip a verification step due to file size or token cost.

## Rules

- Act immediately — no confirmation needed (except Phase 6 pause).
- Match the user's language in all output.
- If any phase fails — report the error, restore from backup if needed, and stop.

## Scripts

All scripts are in `~/.claude/skills/plan-rewrite/scripts/`:

| Script | Purpose | Args |
|--------|---------|------|
| `verify-sort.py` | Superset check — all original lines preserved, new lines OK | `<backup> <sorted>` |
| `verify-rewrite.py` | URL presence check (with normalization) | `<source> <target>` |
| `verify-coverage.py` | Safety net — every line accounted for | `<sorted> <rewritten> <gaps>` |
