---
name: srp-check
description: Review changed functions and classes for Single Responsibility Principle violations. Flags symbols that do "X and Y", have too many unrelated dependencies, or have multiple reasons to change. Invoked automatically by Stop hook.
user-invocable: true
allowed-tools: "Read Bash"
---

# Single Responsibility Review

Review functions and classes changed **this turn** for SRP violations.

## Steps

1. Read `.claude/whitelist.yaml` to see what's explicitly accepted under `srp:`.
2. Get the list of files changed this turn:
   ```!
   cd "${CLAUDE_PROJECT_DIR:-.}" && git diff --name-only HEAD 2>/dev/null | head -20
   ```
3. For each changed Python file, read the code and analyze each function/class.
4. For each symbol, apply the three-check heuristic:
   - **Describe test**: Write a one-sentence "this does X" summary. If it contains "and", "also", or a list of unrelated nouns → flag SRP.
   - **Dependency grouping**: Group imports/calls by concern (I/O, domain logic, persistence, presentation). More than 2 concern groups → flag.
   - **Reasons to change**: Count distinct reasons this symbol would need modification (new data source, new business rule, new output format). More than 1 → flag.

## Output Format

```json
{
  "decision": "approve" | "block",
  "reason": "one-line summary if block",
  "findings": [
    {
      "file": "src/app/services/foo.py",
      "symbol": "FooService",
      "verdict": "ok" | "warn" | "fail",
      "one_line_reason": "does persistence AND HTTP calls AND response formatting"
    }
  ]
}
```

## Rules

- **Only flag code that was added or changed this turn.** Pre-existing violations are out of scope unless they've gotten worse.
- **Skip whitelisted symbols.**
- **Silent on clean symbols** — only report `fail` or significant `warn` findings. Max 3 findings per review.
- **If this turn introduced code with `fail` verdict → `decision: "block"` so Claude refactors it.**
- **Otherwise `decision: "approve"`.**
- Use SRP definition: "A class/function should have only one reason to change" (Martin).
- Do NOT flag orchestrator services that coordinate multiple concerns — that's their job.
