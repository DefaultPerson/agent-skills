#!/usr/bin/env bash
# Fetch an arbitrary URL and save readable text content.
# Usage: extract-html.sh <url> <output-dir>
# Uses pandoc if available (best readable conversion), else falls back to
# raw curl + crude HTML strip.
# Output: <output-dir>/content.md + metadata.json
# Exit: 0 on success, 1 on fetch failure

set -euo pipefail

URL="${1:?usage: extract-html.sh <url> <output-dir>}"
OUT="${2:?usage: extract-html.sh <url> <output-dir>}"

mkdir -p "$OUT"

# Fetch with timeout, follow redirects, real User-Agent
HTML="$(curl -sL -A 'Mozilla/5.0 (compatible; extract-skill/1.0)' --max-time 20 "$URL" || true)"
if [ -z "$HTML" ]; then
  echo "fetch failed: $URL" >&2
  exit 1
fi

# Extract <title> for metadata
TITLE="$(echo "$HTML" | grep -oE '<title[^>]*>[^<]+</title>' | head -1 | sed -E 's/<[^>]+>//g' | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"

# Try pandoc first — much better at extracting readable content from HTML
if command -v pandoc >/dev/null 2>&1; then
  echo "$HTML" | pandoc -f html -t gfm -o "$OUT/content.md" 2>/dev/null || true
fi

# Fallback: crude HTML strip if pandoc missing or failed
if [ ! -s "$OUT/content.md" ]; then
  echo "$HTML" \
    | sed -E 's/<script[^>]*>[^<]*<\/script>//g; s/<style[^>]*>[^<]*<\/style>//g' \
    | sed 's/<[^>]*>//g' \
    | sed 's/&nbsp;/ /g; s/&amp;/\&/g; s/&lt;/</g; s/&gt;/>/g; s/&quot;/"/g; s/&#39;/'\''/g' \
    | awk 'NF' \
    | awk '{lines[NR]=$0} END{for(i=1;i<=NR;i++) print lines[i]}' \
    > "$OUT/content.md"
fi

# Metadata
jq -n --arg url "$URL" --arg title "${TITLE:-unknown}" \
  '{url: $url, title: $title, fetched_at: now | strftime("%Y-%m-%dT%H:%M:%SZ")}' \
  > "$OUT/metadata.json"

if [ ! -s "$OUT/content.md" ]; then
  echo "no content extracted: $URL" >&2
  exit 1
fi

echo "extracted: $URL → $(wc -w < "$OUT/content.md") words"
