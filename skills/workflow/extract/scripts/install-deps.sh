#!/usr/bin/env bash
# Detect which extraction tools are installed and report status.
# Does NOT auto-install — that's the calling skill's job after asking the user.

set -uo pipefail

probe() {
  local tool="$1"
  if command -v "$tool" >/dev/null 2>&1; then
    echo "OK  $tool  ($(command -v "$tool"))"
  else
    echo "MISSING  $tool"
  fi
}

echo "=== extract skill dependency probe ==="
probe yt-dlp
probe pandoc
probe jq
probe curl

cat <<EOF

Install hints (user confirms before any install):
  yt-dlp:  pip install --user yt-dlp     OR  brew install yt-dlp
  pandoc:  brew install pandoc           OR  dnf install pandoc
  jq:      brew install jq               OR  dnf install jq
  curl:    typically preinstalled

Note: Telegram extraction uses curl + embed-page scrape (no extra tool needed).
EOF
