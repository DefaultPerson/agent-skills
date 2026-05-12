#!/usr/bin/env bash
# Extract content from a public Telegram channel post.
# Usage: extract-telegram.sh <url> <output-dir>
# Supports t.me/channel/post-id URLs only (public channels).
# Output: <output-dir>/post.md + media/ (if any media URLs)
# Exit: 0 on success, 1 on fetch failure, 2 on unsupported URL (private/etc)

set -euo pipefail

URL="${1:?usage: extract-telegram.sh <url> <output-dir>}"
OUT="${2:?usage: extract-telegram.sh <url> <output-dir>}"

mkdir -p "$OUT/media"

# Parse URL: expect https://t.me/<channel>/<post-id>
if [[ ! "$URL" =~ ^https?://t\.me/([A-Za-z0-9_]+)/([0-9]+) ]]; then
  echo "unsupported telegram URL (need t.me/channel/post-id): $URL" >&2
  exit 2
fi
CHANNEL="${BASH_REMATCH[1]}"
POST_ID="${BASH_REMATCH[2]}"

# Strategy A: try tchan (if installed)
if command -v tchan >/dev/null 2>&1; then
  if tchan post "$CHANNEL/$POST_ID" > "$OUT/post.md" 2>/dev/null; then
    echo "tchan: extracted $CHANNEL/$POST_ID" >&2
    exit 0
  fi
  echo "tchan failed, falling back to embed scrape" >&2
fi

# Strategy B: fetch the public embed page (t.me uses /s/ prefix for public web view)
EMBED_URL="https://t.me/${CHANNEL}/${POST_ID}?embed=1&mode=tme"
HTML="$(curl -s -A 'Mozilla/5.0 (compatible; extract-skill/1.0)' --max-time 15 "$EMBED_URL" || true)"

if [ -z "$HTML" ]; then
  echo "curl failed: $EMBED_URL" >&2
  exit 1
fi

# Channel may be private / post deleted / 404'd — detect "post not found"
if echo "$HTML" | grep -qE 'tgme_widget_message_error|Channel is private|Post not found'; then
  echo "telegram post not accessible: $URL (private channel or deleted)" >&2
  exit 2
fi

# Extract message text. The post text lives in .tgme_widget_message_text in the embed page.
# Light HTML stripping via sed/awk — not robust against weird formatting, but works for plain posts.
echo "$HTML" \
  | awk 'BEGIN{p=0} /<div class="tgme_widget_message_text/{p=1} p; /<\/div>/{if(p){p=0; print "---END---"}}' \
  | sed 's/<[^>]*>//g' \
  | sed 's/&nbsp;/ /g; s/&amp;/\&/g; s/&lt;/</g; s/&gt;/>/g; s/&quot;/"/g; s/&#39;/'\''/g' \
  | awk '/---END---/{exit} {print}' \
  > "$OUT/post.md"

# Extract media URLs (photos, videos) for separate download
echo "$HTML" \
  | grep -oE 'background-image:url\([^)]+\)' \
  | sed -E "s/background-image:url\(['\"]?([^'\")]+)['\"]?\)/\1/" \
  | sort -u \
  > "$OUT/media/urls.txt"

if [ -s "$OUT/post.md" ]; then
  echo "extracted: $URL → $(wc -w < "$OUT/post.md") words, $(wc -l < "$OUT/media/urls.txt") media URLs"
  exit 0
else
  echo "no content extracted: $URL" >&2
  exit 1
fi
