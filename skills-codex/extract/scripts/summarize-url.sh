#!/usr/bin/env bash
# summarize-url.sh — lightweight metadata fetch for /extract LIGHT mode.
# Prints labelled metadata to stdout for the caller (the model) to condense into
# a one-line summary. Does NOT download full content: no subtitles, no pandoc
# conversion, nothing written to disk.
#
# Usage: summarize-url.sh <url>
# Output: labelled lines (TYPE / TITLE / UPLOADER / DURATION / TEXT / DESC)
#         or an "ERROR: <reason>" line.
# Exit:   always 0 — failures are reported as an ERROR: line so the caller keeps
#         going through the remaining URLs.

set -uo pipefail

URL="${1:?usage: summarize-url.sh <url>}"
UA='Mozilla/5.0 (compatible; extract-skill/1.0)'
MAXLEN=400

# Strip tags, decode common entities, collapse whitespace, truncate.
clip() {
  sed 's/<[^>]*>//g' \
    | sed 's/&nbsp;/ /g; s/&amp;/\&/g; s/&lt;/</g; s/&gt;/>/g; s/&quot;/"/g; s/&#39;/'\''/g' \
    | tr '\n' ' ' \
    | sed 's/[[:space:]]\+/ /g; s/^ //; s/ $//' \
    | cut -c "1-${MAXLEN}"
}

case "$URL" in
  *youtube.com/watch*|*youtu.be/*)
    echo "TYPE: youtube"
    if ! command -v yt-dlp >/dev/null 2>&1; then echo "ERROR: yt-dlp not installed"; exit 0; fi
    json="$(yt-dlp --skip-download --no-warnings --no-playlist -J "$URL" 2>/dev/null || true)"
    [ -n "$json" ] || { echo "ERROR: yt-dlp fetch failed (private/age-gated/removed?)"; exit 0; }
    title="$(printf '%s' "$json" | jq -r '.title // empty')"
    uploader="$(printf '%s' "$json" | jq -r '.uploader // empty')"
    dur="$(printf '%s' "$json" | jq -r '.duration_string // empty')"
    desc="$(printf '%s' "$json" | jq -r '.description // empty' | clip)"
    [ -n "$title" ]    && echo "TITLE: $title"
    [ -n "$uploader" ] && echo "UPLOADER: $uploader"
    [ -n "$dur" ]      && echo "DURATION: $dur"
    [ -n "$desc" ]     && echo "DESC: $desc"
    [ -z "$title$desc" ] && echo "ERROR: no metadata found"
    ;;
  *t.me/*)
    echo "TYPE: telegram"
    html="$(curl -s -A "$UA" --max-time 15 "${URL%/}?embed=1&mode=tme" || true)"
    [ -n "$html" ] || { echo "ERROR: telegram fetch failed"; exit 0; }
    if printf '%s' "$html" | grep -qE 'tgme_widget_message_error|Channel is private|Post not found'; then
      echo "ERROR: telegram post not accessible (private or deleted)"; exit 0
    fi
    text="$(printf '%s' "$html" \
      | awk 'BEGIN{p=0} /<div class="tgme_widget_message_text/{p=1} p; /<\/div>/{if(p){p=0; print "---END---"}}' \
      | awk '/---END---/{exit} {print}' | clip)"
    [ -n "$text" ] && echo "TEXT: $text" || echo "ERROR: no telegram preview text"
    ;;
  *)
    echo "TYPE: html"
    html="$(curl -sL -A "$UA" --max-time 20 "$URL" || true)"
    [ -n "$html" ] || { echo "ERROR: html fetch failed"; exit 0; }
    title="$(printf '%s' "$html" | grep -oiE "<title[^>]*>[^<]+</title>" | head -1 | clip)"
    metatag="$(printf '%s' "$html" | tr '\n' ' ' \
      | grep -oiE "<meta[^>]+(name=[\"']description[\"']|property=[\"']og:description[\"'])[^>]*>" | head -1)"
    desc="$(printf '%s' "$metatag" | grep -oiE "content=[\"'][^\"']*" | head -1 | sed -E "s/^content=[\"']//" | clip)"
    [ -n "$title" ] && echo "TITLE: $title"
    [ -n "$desc" ]  && echo "DESC: $desc"
    [ -z "$title$desc" ] && echo "ERROR: no title/description found (JS-SPA, paywall, or blocked?)"
    ;;
esac
exit 0
