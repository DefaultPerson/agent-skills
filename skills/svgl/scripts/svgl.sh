#!/usr/bin/env bash
# svgl.sh — svgl.app API helper for the /svgl skill.
#
# Subcommands:
#   categories                 -> TSV "category<TAB>total" (sorted desc by total)
#   search <query> [limit]     -> raw JSON array of matching logos
#   category <name> [limit]    -> raw JSON array of logos in a category
#   download <url> <outfile>   -> fetch one SVG to <outfile>, validate, print "saved <outfile>"
#
# Base: https://api.svgl.app  (NOT svgl.app/api — that path returns nothing).
# Deps: curl, jq. No auth. Rate limit is undocumented -> one backoff retry on HTTP 429.
# Exit: 0 on success; non-zero with an "ERROR: …" line on stderr otherwise.

set -uo pipefail

API="https://api.svgl.app"
UA="agent-skills-svgl/1.0"

# GET <path-and-query> -> JSON on stdout; non-zero + stderr on hard failure.
api_get() {
  local url="$API$1" body code
  body="$(curl -s -A "$UA" --max-time 25 -w $'\n%{http_code}' "$url")" || { echo "ERROR: curl failed for $url" >&2; return 1; }
  code="${body##*$'\n'}"; body="${body%$'\n'*}"
  if [ "$code" = "429" ]; then
    sleep 1.5
    body="$(curl -s -A "$UA" --max-time 25 -w $'\n%{http_code}' "$url")" || { echo "ERROR: curl failed for $url" >&2; return 1; }
    code="${body##*$'\n'}"; body="${body%$'\n'*}"
  fi
  [ "$code" = "200" ] || { echo "ERROR: HTTP $code for $url" >&2; return 1; }
  printf '%s' "$body"
}

urlenc() { jq -rn --arg s "$1" '$s|@uri'; }

# Optional client-side cap. svgl IGNORES the API `limit` param when `search` is
# also sent (limit wins, search is dropped), AND ignores `limit` on /category.
# So never send `limit` to those endpoints — slice the JSON array here instead.
slice() { local n="${1:-}"; if [[ "$n" =~ ^[0-9]+$ ]]; then jq ".[:$n]"; else cat; fi; }

cmd="${1:-}"; shift || true
case "$cmd" in
  categories)
    api_get "/categories" | jq -r 'sort_by(-.total)[] | "\(.category)\t\(.total)"'
    ;;
  search)
    q="${1:?usage: svgl.sh search <query> [limit]}"
    out="$(api_get "/?search=$(urlenc "$q")")" || exit 1
    printf '%s' "$out" | slice "${2:-}"
    ;;
  category)
    name="${1:?usage: svgl.sh category <name> [limit]}"
    out="$(api_get "/category/$(urlenc "$name")")" || exit 1
    printf '%s' "$out" | slice "${2:-}"
    ;;
  download)
    url="${1:?usage: svgl.sh download <url> <outfile>}"; out="${2:?usage: svgl.sh download <url> <outfile>}"
    mkdir -p "$(dirname "$out")"
    code="$(curl -s -A "$UA" --max-time 25 -w '%{http_code}' -o "$out" "$url")" || { echo "ERROR: fetch failed: $url" >&2; exit 1; }
    if [ "$code" = "429" ]; then
      sleep 1.5
      code="$(curl -s -A "$UA" --max-time 25 -w '%{http_code}' -o "$out" "$url")" || { echo "ERROR: fetch failed: $url" >&2; exit 1; }
    fi
    [ "$code" = "200" ] || { echo "ERROR: HTTP $code for $url" >&2; rm -f "$out"; exit 1; }
    # Validate it is actually an SVG (allow a leading XML decl / comments / BOM).
    if ! head -c 1024 "$out" | grep -qiE '<svg|<\?xml'; then
      echo "ERROR: not an SVG (no <svg>/<?xml in first 1KB): $url" >&2; rm -f "$out"; exit 1
    fi
    echo "saved $out"
    ;;
  *)
    echo "usage: svgl.sh {categories | search <query> [limit] | category <name> [limit] | download <url> <outfile>}" >&2
    exit 2
    ;;
esac
