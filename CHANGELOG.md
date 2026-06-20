# Changelog

## 0.4.0 — 2026-06-20

`/babysit` moved from a command to a **Claude-only skill** — Claude can now invoke
it itself (still `/babysit`-typeable), with a tightly-scoped description so it only
fires on explicit watch-fix-deploy-loop intent. Its deploy/log adapter is now
platform-agnostic: any `log_cmd` / `deploy_cmd` (coolify or any platform MCP is one
option, nothing hard-coded). No Codex variant (Codex lacks `/loop`); the validator
gained a Claude-only allowlist.

## 0.3.0 — 2026-06-20

Removed `/diagnose` and `/deepen` (outside the core flow, unused). Renamed `/accept`
→ `/verify-done` (clearer intent) and `/extract` → `/extract-links`. `/extract-links`
now defaults to light (one-line inline summaries); pass `--full` for offline content
extraction. README trimmed.

## 0.2.0 — 2026-06-20

Native Codex CLI plugin packaging — `codex plugin marketplace add` + `codex plugin add`
install iron-skills directly (each Codex skill is self-contained, built from the Claude
tree by `ci/build-codex.sh`). README install simplified to one block per runtime.

## 0.1.0 — 2026-06-19

First release under the iron-skills name. Nine skills for AI coding agents
across Claude Code and Codex CLI — cleanup, extract, blueprint, diagnose,
deepen, svgl, goal-prep, autoresearch, accept — plus the `/babysit` command,
the `iron-skills:autoresearch-worker` agent, and a CI validator.
