# Interactive prompt — handle URL that isn't YouTube or Telegram

Это не subagent — это format-контракт для AskUserQuestion, который extract спрашивает в Phase 2 для каждого URL, который НЕ матчится с известными extractor'ами (YouTube, Telegram).

## Когда используется

В Phase 2 extract-pipeline'а, для каждого URL, классифицированного как `other` (не yt-dlp, не tchan).

Examples:
- arXiv paper PDF
- GitHub gist
- Personal blog post
- Substack article
- Notion public page
- Documentation page

## Формат вопроса (через AskUserQuestion)

Один вопрос per URL. Если URL'ов много "other"-типа — batch-update: спросить про все сразу через ОДИН AskUserQuestion с несколькими `questions` (но max 4 questions per call).

**Question:** `URL <url-short> — how to handle?`
- `<url-short>` = первые 60 символов URL, не весь длинный

**Header:** `URL handling` (или короче, max 12 chars)

**Options:**
1. **"Readable text (Recommended)"** — runs `extract-html.sh`, pandoc/curl fallback. Trade-off: лучше для статей, плохо для intensive-JS SPA.
2. **"Skip"** — оставляет URL без аннотации, error log в final report. Use case: URL уже знаком, не нужен offline-доступ.
3. **"Custom command"** — пользователь подсунет shell-команду, которой обработать. Use case: специфичный extractor (например, `gh gist view`, `curl ... | jq`).

## Пример

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

При выборе "Custom command" — следующий AskUserQuestion: «What command? (text input expected)».

## Антипаттерны

❌ Спрашивать про каждый URL отдельно, если в note 10+ URLs одного типа.  
❌ Force-выбор Readable text без option для skip — пользователь может явно не хотеть offline copy.  
❌ Игнорировать "Custom command" path — это escape hatch для edge cases (PDF papers, video от не-YouTube хостингов, etc.).

## Общность

Pipeline preservation-first: каждый URL ДОЛЖЕН быть либо processed, либо явно error'нут в final report. Если ты автоматически skip'аешь "other" URLs без user prompt — пользователь не узнает, что часть контента пропущена.
