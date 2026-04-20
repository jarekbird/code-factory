---
name: complexity-check
description: Unified complexity review — runs Ruff static checks (cyclomatic, perf patterns) plus LLM analysis of algorithmic complexity (Big O reasoning). Invoked automatically by Stop hook and user-invocable manually.
user-invocable: true
allowed-tools: "Read Bash"
argument-hint: "[file-path or --all]"
---

# Complexity Review

Two-layer complexity analysis: deterministic Ruff rules + LLM algorithmic reasoning.

## Scope

- **Stop hook (automatic)** — analyzes files changed this turn via `git diff --name-only HEAD`
- **Manual invocation** — `$ARGUMENTS` is a file path or glob; empty means all tracked Python files

## Steps

### 1. Deterministic static checks (Ruff)

Run the relevant Ruff rules on the files in scope:

```!
cd "${CLAUDE_PROJECT_DIR:-.}" && TARGET="${1:-$(git diff --name-only HEAD 2>/dev/null | grep '.py$' | head -20 | tr '\n' ' ')}"
if [ -n "$TARGET" ]; then
  .venv/bin/ruff check --select C90,PLR0911,PLR0912,PLR0915,PERF,SIM,B $TARGET 2>&1 | head -40
fi
```

Capture violations for the JSON output.

### 2. Whitelist lookup

Read `.claude/whitelist.yaml`. Anything listed under `complexity:` is skipped — just note it as `acceptable-by-design`.

### 3. LLM algorithmic review

For each file in scope, read the Python source and reason about:
- Nested loops over the same collection (potential O(n²))
- Linear scans where a dict/set lookup would be O(1)
- SQLAlchemy relationship access inside a loop (N+1)
- `list.append` in a loop that should be a comprehension
- All-pairs geometric comparison that should use a spatial index (KD-tree, R-tree)
- Missing indexes on filtered columns
- Recursive calls without memoization where appropriate

These are the cases Ruff cannot see — they require understanding intent and data shape.

## Output Format

```json
{
  "decision": "approve" | "block",
  "reason": "one-line summary if block",
  "static_findings": [
    {
      "file": "src/app/services/foo.py",
      "line": 42,
      "rule": "PLR0912",
      "message": "Too many branches (13 > 12)"
    }
  ],
  "llm_findings": [
    {
      "file": "src/app/services/foo.py",
      "function": "bar",
      "severity": "blocker" | "review" | "acceptable-by-design",
      "issue": "description",
      "suggestion": "concrete fix or alternative"
    }
  ]
}
```

## Decision Rules

- **Only block on code added or changed this turn.** Pre-existing violations → warn only, decision: approve.
- **Whitelisted entries** → silent, don't include in findings.
- **Severity guide:**
  - `blocker` — clear anti-pattern with an obvious better solution (N+1, linear scan of huge collection)
  - `review` — worth discussing, judgment call
  - `acceptable-by-design` — intentionally expensive (graph matching, TF alignment). Note but don't block.
- **Max 5 llm_findings and 10 static_findings** — focus on highest-severity.
- **Silent on clean code** — both finding arrays can be empty.
- **Block only if this turn introduced a `blocker` severity finding.** Static findings alone don't block (Ruff's `--fix` would already have handled the fixable ones).

## For Empirical Big O Measurement

If you need hard empirical data (actual O(n) vs O(n²) confirmation), use `/benchmark` — that skill runs the bigO library at varying input sizes. This static check only reasons about patterns.
