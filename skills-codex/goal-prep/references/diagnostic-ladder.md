# Diagnostic ladder

`/goal-prep`'s user-facing intake surface. Uses Claude Code's
`AskUserQuestion` tool with 3 batches (1 → 2 → 3 questions). Q1 is alone
so its answer can update the interpretation before Q2/Q3 references it.

Adapted from `tolibear/goalbuddy` `$goal-prep` guided intake.

## Why 3 batches, not 6 single questions

`AskUserQuestion` allows 1-4 questions per call. Single-question batches
work but slow the user down. We batch where questions are independent.

- **Batch 1** (Q1 alone) — intent reflection. Q1's answer may invalidate
  the entire intake (option "outcome is different" → restart). Must
  resolve before asking anything else.
- **Batch 2** (Q2 + Q3) — proof + scope. After Q1 confirms the outcome,
  these two are independent enough to batch.
- **Batch 3** (Q4 + Q5 + Q6) — authority + handling + heads-up. Each
  independent.

## Pattern

Each `AskUserQuestion` option's `description` field carries the
"when-this-wins" reasoning. The first option is always the recommended
default (with `(Recommended)` suffix on the label per tool guidance).

The question text carries the reflection ("I read this as: X") plus an
explicit blind spot the user may not have named. This forces disagreement
when the interpretation is wrong.

## Batch 1 — intent target (1 question)

```
AskUserQuestion({
  questions: [{
    question: "I read your request as: '<interpreted_outcome>'. One possible blind spot: <blind_spot>. Is this the outcome you want?",
    header: "Intent",
    multiSelect: false,
    options: [
      {
        label: "Yes, that's the outcome (Recommended)",
        description: "The interpretation matches your wording; proceed to scope and proof."
      },
      {
        label: "Outcome is right, measure is wrong",
        description: "Adjust completion_proof in the next batch — keep the outcome, refine the proof."
      },
      {
        label: "Outcome is different",
        description: "Reword the request now; intake restarts from scratch."
      }
    ]
  }]
})
```

Update `goal.md ## Intake Summary` `interpreted_outcome` and
`completion_proof` based on the answer. If "Outcome is different", abort
Phase 1 and re-run the Intake Compiler against the user's new wording.

## Batch 2 — success proof + scope/non-goals (2 questions)

Only after Batch 1's interpretation is locked in.

```
AskUserQuestion({
  questions: [
    {
      question: "What evidence would convince you this worked?",
      header: "Proof",
      multiSelect: false,
      options: [
        {
          label: "<inferred proof_type> (Recommended)",
          description: "<when this is the right standard for this kind of work>"
        },
        {
          label: "<stricter alternative>",
          description: "<when stricter is justified>"
        },
        {
          label: "<weaker alternative>",
          description: "<when weaker is acceptable>"
        }
      ]
    },
    {
      question: "What stays out of scope? Name 1-2 things that look related but shouldn't be touched.",
      header: "Scope",
      multiSelect: false,
      options: [
        {
          label: "<inferred non-goals> (Recommended)",
          description: "Covers the obvious adjacent areas without overreaching."
        },
        {
          label: "None — anything in the repo is fair game",
          description: "Wide scope; only use when truly nothing is off-limits."
        },
        {
          label: "<stricter than inferred>",
          description: "Tighter scope than the recommendation."
        }
      ]
    }
  ]
})
```

Proof-type defaults per goal kind:

- QA (bug-hunt) → `artifact` (e.g. `issues.md` with N entries). Stricter: `review` (PR reviewer signoff). Weaker: `metric` (severity-weighted count ≥ threshold).
- Refactor → `test` (behavior contract diff empty). Alternatives: `metric` (line count delta), `review`.
- Greenfield → `demo` (working slice user can exercise). Alternatives: `artifact` (deployed URL), `metric` (N users completed flow).

Set `goal.md ## Intake Summary` `proof_type` and refine `completion_proof`.
Append the scope answer to `non_goals`; surface in `## Non-Negotiable
Constraints` if scope is unusually tight.

## Batch 3 — authority + handling + heads-up (3 questions)

```
AskUserQuestion({
  questions: [
    {
      question: "Do we have approval to act, or is this preparatory?",
      header: "Authority",
      multiSelect: false,
      options: [
        {
          label: "<inferred authority> (Recommended)",
          description: "<inferred-fit reason>"
        },
        {
          label: "Pre-approval only",
          description: "No destructive ops, no production touches — analysis only."
        },
        {
          label: "Full execution authority",
          description: "Including any required destructive ops and external calls."
        }
      ]
    },
    {
      question: "How to handle this goal?",
      header: "Handling",
      multiSelect: false,
      options: [
        {
          label: "Create fresh charter (Recommended)",
          description: "New slug, new goal.md."
        },
        {
          label: "Reuse existing slug `<best-match>`",
          description: "Refresh charter at that slug; only shown if a related slug exists."
        },
        {
          label: "Inspect first",
          description: "Read existing goal.md or notes/ before deciding."
        }
      ]
    },
    {
      question: "Anything else /goal should know before starting? Domain failure modes you've seen, approaches you've already tried, related work to avoid touching.",
      header: "Heads-up",
      multiSelect: false,
      options: [
        {
          label: "All clear (Recommended)",
          description: "Move forward with the intake as compiled."
        },
        {
          label: "Add what I already tried",
          description: "Type failed approaches as `Other` → appended to `goal.md ## Intake Summary` existing_plan_facts."
        },
        {
          label: "Add domain note",
          description: "Type a domain-specific failure mode as `Other` → appended to `goal.md ## Non-Negotiable Constraints` as an extra bullet."
        }
      ]
    }
  ]
})
```

If the user picks "Add what I already tried" or "Add domain note", the
`Other` slot (auto-provided by AskUserQuestion) collects free-text.
Append:

- "Add what I already tried" + Other text →
  `goal.md ## Intake Summary` `existing_plan_facts` field (preserving
  the existing value, separated by `; tried-and-failed: <text>`).
- "Add domain note" + Other text →
  `goal.md ## Non-Negotiable Constraints` as an extra bullet at the
  end of the kind-specific layer: `- Domain note: <text>`.

"All clear" → no charter mutation.

Update `goal.md ## Intake Summary` `authority`. If "Pre-approval only"
or `needs_approval`/`blocked`, record what's missing in `## Non-Negotiable
Constraints` so the main model under native /goal sees it and won't try
those actions.

Handling answer drives Phase 5 (slug + directory). Option 2 surfaces
conflicts: read existing `goal.md`; if its objective differs from the new
intake, ask via a follow-up `AskUserQuestion` how to reconcile
(overwrite / fork to `<slug>-2` / abort).

## Skipping the ladder

- `/goal-prep --defaults` — skip all 3 batches, use the Recommended option
  for every question. Note in `goal.md ## Intake Summary`
  `blind_spots_considered`: `"used --defaults — ladder skipped"`.
- `/goal-prep --from <path>/goal.md` — load existing goal.md, validate
  intake fields are populated, skip ladder.
- A question may be skipped individually if the user's raw input already
  answered it clearly. Note the skip explicitly:

  > Skipping Q3 (scope) — you said "only `src/auth/` and tests".

## Why a ladder at all

- Force the user to **disagree with the model's interpretation** before any
  work starts. Cold-start hallucinations get caught here.
- Make `completion_proof`, `non_goals`, and `authority` explicit. These
  are the three things models routinely guess wrong.
- Slow down `/goal-prep` so warmup happens naturally — the user spends a
  few minutes thinking about the problem before native /goal runs.
