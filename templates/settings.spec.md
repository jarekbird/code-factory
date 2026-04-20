# Hook Settings Specification

Generate `.claude/settings.json` with the hook wiring below. Substitute language-specific commands for the linter/formatter + architecture enforcement runner.

## Structure

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": ".claude/hooks/check-imports.<ext>",
            "timeout": 5
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "<format + lint --fix command for the target language>",
            "timeout": 10
          },
          {
            "type": "command",
            "command": "<re-index embeddings for the changed file, non-blocking, background>",
            "timeout": 5
          }
        ]
      }
    ],
    "Stop": [
      {
        "hooks": [
          {
            "type": "agent",
            "prompt": "Invoke the complexity-check skill at .claude/skills/complexity-check/SKILL.md...",
            "timeout": 60
          },
          {
            "type": "agent",
            "prompt": "Invoke the srp-check skill...",
            "timeout": 45
          },
          {
            "type": "agent",
            "prompt": "Invoke the dry-check skill...",
            "timeout": 60
          },
          {
            "type": "agent",
            "prompt": "Meta-check: read engineer skill + settings + factory skills, compare against code structure, flag staleness or useful additions...",
            "timeout": 60
          }
        ]
      }
    ]
  }
}
```

## Per-language command substitutions

### Python (Ruff + uv)
- Format+lint: `bash -c 'FILE=$(echo "$0" | jq -r ".tool_input.file_path // empty"); if [[ "$FILE" == *.py ]]; then .venv/bin/ruff format --quiet "$FILE" 2>/dev/null; .venv/bin/ruff check --fix --quiet "$FILE" 2>/dev/null; fi; exit 0'`
- Embed: `bash -c 'FILE=$(echo "$0" | jq -r ".tool_input.file_path // empty"); if [[ "$FILE" == *.py ]] && [[ "$FILE" == *src/* ]]; then .venv/bin/python .claude/hooks/code_embeddings.py embed "$FILE" > /dev/null 2>&1 & fi; exit 0'`

### TypeScript/JavaScript (Biome or ESLint + Prettier)
- Biome: `bash -c 'FILE=$(echo "$0" | jq -r ".tool_input.file_path // empty"); if [[ "$FILE" =~ \\.(ts|tsx|js|jsx)$ ]]; then npx biome format --write "$FILE" 2>/dev/null; npx biome check --apply "$FILE" 2>/dev/null; fi; exit 0'`
- ESLint + Prettier: `bash -c 'FILE=$(...); if [[ ... ]]; then npx prettier --write "$FILE"; npx eslint --fix "$FILE"; fi; exit 0'`

### Go (gofmt + golangci-lint)
- `bash -c 'FILE=$(echo "$0" | jq -r ".tool_input.file_path // empty"); if [[ "$FILE" == *.go ]]; then gofmt -w "$FILE"; golangci-lint run --fix "$FILE" 2>/dev/null; fi; exit 0'`

### Rust (rustfmt + clippy)
- `bash -c 'FILE=$(echo "$0" | jq -r ".tool_input.file_path // empty"); if [[ "$FILE" == *.rs ]]; then rustfmt "$FILE"; cargo clippy --fix --allow-dirty --allow-staged 2>/dev/null; fi; exit 0'`

### Java/Kotlin (spotless via Maven/Gradle)
- `bash -c 'FILE=$(...); if [[ "$FILE" == *.java ]]; then mvn spotless:apply -q; fi; exit 0'`

## Rules

- **Keep each PostToolUse hook under 500ms** for per-edit responsiveness
- **Never block** in PostToolUse format/lint — exit 0 even if formatter fails
- **Always block** (exit 2) in PreToolUse if architecture rules are violated
- **Agent hooks** in Stop can use subagents with the Read/Bash tools to invoke review skills
- Use `timeout` generously on agent hooks (30-60s) — they do real LLM work

## Reference implementation

See `references/python-litestar/settings.json` for a working Python+Litestar version.
