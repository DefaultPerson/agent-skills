# State conventions

> **Scope:** this applies to `/autoresearch` state files and `/goal-prep`
> charter directories only. Native `/goal` manages its own internal state;
> we don't touch it.

`iron-skills` keeps state on disk. The `/autoresearch` loop reads state
at the start of every iteration; nothing depends on conversation context
surviving.

## Locations

| Skill | Location |
|-------|----------|
| `/goal-prep` | `<cwd>/.ags/<slug>/{goal.md, run.txt, notes/}` (no `state.yaml`; was `<cwd>/.claude/ags/<slug>/` before v0.3.2 — legacy path still recognized for resume/archive; `preamble.md` was emitted before v0.3.3 — dropped) |
| `/autoresearch` | `<cwd>/autoresearch-scratchpad.md` + `<cwd>/autoresearch-history.tsv` on branch `autoresearch/<slug>` (scratchpad+history backwards-compatible with `agent-workflow`; per-iteration receipt files were dropped in v0.3.1) |

All paths are project-relative. Storage is committable; users decide
whether to keep `.ags/` in `.gitignore` or not (commit-tracking it lets
the charter live in project history).

## Slug derivation

```bash
slug() {
    local raw="$1"
    echo "$raw" \
        | tr '[:upper:]' '[:lower:]' \
        | sed 's/[^a-z0-9]/-/g; s/--*/-/g; s/^-//; s/-$//' \
        | cut -c1-40
}
```

Each skill inlines this snippet — no shared helper script.

If `slug` collides with an existing directory, append `-2`, `-3`, etc., or
ask the user (`/goal-prep` Phase 5).

## Atomic writes (for `/autoresearch` scratchpad and `/goal-prep` charter)

Always write via temp-file rename. POSIX `mv` is atomic on the same
filesystem.

```bash
TMPF=$(mktemp -p "${DIR}" .${BASE}.XXXXXX)
write_content > "$TMPF"
mv "$TMPF" "${DIR}/${BASE}"
```

Never write directly to a long-lived file. A concurrent reader (or
crashed mid-write) would otherwise see truncated content.

## Concurrency

Two sessions in the same cwd would race. Guard writes with `flock` on a
sibling `.lock` file:

```bash
(
    flock -n 9 || { echo "[lock-conflict] another session is writing; aborting"; exit 1; }
    TMPF=$(mktemp -p "${DIR}" .${BASE}.XXXXXX)
    printf '%s' "$NEW_CONTENT" > "$TMPF"
    mv "$TMPF" "${DIR}/${BASE}"
) 9>"${DIR}/.lock"
```

Lock file lives at `<dir>/.lock`. Do not commit it; add to `.gitignore`
if directory is committed.

## Schema versioning (`autoresearch-scratchpad.md` only)

Current version: `state_schema_version: 3` (introduced in v0.3.0;
renames `codex_enabled` → `cross_llm_review_enabled` for bidirectional
cross-LLM review support). Previous v2 (in v0.2.0) added `codex_enabled`
field. v0.3.1 dropped the sibling `autoresearch-iterations/` receipts
directory but did NOT bump the schema (receipts were never required
fields).

`/autoresearch` refuses to operate when the file version is newer
than it knows:

```bash
ver=$(yq '.state_schema_version' autoresearch-scratchpad.md)
CURRENT=3
if [ "$ver" -gt "$CURRENT" ]; then
    echo "[schema-future] scratchpad v$ver is newer than this plugin (v$CURRENT). Update iron-skills."
    exit 1
fi
```

**v1/v2 → v3 auto-migration** runs in Phase 0.5b on `--continue`:
- Remove deprecated `codex_available`, `codex_skipped_at_phase_2`,
  `codex_enabled`.
- Add `cross_llm_review_enabled` (asks user at Phase 0.55).
- Pre-existing `autoresearch-iterations/` directories from older runs
  are left untouched (v0.3.1 dropped receipt writes; nothing reads them).
- Bump `state_schema_version` to 3.

Older states without `state_schema_version` field are treated as v1
and migrated identically.

`/goal-prep` doesn't have a state file to version (only `goal.md` charter,
which is user-editable plain markdown).

## Final state on `/autoresearch` completion

When `max_iterations` is reached or `--abort` is invoked:

- Keep `autoresearch-scratchpad.md`, `autoresearch-history.tsv`, and the
  `autoresearch/<slug>` branch in place. These are the post-mortem.
- Delete crons (see `scheduling-policy.md`).
- Do not delete artifacts.
