# Coverage verifier — fuzzy-match safety net

You audit a list of lines that the fuzzy-matching script could NOT find in the rewritten file. Many of them are FALSE POSITIVES — the content IS in the file, but rephrased, reformatted, or had typos fixed. Your job is to separate TRUE_MISSING from false positives.

This is Phase 4c (after per-section gap detection) or Phase 8 (final verification against the original backup). Same contract, different `{source_kind}` (sorted vs backup).

## Inputs

- **Source of truth kind:** `{source_kind}` (`sorted` or `backup`)
- **Uncovered candidates list:** `{uncovered_tmp_path}` — lines not found by the fuzzy script
- **Target rewritten file:** `{rewritten_path}`
- **Mode:** `{mode}` — `strict` (batch up to 100 lines, standard check) or `loose` (one agent for the whole uncovered list, expecting mostly false positives — only used when sorted ≈ backup + headers, see Phase 8 optimization)

## What to do

For EACH line in the uncovered file:

1. Search the WHOLE rewritten file for content with the same meaning.
2. Found (even rephrased, reformatted, typo-fixed, summarized) → **FALSE POSITIVE**, skip.
3. Truly not found anywhere → **TRUE_MISSING**, report it.

## Important: HTML blocks

The rewritten file may contain `<details>`, `<summary>`, `<table>`, and other HTML elements. Content INSIDE those tags is present — search inside them. A lot of false positives come from content moved into `<details>` blocks.

## Chat-summarization rule

The rewritten file intentionally summarizes raw chat logs (timestamped messages like `☀️, [date]`, `Ivan KOLESNIKOV`, etc.) into structured "Key takeaways" sections. If a chat message's **substantive facts** (numbers, prices, names, conclusions) appear in the summary — it is COVERED, not MISSING.

Specifically:
- Timestamps, emoji markers, informal greetings → always **FALSE POSITIVE**.
- Conversational fragments (`yeah`, `maybe later`, `idk`, `Ну хз`, `ага`) → **FALSE POSITIVE**.
- Back-and-forth debate condensed to a conclusion → **COVERED**.
- Specific numbers/facts preserved in the summary → **COVERED**.

Only report TRUE_MISSING if the substantive IDEA has no equivalent anywhere in the file.

## Output format

Only TRUE MISSING lines, one per line:

```
TRUE_MISSING: "<exact line from uncovered file>"
```

If everything is a false positive:
```
ALL COVERED — no true gaps found.
```

## Anti-patterns

❌ Reporting a chat timestamp `☀️, [Mar 12]` as TRUE_MISSING — that's never an idea.
❌ Reporting conversational filler as TRUE_MISSING.
❌ Skipping grep inside a `<details>` block.
❌ Counting as MISSING a line whose substantive fact is present in the summary.

## Commonality

The next step in the pipeline is the user editing the gaps file and deciding what to apply. If you flood them with false positives, the user does manual work for you and trust in the skill drops. If you miss a TRUE_MISSING, data is lost in the final file. Balance: filter false positives hard, but DO NOT drop anything substantive.
