---
name: dead-code-check
description: Detect dead code — unused functions, abandoned modules, orphaned files, stale TODO/FIXME markers. LLM-based review that complements the language's syntactic linter checks. Invoked automatically by Stop hook and user-invocable manually.
user-invocable: true
allowed-tools: "Read Bash Grep Glob"
argument-hint: "[file-path or --all]"
---

# Dead Code Review

Find code that is defined but never used. The language's linter (Ruff for
Python, ESLint for JS/TS, golangci-lint for Go) already catches the
syntactic cases (unused imports, unused locals). This skill catches the
semantic cases the linter cannot see.

## Scope

- **Stop hook (automatic)** — analyzes files changed this turn via `git diff --name-only HEAD`
- **Manual invocation** — `$ARGUMENTS` is a file path or `--all` for a full-repo sweep

## What to look for

1. **Unused functions / methods** — defined but never called anywhere (excluding tests that test them)
2. **Unused classes / types** — defined but never instantiated or referenced
3. **Unused modules / files** — no other file imports from them
4. **Unreachable code** — lines after an unconditional return/throw, or inside always-false branches
5. **Stale TODO / FIXME / XXX comments** — reference removed symbols, deleted features, or plans that have moved on
6. **Orphaned test fixtures / helpers** — defined but no test uses them
7. **Dead imports from dead sources** — imports from a module that itself only exists to be imported (re-export chains)
8. **Dead branches** — conditional paths that can't be reached given earlier conditions
9. **Shadowed definitions** — a function/variable defined then immediately overwritten without being used

## Process

1. Read `.claude/whitelist.yaml` — accept entries under `dead_code:`.
2. Get changed files this turn:
   ```!
   cd "${CLAUDE_PROJECT_DIR:-.}" && git diff --name-only HEAD 2>/dev/null | head -30
   ```
3. For each changed source file:
   - Read the file
   - For every function/method/class defined, grep the whole repo for references
   - For every module, check if any other module imports from it
4. Flag anything that the change this turn made dead (e.g., "this refactor removed the only caller of `foo()` but the definition still exists").

## Output Format

```json
{
  "decision": "approve" | "block",
  "reason": "one-line if block",
  "findings": [
    {
      "file": "src/services/foo.<ext>",
      "symbol": "legacy_helper",
      "kind": "function" | "class" | "module" | "branch" | "todo",
      "severity": "high" | "medium" | "low",
      "issue": "Defined at line 42. No external callers.",
      "suggestion": "Delete — if intentionally kept, add to .claude/whitelist.yaml under dead_code."
    }
  ]
}
```

## Rules

- **Only BLOCK when this turn introduced dead code.** If the change this turn
  left a function unused (refactoring away its only caller), block with a
  suggestion to delete or update the caller.
- **Pre-existing dead code** → include as `low` severity warnings, but
  `decision: approve`. That's technical debt, not a regression.
- **Respect the whitelist.** Entries under `dead_code:` are explicitly kept
  (public API surface, plugin hooks, etc.).
- **Max 5 findings** — focus on highest severity.
- **Silent on clean code.**

## Language-specific false-positive guardrails

Adapt the guardrails below to the target stack. These examples are for Python
but the concept is the same elsewhere: symbols may appear dead to grep but
be consumed by runtime string-based registration, config files, or framework
auto-discovery.

**Python:**
- Pytest fixtures consumed by name via auto-discovery
- Celery tasks invoked by name string (`send_task("foo")`, not `foo.delay()`)
- Framework controllers / route handlers registered in the app factory
- SQLAlchemy model methods invoked via ORM relationship accessors
- `__all__` exports may be consumed externally

**TypeScript/JavaScript:**
- Express route handlers attached via `app.use(...)`
- React components referenced in routing tables or dynamically imported
- Package `exports` entries in package.json
- Decorators registered via metadata (NestJS, TypeORM)

**Go:**
- `init()` functions in packages (side effects on import)
- Interfaces satisfied implicitly
- `go:embed` directives that reference files

**Rust:**
- `#[no_mangle]` functions called from FFI
- `#[cfg]` blocks that are live for other targets
- Macros expanded at build time
