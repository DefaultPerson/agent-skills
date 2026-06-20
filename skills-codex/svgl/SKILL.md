---
name: svgl
description: >
  Fetch SVG brand/tech logos from the svgl.app public API into a project — by
  name, by category, or just listing categories. Downloads the actual `.svg`
  file(s) locally (handling light/dark theme variants and optional wordmarks),
  or with `--json` returns metadata/URLs only. Tradeoff: depends on svgl.app's
  catalogue (~660 logos) and its undocumented rate limit; only public logos.
  For a single logo you already have a URL for, just curl it. Triggers:
  "svgl", "/svgl", "get logo", "fetch logo", "svg logo", "download logo",
  "логотип", "svg иконка", "достань логотип".
when_to_use: >
  You want one or more brand/tech logos as local SVG files (e.g. for a frontend
  project's assets), and svgl.app likely has them. Do NOT use for non-SVG
  assets, for private/internal logos not in svgl.app, or when you only need to
  know a logo exists (use `--json` then). Not a general image downloader.
allowed-tools: [Bash, Read, Glob]
---

# svgl (Codex variant)

Fetch SVG logos from [svgl.app](https://svgl.app) via its public API: search by name, browse categories, download the `.svg` files (light/dark aware) into your project.

This is the **Codex CLI variant**. Behaviourally identical to the Claude Code variant — only the user-interaction idiom differs (numbered list TUI prompt instead of `AskUserQuestion`). The shared `scripts/svgl.sh` comes from the Claude variant tree via install-time symlinks.

> **Letter = spirit.** If a rule blocks you from reaching the goal it was
> written for, the rule is wrong, not the goal. Don't look for a wording
> loophole — ask what the rule is protecting, and protect that.

## Usage

```
/svgl <name> [name2 ...] [flags]
/svgl --category <Category> [--limit N] [flags]
/svgl --list-categories
```

Flags:
- `--theme light|dark|both` — for logos that ship theme variants. Default **both** (writes `-light`/`-dark` files); single-variant logos ignore it.
- `--out <dir>` — output directory. Default `./svgl/`.
- `--wordmark` — also download the wordmark variant if the logo has one.
- `--json` — don't download; print matched logos' title / category / website / SVG URL(s).
- `--limit N` — cap results (search and category).
- `--all` — download every match without asking (skip disambiguation).
- `--force` — overwrite existing files (default: skip files already present).

## Weaknesses and when NOT to use

- **Best-effort catalogue.** svgl.app has ~660 logos. If a brand isn't there, the term simply returns no match (reported, not invented). Not a universal logo source.
- **Undocumented rate limit.** The API has no published limit; large `--all` batches may hit HTTP 429. `scripts/svgl.sh` retries once with backoff per request — for big category dumps, expect it to be slow, and prefer `--limit`.
- **Public logos only.** No auth; private/internal brand kits are out of scope.
- **svgl API quirk (handled):** the API `limit` param is **ignored when combined with `search` or `/category`** (it silently returns the unfiltered list). `scripts/svgl.sh` therefore never sends `limit` to those endpoints and slices client-side. Don't "fix" this by adding `&limit=` to a search URL — it breaks the search.
- **Literal substring search.** `search` matches the title as a case-insensitive substring, so `nextjs` does NOT match `Next.js` (the dot breaks it) — use `next`. A no-match query is a clean "not found": svgl signals zero results with HTTP 404, which `scripts/svgl.sh` normalises to an empty result (so it never surfaces as a scary error).
- **Not an SVG optimiser/editor.** It downloads files as-is from svgl's CDN.
- **Non-interactive mode (`codex exec`).** Ambiguous queries (>1 match, no exact title) and the category bulk-download confirm need user input. If invoked from `codex exec` without a TTY, fail with an explicit error rather than guessing the first hit — or require an unambiguous query / `--all`.

## How to do it wrong vs right

### Polymorphic `route` / `category`

❌ **Wrong:** Treat `item.route` as always a string → `curl $(jq -r .route)` downloads the literal `[object Object]` / fails for theme-aware logos like React.
- `route` (and `wordmark`) is **`string` OR `{light, dark}`**; `category` is **`string` OR `string[]`**. No flag says which.

✅ **Right:** Branch on type with jq:
```bash
# route URL(s) for the requested theme
jq -r 'if (.route|type)=="object" then .route.light, .route.dark else .route end'
# categories as a flat list
jq -r '(.category | if type=="array" then .[] else . end)'
```

### Disambiguation

❌ **Wrong:** `/svgl react` → silently download the first search hit (`Preact`).
- The user asked for "react"; guessing wastes their time and clutters the repo.

✅ **Right:** If there's an exact (case-insensitive) title match, take it. Otherwise, if >1 match, print a numbered TUI list and wait for a reply:
```
Multiple matches for "react":
  1. Preact (Library)
  2. React (Library)
  3. React Query (Library)
  4. React Router (Library)
  5. React Wheel Picker (Library)
Which to download? (number, comma-separated list, "all", or "cancel")
> _
```
Accept numbers / `all` / `cancel`. The user picks (or pass `--all`).

### Search vs limit

❌ **Wrong:** `svgl.sh` builds `/?search=react&limit=20` → svgl ignores `search`, returns 20 random logos.

✅ **Right:** Fetch `/?search=react` alone; cap with jq `.[:N]` client-side (the script's `slice`). Same for `/category`.

## Roles

`scripts/svgl.sh` (shared — symlinked from the Claude variant tree at install time) wraps the API. Base URL `https://api.svgl.app`. Deps: `curl`, `jq` (both already required by the plugin).

| Subcommand | Purpose | Output |
|---|---|---|
| `svgl.sh categories` | list categories | TSV `category<TAB>total`, sorted by total |
| `svgl.sh search <query> [limit]` | search by title (substring, case-insensitive) | raw JSON array (client-side sliced) |
| `svgl.sh category <name> [limit]` | logos in a category (name **case-sensitive**) | raw JSON array (client-side sliced) |
| `svgl.sh download <url> <outfile>` | fetch one SVG, validate it's SVG | `saved <outfile>` or `ERROR: …` |

## What the skill does (step by step)

1. **Parse args** — terms vs flags. Pick the mode: `--list-categories` / `--category` / search-terms.

2. **`--list-categories`** → `bash scripts/svgl.sh categories` → print the table. Done.

3. **`--category <C>`** → resolve `<C>` against `svgl.sh categories` **case-insensitively** (the endpoint is case-sensitive; map e.g. `library`→`Library`). If no category matches, report the valid names and stop. Then `bash scripts/svgl.sh category <RealName> [N]`. With `--json` → print metadata. Otherwise, unless `--all`, show how many were found and confirm via a numbered TUI prompt (1 = download all N / 2 = pick / 3 = cancel) before a bulk download (a category can be dozens of logos). Then go to step 5 for each chosen item.

4. **Search terms** — for each term: `bash scripts/svgl.sh search "<term>" [N]`.
   - 0 results → record `not found: <term>`, continue.
   - Exact case-insensitive title match present → take that one item.
   - Else exactly 1 result → take it.
   - Else (>1, no exact) → numbered TUI list (see ✅ above); accept numbers / `all` / `cancel`. With `--all`, take all matches.

5. **Resolve URLs + filenames** for each chosen item:
   - `slug` = `title` lowercased, every run of non-`[a-z0-9]` → `-`, trimmed (e.g. `Proton Mail`→`proton-mail`, `D3.js`→`d3-js`).
   - `route` is a **string** → one file `<slug>.svg`.
   - `route` is **`{light,dark}`** → per `--theme`: `both` (default) → `<slug>-light.svg` + `<slug>-dark.svg`; `light`/`dark` → only that one, `<slug>-<theme>.svg`.
   - `--wordmark` and `wordmark` present → same rules with a `-wordmark` infix (`<slug>-wordmark.svg` or `<slug>-wordmark-<theme>.svg`).
   - `--json` → skip download; emit `{title, category, url, files:[urls]}` per item and stop.

6. **Download** — for each (url, filename): if the file exists and no `--force`, skip (report `exists`). Else `bash scripts/svgl.sh download "<url>" "<out>/<filename>"`. Default `<out>` = `./svgl/` (created on demand).

7. **Report** — per item: `saved <path>` / `exists <path>` / `error (<reason>)`; plus `not found: <term>` lines and a one-line aggregate (`K saved, M skipped, E errors`).

## Outputs

- SVG files under `--out` (default `./svgl/`), e.g. `svgl/react-light.svg`, `svgl/react-dark.svg`, `svgl/vercel.svg`.
- Nothing else is written; the skill never edits the source note or `.gitignore`. With `--json`, no files — only a printed report.
- No auto-commit (these are project assets; committing them is the user's call).

## Connections to other skills

- Standalone utility — not part of the cleanup→blueprint flow and **does not call** other skills.
- Pairs naturally with `frontend-design` / any UI work that needs brand logos.

## Rules

### Authority (the user picks the logo)
The "this is probably the React they meant" guess is a proposal, not a verdict. When the query is ambiguous (>1 match, no exact title), the choice is the user's via the numbered TUI prompt, not a silent first-hit download. The exception is `--all` (explicit intent) and an exact title match (unambiguous).

### Commonality (report the whole truth)
Every requested term ends as `saved` / `exists` / `error` / `not found`. "Got most of them" hides the gaps; downstream work (or the user's asset folder) then has holes they don't know about.

### Prior commitment (handle the polymorphism)
You committed to branching on `route`/`category` type. Skipping it ("route is a string") silently corrupts theme-aware logos. Not an optimisation — a correctness bug.

## Self-check before delivering the result

- Did every search term resolve to `saved` / `exists` / `error` / `not found` — none silently dropped?
- For theme-aware logos, did you branch on `route` type and write the right `-light`/`-dark` files (not a broken `[object Object]` fetch)?
- Was an ambiguous query (>1 match, no exact) sent through the numbered TUI prompt, not auto-resolved to the first hit?
- Are downloaded files valid SVGs (the script validates `<svg`/`<?xml`; an `ERROR:` means it wasn't)?
- Did you respect `--out` / `--theme` / `--force`, and create `./svgl/` only when actually downloading?

If "no" on any item — redo, don't ship.
