# agent-workflow

Spec-driven development pipeline for AI coding agents. Turn messy notes into shipped code — autonomously.

Built on the [harness pattern](https://www.anthropic.com/engineering/harness-design-long-running-apps): state on disk, deterministic verification, graceful recovery from context limits.

## The Flow

```
                /workflow:       /workflow:       /workflow:       /workflow:
                 cleanup          clarify          execute          verify
 ┌────────┐                ┌────────┐        ┌────────┐        ┌────────┐
 │ notes  ├───────────────>│tasks+AC├───────>│  code  ├───────>│  PASS  │
 │ ideas  │   sort+verify  │proof   │        │commits │        │  FAIL  │
 │ chat   │   gap-check    │[P]marks│        │per task│        │  ?     │
 └────────┘                └───┬────┘        └───┬────┘        └────────┘
                               │            worktree │
                          [approval]        agents ◄──┘ fix loop
                             gate               (max 3 rounds)
```

All commands use the `workflow:` prefix:

- **workflow:cleanup** — sort, rewrite, 3-level gap detection, 100% content preservation. Split into spec + references.
- **workflow:clarify** — tasks with Given/When/Then AC, proof commands, [P]arallel markers, execution order. Approval gate.
- **workflow:execute** — parallel worktree agents per [P] task. Each task = one commit. Auto-verify + fix loop (max 3).
- **workflow:verify** — fresh context, zero builder narrative. Run every proof command, report PASS/FAIL/UNKNOWN.
- **workflow:autoresearch** — autonomous optimization loop. One atomic change per iteration: commit → measure → keep or revert.
- **workflow:ralph-loop** — autonomous execution across context limits. Stop hook blocks exit until completion promise.
- **workflow:cancel-ralph** — abort active ralph loop.

## Example

```bash
/workflow:cleanup notes.md chat-export.md ideas.md
```

Sort semantically, rewrite into clean markdown, 3-level gap detection — **zero content loss**.

```bash
/workflow:clarify spec.md
```

Decompose into atomic tasks with acceptance criteria. Approval gate — nothing runs without your OK.

```bash
/workflow:execute spec.md
```

Parallel worktree agents, commit per task, auto-verify. ralph-loop activates automatically for large specs.

```bash
/workflow:verify spec.md
```

Independent verification — fresh context, runs every proof command.

## Installation

### Claude Code

```bash
/plugin marketplace add DefaultPerson/agent-workflow
/plugin install agent-workflow@agent-workflow
```

ralph-loop is included — long-running execution works out of the box.

### Codex CLI

```bash
git clone https://github.com/DefaultPerson/agent-workflow.git
cp -r agent-workflow/skills-codex/* ~/.codex/skills/
```

## Prerequisites

Git, `gh` CLI (authenticated), Python 3.10+.

## License

MIT
