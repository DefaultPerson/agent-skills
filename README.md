# claude-code-skills

Collection of custom skills for Claude Code CLI.

## Skills

### plan-rewrite

Rewrite and reorganize a plan file: semantic sort, AI rewrite, 100% verified gap detection.

**Usage:** `/plan-rewrite <file path>`

**Algorithm:** 9-phase pipeline — sort → verify → rewrite → gap detection (deterministic + semantic + fuzzy) → user review → apply → final verification → report.

## Installation

Copy desired skill directories into `~/.claude/skills/`.

## License

MIT
