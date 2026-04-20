---
name: dry-check
description: Detect semantic code duplication via voyage-code-3 embeddings. For each new/changed function, finds similar existing functions and judges if they're genuine duplicates. Invoked automatically by Stop hook.
user-invocable: true
allowed-tools: "Read Bash"
---

# DRY Check (Embedding-based)

Detect semantic duplicates in code changed **this turn** using voyage-code-3 embeddings.

## Steps

1. Read `.claude/whitelist.yaml` to see what's explicitly accepted under `dry:`.
2. Get the list of files changed this turn:
   ```!
   cd "${CLAUDE_PROJECT_DIR:-.}" && git diff --name-only HEAD 2>/dev/null | grep ".py$" | head -20
   ```
3. Re-embed each changed file to keep the index fresh:
   ```
   For each changed file: .venv/bin/python .claude/hooks/code_embeddings.py embed <file>
   ```
4. For each function/class added or modified this turn, query for semantic neighbors:
   ```
   .venv/bin/python .claude/hooks/code_embeddings.py query <file> <symbol_name>
   ```
5. For each returned neighbor with similarity ≥ 0.92, review both the new symbol and the neighbor's content. Judge whether it is:
   - **Genuine duplication** — same logic with cosmetic differences. Flag.
   - **Structural similarity, different purpose** — e.g., two route handlers with similar shape. OK.
   - **Different layer, different concern** — e.g., a service and a worker both calling the same thing. OK.
6. Use the `role` field on neighbors to filter:
   - Don't flag `api` ↔ `api` with high similarity if they're clearly different CRUD resources.
   - Don't flag `test` ↔ `test` similarity — tests often share fixtures.
   - Cross-role matches (e.g., service ↔ engine doing the same thing) are strong duplication signals.

## Output Format

```json
{
  "decision": "approve" | "block",
  "reason": "one-line if block",
  "findings": [
    {
      "new_symbol": {
        "file": "src/app/services/foo.py",
        "name": "process_item"
      },
      "duplicate_of": {
        "file": "src/app/services/bar.py",
        "name": "handle_entry",
        "role": "service"
      },
      "similarity": 0.94,
      "verdict": "genuine-duplicate" | "structural-only" | "cross-domain",
      "reason": "Both iterate a list, apply transform, return dict. Same logic.",
      "suggestion": "Extract shared helper or use existing function."
    }
  ]
}
```

## Rules

- **Similarity thresholds:**
  - 0.92-0.95 → warn (review)
  - 0.95+ → strong duplicate signal (block if this turn introduced it)
- **Only flag new/changed code from this turn as duplicates of existing code.** Don't flag existing code against existing code.
- **Skip whitelisted entries.**
- **Max 3 findings.** Focus on the highest-similarity genuine duplicates.
- **Silent on clean code.** No findings → `{"decision": "approve", "findings": []}`.
- **If this turn introduced a genuine-duplicate with similarity ≥ 0.95 → `decision: "block"`.**
- **Otherwise `decision: "approve"` with warnings as findings.**
