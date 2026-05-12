---
name: extract
description: >
  Use when a notes/plan file contains URLs (YouTube videos, Telegram posts,
  articles) whose content needs to be brought into the workspace before
  /cleanup or further analysis. Replaces each URL with a local pointer
  to extracted text. Tradeoff: YouTube subtitles via yt-dlp, public
  Telegram via tchan/embed-scrape, generic HTML via pandoc/curl. Private
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

Pull content out of every URL in a notes file (YouTube subtitles, Telegram post text, HTML articles) into a sibling `<note>.extracted/` directory, replacing each URL with a local pointer.

> **Буква = дух.** Если правило мешает достичь цели, ради которой оно
> написано — правило ошибочно, а не цель. Не ищи лазейку в формулировке —
> спроси, что правило защищает, и защищай это.

## Usage

```
/extract <note.md> [--force]
```

`--force` re-processes URLs even if they're already annotated (default: skip already-annotated).

## Слабые стороны и когда НЕ использовать

- **Не работает с private/auth resources.** Private Telegram channels, paywalled articles, logged-in-only pages — out of scope. Те URL вернут error в final report.
- **Зависит от внешних tools (yt-dlp, tchan, pandoc).** Если они не установлены, скилл предложит install через AskUserQuestion. Никогда не auto-install без OK. Если пользователь отказывается — соответствующие URL получают error.
- **Излишен для 1-2 URL'ов.** Copy-paste быстрее, чем pipeline. Используй только если 3+ URL.
- **Длинные YouTube видео (>2h, ~30k слов).** Extract пройдёт, но downstream работа (cleanup) может задохнуться от объёма. Pre-trim'ить вручную если нужно.
- **JS-heavy SPA сайты.** `extract-html.sh` использует curl — JS не выполняется. Получишь скелет страницы без контента. Используй для blog posts, articles, docs, НЕ для interactive web apps.

## Как делать неправильно vs правильно

### Dependency management

❌ **Плохо:** yt-dlp missing → автоматически `pip install --user yt-dlp` без спроса.
- User может не хотеть Python user-site packages.
- User может быть на shared system, где pip нельзя.
- Скилл превратился в installer.

✅ **Хорошо:** Detect missing → AskUserQuestion: (1) "I'll install yt-dlp", (2) "Skip YouTube URLs", (3) "Abort". User-explicit only.

### URL annotation

❌ **Плохо:** Replace URL в note полностью: `[YouTube видео](./extracted/youtube-abc/subtitles.en.txt)` — original URL потерян.
- Auditability: не понять, откуда контент.
- Re-extract невозможен без оригинала.

✅ **Хорошо:** URL preserved, рядом appended local pointer:
```
Смотри https://youtube.com/watch?v=abc → [./note.extracted/youtube-abc/subtitles.en.txt](./note.extracted/youtube-abc/subtitles.en.txt)
```

### Multi-URL note

❌ **Плохо:** Note содержит 10 URL — обработал 7, на 3 упал — отчитал "extract done" без error mentions.
- Пользователь не знает про 3 broken URL.
- Downstream работает с дырявой картой.

✅ **Хорошо:** Final report enumerates: `7 extracted, 3 errors (with reason per URL)`. Original note annotates только successful ones. Error URL'ы остаются без аннотации — пользователь решает, переобработать или забыть.

## Роли

`roles/interactive-prompt.md` — format для AskUserQuestion при obrabatывании `other`-типа URL (не YouTube, не Telegram). Substitution: `{url_short}` (первые 60 chars URL).

Scripts в `scripts/` — building blocks, скилл вызывает их через Bash:

| Script | Purpose | Args |
|---|---|---|
| `install-deps.sh` | Probe which tools installed | (none) |
| `extract-youtube.sh` | yt-dlp wrapper, subtitle cleanup | `<url> <output-dir>` |
| `extract-telegram.sh` | tchan / embed scrape | `<url> <output-dir>` |
| `extract-html.sh` | pandoc / curl fallback | `<url> <output-dir>` |

## Что делает скилл (по шагам)

1. **Прочитать note, найти URLs.** Regex `https?://[^\s)]+` (с trailing-punctuation strip). Классификация по домену: `youtube.com|youtu.be` → youtube, `t.me` → telegram, всё остальное → other.
2. **Probe dependencies.** `bash scripts/install-deps.sh`. Если для нужных типов URL tool отсутствует — AskUserQuestion (install / skip / abort). НИКОГДА auto-install без OK.
3. **Для каждого URL — extract.**
   - YouTube → `bash scripts/extract-youtube.sh <url> <note>.extracted/<slug>/`
   - Telegram → `bash scripts/extract-telegram.sh <url> <note>.extracted/<slug>/`
   - Other → AskUserQuestion через `roles/interactive-prompt.md`. По выбору: readable HTML / skip / custom command.
   - Slug: `<type>-<short-id>` (например `youtube-dQw4w9WgXcQ`, `telegram-channel-123`, `html-blog-example-com`). Max 50 chars.
   - Errors (404, private, fetch fail) — лог в `<note>.extracted/.errors.log`, URL не аннотируется, продолжать дальше.
4. **Annotate note.** Для каждого SUCCESSFULLY extracted URL — append `→ [<local-path>](<local-path>)` сразу после URL в исходной note. Original URL preserved. Use Edit tool, не Write. Если URL уже annotated (есть `→ [./...]` сразу после) — skip unless `--force`.
5. **Update .gitignore.** Add `*.extracted/` к `.gitignore` git root'а (если git initialized). Idempotent — `gitignore_add` из `bin/common.sh`.
6. **Final report + commit.** Output 1 строка на URL (extracted / error / skipped), aggregate metrics. Auto-commit `extract: <N> URLs from <note>` (только processed-files, не вся ветка).

## Outputs

Per processed note:
- `<note>.extracted/<slug>/` — extracted content (per URL):
  - YouTube: `subtitles.en.txt`, `subtitles.ru.txt` (если есть), `metadata.json`
  - Telegram: `post.md`, `media/urls.txt` + optional media files
  - HTML: `content.md`, `metadata.json`
- `<note>.extracted/.errors.log` — errors per URL (если были)
- `<note>` — модифицирован: рядом с каждым URL добавлен local pointer link

Git:
- `.gitignore` — добавлен `*.extracted/`
- Commit: `extract: <N> URLs from <note>` (encompasses note edit + .gitignore + не contents of .extracted/ т.к. они gitignored)

## Связи с другими скиллами

- **Вход:** Любой markdown-файл с URL'ами. Обычно — note или plan, перед `/cleanup` или ручной обработкой.
- **Выход:** Аннотированная note с local pointers. Подходит для:
  - `/cleanup` — теперь у cleanup есть offline-копии для gap detection
  - `mattpocock:to-prd` / manual analysis — контент под рукой
  - Голое чтение — пользователь открывает локальные файлы быстрее, чем браузер
- **Не вызывает** другие скиллы автоматически. После Step 6: `Extracted N URLs from <note>. Run /cleanup next if needed.` — мягкая подсказка для типичного pipeline'а, без force'инга.

## Правила

### Общность
Note — общий артефакт. После extract'а её будут читать пользователь, downstream скиллы, future-сессии. Если ты skip'ал URLs или потерял error info — все downstream работают с дырявой картой. Не "обработал почти все" — это "не обработал часть", и это надо явно репортить.

### Прежнее обязательство
В шаге 2 ты обязался обработать КАЖДЫЙ URL — либо extracted, либо явно error'нут с reason. В шаге 4 ты обязался preserve original URL и append pointer (не replace). В шаге 5 — gitignore_add idempotent. Пропуск любого шага = withdrawing основание доверять final report.

### Авторитет
Скилл существует именно потому, что вручную extract'ить десяток URL — медленно и ошибкогенно. Если ты skip'аешь "ясно, что нерелевантно" без user prompt — ты в роли судьи относительно content, который не видел. Это не твоя роль; решение пропустить — у пользователя через AskUserQuestion.

## Самопроверка перед выдачей результата

Прошёл бы этот результат ревью у синьора? Конкретно:

- Все URL из note обработаны (extracted) ИЛИ явно error'нуты в final report (с reason)?
- Оригинальная note корректно аннотирована — original URL preserved, pointer appended?
- `<note>.extracted/` структура согласована (slug naming, metadata.json для каждого extract'а)?
- `.gitignore` обновлён idempotent — нет дублирования строк?
- Commit message reflects actual work — `extract: N URLs from <note>`?
- Нет утёкших secrets в `<note>.extracted/` (auth tokens из API responses, личные данные)?

Если "нет" хоть на один пункт — переделай, не отдавай.
