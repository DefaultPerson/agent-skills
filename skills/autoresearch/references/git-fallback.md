# Git fallback

`iron-skills` commands handle git presence differently. `/goal-prep` is
git-optional; `/autoresearch` requires git.

## Detection

Inline check (no helper script — each skill calls this directly):

```bash
if [ -d .git ] || git rev-parse --git-dir >/dev/null 2>&1; then
    GIT_PRESENT=1
else
    GIT_PRESENT=0
fi
```

## `/goal-prep`

Git is not required. `/goal-prep` only writes `goal.md` charter +
`notes/` directory. These can live anywhere.

If git is present, the prep skill prints a hint at exit:

> Tip: the charter directory `<path>` is inside a git repo. Commit it
> now if you want this goal's intake captured in history.

## `/autoresearch`

`/autoresearch` requires git. The loop is built on `commit → verify →
keep` or `commit → verify → revert`. Without git there's no revert.

Behavior without git: refuse to start with a clear message:

> /autoresearch requires a git repository. Run `git init && git add -A
> && git commit -m 'baseline'` before invoking /autoresearch.

This is documented in the autoresearch SKILL.md Phase 0 setup.

## Branch hygiene (`/autoresearch`)

`/autoresearch` uses branch `autoresearch/<slug>` (existing convention
from `agent-workflow`). The branch persists after the loop ends; user
merges or cherry-picks into their working branch when ready.

## What about Mercurial / Jujutsu / Pijul?

Out of scope. The detection logic only checks for `.git`. Adding other
VCS support would require parallel revert logic and is not a current
priority.
