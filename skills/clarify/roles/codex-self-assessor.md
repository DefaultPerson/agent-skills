# Codex self-assessor — categorize the Claude critique

You are Codex in a fresh `codex exec` invocation without the orchestrator's context. Your job is to categorize each issue from the Claude critique: ACCEPT, REJECT_PETTY, NEEDS_USER.

This is Phase 7.6 in the **Codex variant** of the clarify pipeline. Claude (the cross-model reviewer) has finished its review and emitted findings as JSON. The orchestrator (the Codex host running `/clarify`) now needs to decide what to apply and what to reject. The decision is NOT made by the orchestrator itself (same-process bias risk) — it's made by you, in a clean `codex exec` context.

This file mirrors `claude-self-assessor.md` for the symmetric Codex variant. The Claude variant uses `claude -p` as self-assessor when Codex is reviewer; the Codex variant uses `codex exec` as self-assessor when Claude is reviewer.

## Inputs

- **Spec file:** `{spec_path}` (path on disk — read it)
- **Claude critique:** appended to this prompt as JSON below the marker line `Claude findings:` (the orchestrator pipes it via stdin — there is NO critique file on disk)
- **Round:** `{round}`

## What to do

Read the spec from disk. Read the Claude findings JSON from the prompt body. For every issue in the findings array:

1. **Substantive issue?** If the problem is real (e.g. AC without proof command, missing edge case, inconsistent dependency) → **ACCEPT**.
2. **Style/petty issue?** If Claude is complaining about style, formatting, word choice, section ordering, or markdown syntax → **REJECT_PETTY** (with reasoning).
3. **User-intent issue?** If Claude proposes changing/removing a requirement the user clearly stated, or type = NEEDS_USER → **NEEDS_USER** (flag for user-prompt).

## Categorization in detail

### ACCEPT

- Missing AC, unverifiable proof command, missing edge case → fix is mechanical.
- Coverage gap (Overview item without a task) → need to add a task.
- Contradiction between FR-N and FR-M → needs resolution (possibly via NEEDS_USER if both are intended).
- Ambiguous task description → needs tightening.

### REJECT_PETTY

- "Rename variable X to Y" — style.
- "Section ordering should be reversed" — style.
- "Use more formal language" — style.
- "Add a header to section X" — formatting.
- "Word X is redundant with word Y" — wording.

### NEEDS_USER

- Claude proposes removing a requirement the user intentionally added.
- Claude flags a requirement as "unusual" without it being obviously wrong.
- Claude found a true contradiction whose resolution requires a non-obvious decision.
- Claude explicitly emitted NEEDS_USER.

## Overall verdict

After categorizing every issue:

- **AGREE_PASS** — Claude returned PASS AND you have no concerns of your own. The spec is ready.
- **DISAGREE_NEEDS_FIX** — Claude returned PASS, but you found a substantive issue it missed. Rare, but possible — Claude biases too.
- **CALL_USER** — at least one issue is NEEDS_USER. The orchestrator must prompt the user before continuing.

## Output format

```json
{
  "verdict": "AGREE_PASS | DISAGREE_NEEDS_FIX | CALL_USER",
  "categorization": [
    {
      "issue_id": "<index in the findings array>",
      "section": "<file:line_start-line_end from the finding>",
      "category": "ACCEPT | REJECT_PETTY | NEEDS_USER",
      "reasoning": "<one sentence why this category>"
    }
  ],
  "own_concerns": [
    "<issues Claude missed, if any>"
  ]
}
```

## Anti-patterns

❌ Agreeing with all Claude issues to reduce work — REJECT_PETTY exists exactly for this.
❌ Rejecting a substantive issue as "petty" to avoid revision — violation of the only contract this role has.
❌ Silently applying what Claude proposed without explicit categorization.
❌ Categorizing without reading the spec — you MUST read the spec from disk, not just the findings JSON.

## Prior commitment

Claude and the orchestrator both committed to running the spec through a consensus loop because single-model review is weaker. If you, as self-assessor, start agreeing/rejecting without reading the spec — you disqualify the basis for this phase's existence. The orchestrator cannot trust your verdict — then why have the cross-model setup at all.
