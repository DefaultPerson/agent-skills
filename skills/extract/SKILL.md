---
name: extract
description: >
  Use when a notes/plan file contains URLs (YouTube videos, Telegram posts,
  articles) whose content needs to be brought into the workspace before
  /cleanup or further analysis. Replaces each URL with a local pointer
  to extracted text. Tradeoff: YouTube subtitles via yt-dlp, public
  Telegram via embed-page scrape, generic HTML via pandoc/curl. Private
  or auth-required resources are out of scope. For 1-2 URLs, copy-paste
  is faster. Triggers: "extract", "/extract", "развернуть ссылки",
  "expand links", "fetch URLs", "извлеки контент".
when_to_use: >
  Note has 3+ URLs and downstream work (/cleanup, /clarify, mattpocock:to-prd,
  goal feature, manual analysis) needs the content available offline. Do NOT
  use for a single URL you can just open in browser, for private/auth-required
  resources, or when the user wants to keep the note as URL-references only.
disable-model-invocation: false
allowed-tools: [Bash, Read, Edit, Glob, Grep, AskUserQuestion]
---

# Extract

Pull content out of every URL in a notes file (YouTube subtitles, Telegram post text, HTML articles) into a shared sibling `extracted/<note-basename>/` directory, replacing each URL with a local pointer. Processing multiple notes in the same directory consolidates under one `extracted/` parent.

> **Letter = spirit.** If a rule blocks you from reaching the goal it was
> written for, the rule is wrong, not the goal. Don't look for a wording
> loophole — ask what the rule is protecting, and protect that.

## Usage

```
/extract <note.md> [--force]
```

`--force` re-processes URLs even if they're already annotated (default: skip already-annotated).

## Weaknesses and when NOT to use

- **Does not work with private/auth resources.** Private Telegram channels, paywalled articles, logged-in-only pages — out of scope. Those URLs return an error in the final report.
- **Depends on external tools (yt-dlp, pandoc).** If they're not installed, the skill prompts the user to install via AskUserQuestion. Never auto-installs without explicit OK. If the user declines — the matching URLs get an error. (Telegram embed-scrape needs only `curl`, which is almost always present.)
- **Overkill for 1-2 URLs.** Copy-paste is faster than the pipeline. Use it only with 3+ URLs.
- **Long YouTube videos (>2h, ~30k words).** Extract will succeed, but downstream work (cleanup) may choke on the volume. Pre-trim manually if needed.
- **JS-heavy SPA sites.** `extract-html.sh` uses curl — JS is not executed. You'll get the page skeleton without content. Use it for blog posts, articles, docs, NOT for interactive web apps.
- **Heuristic reference-detection is imperfect.** Notes often contain URLs that aren't content to extract — API doc landing pages, GitHub repo roots, citation-style references, tool homepages. The skill flags them via heuristics in step 1 and surfaces a triage prompt in step 2 (default = skip). What looks like a "tool homepage" might be content the user wants (e.g. a project's blog) — the call is always handed to the user, never silently dropped.

## How to do it wrong vs right

### Dependency management

❌ **Wrong:** yt-dlp missing → automatically `pip install --user yt-dlp` without asking.
- User might not want Python user-site packages.
- User might be on a shared system where pip is restricted.
- The skill turned itself into an installer.

✅ **Right:** Detect missing → AskUserQuestion: (1) "I'll install yt-dlp", (2) "Skip YouTube URLs", (3) "Abort". User-explicit only.

### URL annotation

❌ **Wrong:** Replace the URL in the note entirely: `[YouTube video](./extracted/youtube-abc/subtitles.en.txt)` — original URL is lost.
- Auditability: no way to tell where the content came from.
- Re-extract is impossible without the original.

✅ **Right:** URL preserved, local pointer appended next to it:
```
See https://youtube.com/watch?v=abc → [./extracted/note/youtube-abc/subtitles.en.txt](./extracted/note/youtube-abc/subtitles.en.txt)
```

### URL noise (citations, API refs, repo roots)

❌ **Wrong:** Note has 12 URLs — extract all 12, including 4 that are bare GitHub repo roots, an API docs landing page, and citation `[1] [2] [3]` references at the end.
- 4 useless extracts pollute `extracted/`, each with their own slug subfolder.
- Downstream `/cleanup` has to navigate around noise files that contain only navigation HTML.
- The user's actual content (the other 8) gets diluted; signal-to-noise drops.

✅ **Right:** Classify URLs in step 1. Detected `reference` URLs (bare hosts, `docs.*`, GitHub repo roots, package-registry landings, anchor-only fragments) are surfaced together in a single triage AskUserQuestion (step 2): "These N URLs look like references, not content — skip all? Extract all anyway? Pick which?" Default = skip all. Skipped URLs appear in the final report so the user can audit the decision.

### Multi-URL note

❌ **Wrong:** Note has 10 URLs — processed 7, 3 failed — report "extract done" without mentioning the errors.
- The user doesn't know about the 3 broken URLs.
- Downstream works from a holey map.

✅ **Right:** Final report enumerates: `7 extracted, 3 errors (with reason per URL)`. The note only annotates successful ones. Errored URLs are left un-annotated — the user decides whether to retry or accept the gap.

## Roles

`roles/interactive-prompt.md` — AskUserQuestion format for `other`-type URLs (not YouTube, not Telegram). Substitution: `{url_short}` (first 60 chars of the URL).

Scripts in `scripts/` are building blocks; the skill calls them via Bash:

| Script | Purpose | Args |
|---|---|---|
| `install-deps.sh` | Probe which tools are installed | (none) |
| `extract-youtube.sh` | yt-dlp wrapper, subtitle cleanup | `<url> <output-dir>` |
| `extract-telegram.sh` | public Telegram embed-page scrape | `<url> <output-dir>` |
| `extract-html.sh` | pandoc / curl fallback | `<url> <output-dir>` |

## What the skill does (step by step)

1. **Read the note, find URLs.** Regex `https?://[^\s)]+` (with trailing-punctuation strip). Classify each URL:
   - **`youtube`** — `youtube.com/watch?v=*` or `youtu.be/*` (specific video).
   - **`telegram`** — `t.me/<channel>/<post-id>` (specific public post).
   - **`reference`** — likely not content, by any of:
     - bare host (no path, or only `/`),
     - `docs.*` subdomain, or path starts with `/docs/`, `/reference/`, `/api/`, `/library/`,
     - GitHub repo root (`github.com/<owner>/<repo>` with no further segments — `/blob/`, `/issues/N`, `/pull/N`, `/releases/...` are content, not reference),
     - package registry landings (`npmjs.com/package/*`, `pypi.org/project/*`, `crates.io/crates/*`, `rubygems.org/gems/*`),
     - anchor-only or fragment-only URLs (`#section-id`).
   - **`other`** — everything else (article, blog post, generic HTML).
2. **Triage references with the user (if any detected).** Single AskUserQuestion listing every `reference` URL plus its detected reason. Options (mutually exclusive):
   1. **Skip all references** (default, recommended) — they go into the final report as `skipped(reference)`.
   2. **Extract all anyway** — re-class each to `other` and run them through the interactive prompt.
   3. **Pick which to extract** — fall through to per-URL prompts (1-at-a-time AskUserQuestion).

   If there are no `reference` URLs — skip this step silently.
3. **Probe dependencies.** `bash scripts/install-deps.sh`. If a tool required for the URL types is missing — AskUserQuestion (install / skip / abort). NEVER auto-install without explicit OK.
4. **For each URL — extract.** Output root is `<note-dir>/extracted/<note-basename>/` — one shared `extracted/` per directory, per-note subfolder inside. For multi-note runs in the same directory, the parent is consolidated automatically.
   - YouTube → `bash scripts/extract-youtube.sh <url> <note-dir>/extracted/<note-basename>/<slug>/`
   - Telegram → `bash scripts/extract-telegram.sh <url> <note-dir>/extracted/<note-basename>/<slug>/`
   - Other → AskUserQuestion via `roles/interactive-prompt.md`. By choice: readable HTML / skip / custom command.
   - Slug: `<type>-<short-id>` (e.g. `youtube-dQw4w9WgXcQ`, `telegram-channel-123`, `html-blog-example-com`). Max 50 chars.
   - Errors (404, private, fetch fail) — log to `<note-dir>/extracted/<note-basename>/.errors.log`, do not annotate the URL, keep going.
5. **Annotate the note.** For each SUCCESSFULLY extracted URL — append `→ [<local-path>](<local-path>)` right after the URL in the note. `<local-path>` is relative to the note: `./extracted/<note-basename>/<slug>/...`. Original URL preserved. Use the Edit tool, not Write. If a URL is already annotated (`→ [./...]` directly after) — skip unless `--force`. Triage-skipped URLs are NOT annotated.
6. **Update .gitignore.** Add `extracted/` to `.gitignore` at git root (if git is initialized). Idempotent — only append if the line isn't already there:
   ```bash
   grep -qxF 'extracted/' .gitignore 2>/dev/null || echo 'extracted/' >> .gitignore
   ```
7. **Final report + commit.** One line per URL with state `extracted` / `error` / `skipped(reference)` / `skipped(user)` plus aggregate metrics. Auto-commit `extract: <N> URLs from <note>` (only processed files, not the whole branch).

## Outputs

Per processed note (anchored at `<note-dir>/extracted/<note-basename>/`):
- `<slug>/` — extracted content (per URL):
  - YouTube: `subtitles.en.txt`, `subtitles.ru.txt` (if available), `metadata.json`
  - Telegram: `post.md`, `media/urls.txt` + optional media files
  - HTML: `content.md`, `metadata.json`
- `.errors.log` — per-URL errors (if any)
- `<note>` — modified: a local pointer link is appended next to each URL

Multi-note layout in one directory (single shared parent):
```
<dir>/note-1.md
<dir>/note-2.md
<dir>/extracted/
  note-1/
    youtube-abc/...
    telegram-xyz/...
  note-2/
    html-blog-example/...
```

Git:
- `.gitignore` — `extracted/` added
- Commit: `extract: <N> URLs from <note>` (encompasses note edit + .gitignore; the contents of `extracted/` are gitignored)

## Connections to other skills

- **Input:** any markdown file with URLs. Usually a note or plan before `/cleanup` or manual review.
- **Output:** annotated note with local pointers. Suitable for:
  - `/cleanup` — now has offline copies for gap detection
  - `mattpocock:to-prd` / manual analysis — content at hand
  - plain reading — the user opens local files faster than a browser
- **Does not call** other skills automatically. After step 6: `Extracted N URLs from <note>. Run /cleanup next if needed.` — a soft hint for the typical pipeline, not a forced chain.

## Rules

### Commonality
The note is a shared artifact. After extract, it'll be read by the user, downstream skills, and future sessions. If you skipped URLs or lost error info, everything downstream works from a holey map. Not "processed most of them" — that's "missed some", and it has to be reported explicitly.

### Prior commitment
In step 1 you committed to classifying every URL (not just `youtube`/`telegram`/`other` — also `reference`). In step 2 you committed to surfacing every `reference` URL to the user before deciding its fate. In step 4 you committed to processing EVERY remaining URL — either extracted, or explicitly errored with reason. In step 5 you committed to preserving the original URL and appending the pointer (not replacing). In step 6 — idempotent `gitignore_add`. Skipping any step withdraws the basis for trusting the final report.

### Authority
The skill exists precisely because extracting a dozen URLs by hand is slow and error-prone. If you silently skip "obviously irrelevant" URLs without prompting the user, you are judging content you haven't seen — that's the user's role, not yours. The `reference` heuristic in step 1 is a PROPOSAL, not a verdict; the triage AskUserQuestion in step 2 is where the actual skip decision lands.

## Self-check before delivering the result

Would this result pass review by a senior engineer? Concretely:

- Were all URLs from the note processed — extracted, errored (with reason), or skipped via explicit user decision (triage)?
- Were `reference`-classed URLs surfaced via AskUserQuestion in step 2 — not silently dropped?
- Is the original note annotated correctly — original URL preserved, pointer appended only for extracted ones, triage-skipped URLs left bare?
- Is the `extracted/<note-basename>/` layout consistent (slug naming, metadata.json per extract; one shared `extracted/` parent per directory)?
- Is `.gitignore` updated idempotently — no duplicate lines?
- Does the commit message reflect actual work — `extract: N URLs from <note>`?
- Does the final report enumerate every URL with state (`extracted` / `error` / `skipped(reference)` / `skipped(user)`)?
- No leaked secrets in `extracted/` (auth tokens from API responses, personal data)?

If "no" on any item — redo, don't ship.
