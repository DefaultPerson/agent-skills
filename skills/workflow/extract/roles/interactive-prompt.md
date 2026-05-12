# Interactive prompt — handle a URL that isn't YouTube or Telegram

This is not a subagent — it's a format contract for the AskUserQuestion extract calls in step 2 for each URL that doesn't match a known extractor (YouTube, Telegram).

## When it's used

In step 2 of the extract pipeline, for each URL classified as `other` (not yt-dlp, not Telegram).

Examples:
- arXiv paper PDF
- GitHub gist
- Personal blog post
- Substack article
- Notion public page
- Documentation page

## Question format (via AskUserQuestion)

One question per URL. If many "other" URLs — batch them: ask about all of them via a SINGLE AskUserQuestion with multiple `questions` (but max 4 questions per call).

**Question:** `URL <url-short> — how to handle?`
- `<url-short>` = first 60 characters of the URL, not the whole long string

**Header:** `URL handling` (or shorter, max 12 chars)

**Options:**
1. **"Readable text (Recommended)"** — runs `extract-html.sh`, pandoc/curl fallback. Trade-off: good for articles, bad for JS-heavy SPAs.
2. **"Skip"** — leaves the URL un-annotated, logs an error in the final report. Use case: URL is already familiar, no offline copy needed.
3. **"Custom command"** — the user supplies a shell command to handle it. Use case: specific extractor (e.g. `gh gist view`, `curl ... | jq`).

## Example

```
Question: URL https://arxiv.org/abs/2403.17211 — how to handle?
Header: URL handling
Options:
  - label: "Readable text (Recommended)"
    description: "Fetch via curl, run through pandoc. Works for arXiv abstract pages."
  - label: "Skip"
    description: "Leave URL un-annotated. Final report flags as error."
  - label: "Custom command"
    description: "User provides shell command (e.g. 'curl ... | pdf2text')."
```

When "Custom command" is selected — the next AskUserQuestion: "What command? (text input expected)".

## Anti-patterns

❌ Asking about each URL separately when the note has 10+ URLs of the same type.
❌ Forcing Readable text without a skip option — the user may explicitly not want an offline copy.
❌ Ignoring the "Custom command" path — it's the escape hatch for edge cases (PDF papers, video from non-YouTube hosts, etc.).

## Commonality

Pipeline is preservation-first: every URL MUST be either processed or explicitly errored in the final report. If you auto-skip "other" URLs without a user prompt, the user doesn't know some content was missed.
