# Cross-LLM integration (codex ↔ claude)

`iron-skills` integrates with the OTHER LLM's CLI as an
**optional** adversarial/rescue layer. Never required, never auto-applied.

Direction depends on host:

| Host | Other LLM CLI | Used for |
|------|---------------|----------|
| Claude Code | `codex review`, `codex:codex-rescue` | adversarial review at completion, rescue at stuck-loop |
| Codex CLI | `claude -p` | adversarial review at completion, rescue at stuck-loop |

Symmetric design. Plugin name is `ags`; same commands/agents work in
both hosts.

## Three invocation patterns (canonical)

Pick the right pattern for the context.

### A. CLI via Bash — for programmatic adversarial review

**Claude Code host calling codex CLI:**

```bash
codex review --uncommitted "<prompt>"      # working-tree diff
codex review --base main   "<prompt>"      # branch-vs-base diff
codex review --commit <sha> "<prompt>"     # single commit
```

**Codex host calling claude CLI:**

```bash
claude -p "<prompt with diff context>"     # headless Claude session
# Or with stdin context:
git diff main | claude -p "Adversarially review the diff above..."
```

Used by:

- `/goal-prep` charter injection (the main model under native
  `/goal` runs the CLI via Bash before declaring completion).
- `/autoresearch` Phase 8 pre-merge step.

**Why CLI:** `codex review` is a stable public subcommand of the codex
CLI; `claude -p` is a stable headless mode of claude. Neither goes
through the Skill tool, so they can be called from inside any skill or
subagent that has Bash access. Borrowed pattern from
`agent-workflow/skills/clarify` Phase 7.6 (see anti-pattern note below).

### B. Subagent via Agent tool — for stuck loops

**Claude Code host (after 3 fails, if user opts in):**

```typescript
Agent({
  subagent_type: "codex:codex-rescue",
  description: "Rescue: stuck autoresearch at iter <N>",
  prompt: `Autoresearch has produced 3 consecutive failing iterations on
the same metric.

Goal: ${scratchpad.goal}
Metric command: ${scratchpad.metric_cmd}
Direction: ${scratchpad.direction}
Last 3 history rows: ${tail3(history_tsv)}
Recent scratchpad memory: ${scratchpad.body}

Diagnose the root cause and propose a fundamentally different approach.`,
})
```

**Codex host:** no equivalent registered subagent for claude exists in
the current codex plugin ecosystem. Codex variant falls back to
Pattern A (`claude -p` via Bash) for rescue:

```bash
claude -p "Rescue: stuck autoresearch at iter <N>. Goal: <...>.
Last 3 history rows: <...>. Diagnose and propose different approach."
```

**Why subagent (Claude Code only):** `codex:codex-rescue` is registered
by the codex plugin as a subagent (see `agents/codex-rescue.md` in
`openai/codex-plugin-cc`) and exposed to the Agent tool's
`subagent_type` enum. No `disable-model-invocation` block.

### C. User-typed slash commands — for interactive workflows

The user can always type `/codex:rescue` in their Claude Code session,
or invoke `claude` interactively (no equivalent slash в Codex).
`/autoresearch` Phase 2 AskUserQuestion offers this path explicitly:
it prints the slash command so the user runs it themselves rather than
us invoking via Skill tool.

## ⚠️ Anti-pattern: do NOT invoke cross-LLM slash commands via Skill tool

```typescript
Skill({skill: "codex:adversarial-review"})  // ❌ refused
```

The codex plugin sets `disable-model-invocation: true` on several
commands (verified: `commands/adversarial-review.md`,
`commands/cancel.md`). The Skill tool refuses to call these from within
another skill — model-driven invocations are deliberately blocked at
the plugin level.

If/when claude ships similar slash commands with the same flag, the
analogous workaround applies.

**Workaround:** use Pattern A (CLI via Bash) for programmatic
adversarial review. The CLI subcommands (`codex review`, `claude -p`)
have no such gate.

This lesson is borrowed verbatim from `agent-workflow/skills/clarify`
Phase 7.6, which originally tried to invoke `/codex:rescue` via Skill
tool and got bitten by exactly this flag. From clarify SKILL.md:

> "We used to and got bitten by the Skill tool refusing to call slash
> commands with disable-model-invocation: true. The dependency is now
> the public CLI subcommand codex review, which is stable and
> documented."

## Detection (interactive, v0.3.0+)

Each skill inlines the detection check — no shared helper script. Both
hosts use the same one-line probes:

```bash
if command -v codex  >/dev/null 2>&1; then CODEX_ON_PATH=1;  else CODEX_ON_PATH=0;  fi
if command -v claude >/dev/null 2>&1; then CLAUDE_ON_PATH=1; else CLAUDE_ON_PATH=0; fi
```

(Detect-the-other only — the CC variant cares about `codex`; the Codex
variant cares about `claude`.)

**Detection only feeds the `AskUserQuestion`'s Recommended default — it
does not gate behavior.** Both commands ask the user explicitly:

- `/goal-prep` at **Phase 0.55**: "Include cross-LLM adversarial
  review as a pre-completion step in the charter?" → stored as
  `intake.cross_llm_review_enabled`. Used by Phase 8.5 to include/skip
  Step 2 of `## Adversarial Review`.
- `/autoresearch` at **Phase 0.55**: "Enable cross-LLM review hooks
  at stuck-points and pre-merge?" → stored as
  `scratchpad.cross_llm_review_enabled`. Used by Phase 2 (3-fail
  trigger) and Phase 8 (pre-merge suggestion).

If user picks "What's this about?", both commands print install info for
both CLIs and re-ask.

**Why interactive:** silent detection misses custom install paths and
gives the user no opt-out for project-specific reasons (deterministic
runs, paranoia, etc).

## Charter-injection pattern (native /goal companion)

Native `/goal` cannot be intercepted with hooks from our plugin. The
available channel is **conversation context**, which the evaluator
and main model both read.

`/goal-prep` emits, at exit, a preamble block that includes a
host-aware CLI invocation hint:

> Adversarial review: before declaring completion, run via Bash
> (pick based on host):
>   - Claude Code host: `codex review --uncommitted "<prompt>"`
>   - Codex host: `claude -p "<prompt>"`
> Address blockers before completion.

The user copies the preamble into their next message, then runs
`/goal <condition>`. Both the evaluator and main model see the
instruction. Main model picks the right CLI based on whichever is on
PATH.

We use CLI not slash commands here because the slash equivalents
(`/codex:adversarial-review`) have `disable-model-invocation: true` —
the main model under native `/goal` cannot invoke them via Skill tool.
CLI via Bash works regardless.

No enforcement — this is best-effort. If compliance turns out to be
low in practice, a dedicated `goal-review` command could be
added as an explicit manual trigger.

## Auto-suggest, never auto-apply (`/autoresearch`)

Cross-LLM CLI commands are dual-use: `codex:rescue` / `claude -p` may
write code; `codex review` runs analysis only. `/autoresearch`
must never trigger either without explicit user confirmation.

The pattern is **always**:

1. Detect the trigger condition (3 consecutive DISCARD/CRASH/GUARD_FAIL
   iterations, pre-merge of best_commit, etc).
2. Print a one-line suggestion via `AskUserQuestion`.
3. Options (host-aware):
   - **For rescue (Phase 2):**
     - Claude Code: "Try codex rescue subagent" → `Agent({subagent_type: "codex:codex-rescue", ...})` (Pattern B)
     - Codex: "Run claude -p rescue" → `claude -p "<context>"` via Bash (Pattern A)
     - Either host: "Print rescue command for me to run" → user types interactively (Pattern C)
   - **For review (Phase 8 pre-merge):**
     - Claude Code: "Run codex review now" → `codex review --base main` via Bash
     - Codex: "Run claude review now" → `claude -p` with diff context via Bash
4. If user picks `Skip`, log `cross_llm_skipped_at_<phase>: <reason>` in
   scratchpad and continue.

## CRITICAL: Do not auto-apply review findings

Ported from `codex-plugin-cc`'s `codex-result-handling` skill (Apache 2.0,
attribution in LICENSE):

> After presenting review findings, **STOP**. Do not make any code
> changes. Do not fix any issues. You MUST explicitly ask the user which
> issues, if any, they want fixed before touching a single file.
> Auto-applying fixes from a review is strictly forbidden, even if the
> fix is obvious.

For `iron-skills` specifically (applies to BOTH codex and claude
review output):

- **CLI review output (codex review / claude -p)** — present findings
  to the user, then use `AskUserQuestion` to ask which findings, if any,
  should be addressed. Do **not** auto-edit files based on review prose
  alone.
- **`codex:codex-rescue` subagent output (Claude Code only)** — Codex
  may have written code itself. Present the diff + summary to the user;
  ask via `AskUserQuestion` whether to keep the changes or revert.
- **Failed cross-LLM run** — if codex/claude reports auth/setup issues,
  direct the user to the appropriate setup command and stop. Do not
  improvise an alternate auth flow.

Rationale: Cross-LLM means using a different model with different
alignment. Auto-applying its output bypasses anti-patterns and intake
constraints that the goal's charter spelled out.

## Preserve evidence boundaries

When relaying cross-LLM output back to the user (applies to both):

- Preserve the helper's verdict, summary, findings, and next-steps
  structure.
- For review output: present findings first, ordered by severity.
- Use file paths and line numbers exactly as the OTHER LLM reports them.
- If the OTHER LLM marked something as an inference, uncertainty, or
  follow-up question, **preserve that distinction**. Don't promote
  inferences to facts.
- If the OTHER LLM made edits, say so explicitly and list the touched
  files.
- If there are no findings, say so explicitly and keep any residual-risk
  note brief.

These rules are also from `codex-result-handling` and prevent laundering
uncertainty into confidence — equally applicable to either CLI's output.

## Trigger points

### `/autoresearch`

| Trigger | Pattern | Claude Code command | Codex command |
|---------|---------|---------------------|---------------|
| 3 consecutive `DISCARD`/`CRASH`/`GUARD_FAIL` rows | B or C | `Agent({subagent_type: "codex:codex-rescue", ...})` or print `/codex:rescue` | Bash `claude -p "<context>"` or print interactive `claude` invocation |
| About to merge `best_commit` into `main` | A (CLI) | Bash `codex review --base main "<prompt>"` | Bash `claude -p` with `git diff main` context |

### `/goal-prep`

No runtime cross-LLM invocation in /goal-prep itself (it's
non-execution). Instead, it emits a Bash command into the charter +
preamble that the host's main model runs at completion time:

- Claude Code host: `codex review --uncommitted "<prompt>"`
- Codex host: `claude -p "<prompt>"`

Downstream, the main model under native `/goal` picks the right CLI
based on what's on PATH and runs it via Bash before declaring
completion.

## Fallback when neither CLI available

- Do not surface suggestions to the user.
- Log silently in scratchpad: `cross_llm_skipped_at_<phase>: <reason>`.
- Continue with the command's normal fallback (pivot logic in
  /autoresearch Phase 2; pause for user input via `AskUserQuestion`).

## Why optional and not required

- codex CLI requires its own setup (OpenAI API key or ChatGPT subscription).
- claude CLI requires Claude account (Anthropic API key or claude.ai sub).
- Both are separate runtimes; not all users have either.
- The plugin's core value (`/goal-prep` intake + anti-patterns +
  `/autoresearch` deterministic loop) stands without external
  advisors.

Treat cross-LLM as a force multiplier, not a dependency.
