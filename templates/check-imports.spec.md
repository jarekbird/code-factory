# Import Guard Hook Specification (language-agnostic)

Generate `.claude/hooks/check-imports.<ext>` — a PreToolUse hook script that blocks banned imports at the architecture boundary before the edit lands.

## Interface contract

- Read a JSON object from stdin (Claude Code hook input)
- Extract `tool_input.file_path` and `tool_input.content || tool_input.new_string`
- Examine the new content for forbidden import statements based on the file's layer
- If a violation is found: write a human-readable reason to stderr and exit with code **2**
- If no violation (or if the file is not in a watched layer): exit with code **0**

## Layer rules (adapt to target language)

For each layer boundary the project declares, check imports syntactically:

- Given a file path in layer A, and a list of modules/packages layer A is forbidden to import, scan the new content for import statements that match.
- Be language-appropriate:
  - Python: `from X import ...` / `import X` / `from X.Y import ...`
  - TypeScript/JavaScript: `import ... from 'X'` / `require('X')` / `const X = await import(...)`
  - Go: `import "X"` blocks
  - Rust: `use X::...` / `extern crate X`
  - Java/Kotlin: `import x.y.z;`

## Implementation language

Write the hook in whatever language is most practical:
- A shell script (bash/zsh) if the checks are simple text matches
- A Node script if this is a JS/TS project and Node is already available
- A Python script if Python is already available on the path
- Use the target project's package manager scripts if they exist

## Output format

```
BLOCKED: <layer> files cannot import: <banned list>. <short reason>.
```

Write to stderr. Exit 2.

## Reference implementation

See `references/python-litestar/check-imports.sh` for a working Python/Litestar version. It enforces:
- `src/app/engine/` cannot import `sqlalchemy`, `litestar`, `celery`, `app.models`, `app.services`
- `src/app/api/` cannot import `sqlalchemy` directly

## Testing

After creating the hook:
1. Make it executable (`chmod +x`)
2. Feed a test JSON to stdin manually to confirm it blocks violations and allows clean code
3. Record pass/fail
