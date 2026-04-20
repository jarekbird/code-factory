# Engineer Skill Specification (language-agnostic)

When generating the project's `.claude/skills/engineer/SKILL.md`, produce a skill with this structure. Fill in the `{PLACEHOLDERS}` based on what you detected and researched about the target codebase.

## Required frontmatter

```yaml
---
name: engineer
description: Architecture conventions for {PROJECT_NAME}. Enforces layer boundaries, pipeline flow, and coding standards. Auto-loads when editing source files.
user-invocable: false
paths: "{SOURCE_GLOB}"  # e.g., "src/**/*.py", "src/**/*.ts", "**/*.go"
---
```

## Required sections (adapt content to target stack)

### 1. Introduction
One paragraph identifying the project, its stack (language, framework, DB, package manager), and stating conventions are strict.

### 2. Layer Boundaries
Diagram of the dependency arrow (`A → B → C`). Describe each layer in one bullet, including which languages/imports belong and which don't. Enforcement is via static tools (import-linter, dependency-cruiser, ArchUnit, etc.) — name the tool used.

### 3. Pipeline / Data Flow (if applicable)
If the project has a multi-step pipeline, document the flow and the pause/approval points. If not, skip this section.

### 4. Sub-module Layout
List the sub-folders or packages within each layer and what they contain.

### 5. Model / Entity Conventions
- Base class or mixin every model inherits (if the ORM supports mixins)
- ID type (UUID vs auto-increment)
- Audit fields
- Soft delete pattern (if used)

### 6. Service Conventions
- What makes a well-designed service in this project
- Logging library + context required
- DB session handling

### 7. Controller/Handler Conventions
- Thin handlers: parse, delegate, return
- Endpoint versioning prefix
- Dependency injection style

### 8. Worker/Job Conventions (if async jobs exist)
- Task framework (Celery, Bull, Sidekiq, go-task, etc.)
- Fan-out patterns
- Retry/ack semantics

### 9. Testing Conventions
- Test framework + HTTP client for integration tests
- Directory layout (unit/integration/perf)
- Required fixtures (DB rollback, test client, query counter)
- When to write tests (service/endpoint/engine functions must all be tested)

### 10. Performance Awareness
- Common anti-patterns in this language (e.g., N+1 for ORMs, append-in-loop vs comprehension)
- When to use spatial indices, hashmaps, prefix sums
- Reference to `/benchmark` skill for hard data
- Whitelist file location for accepted complexity

### 11. Research and References
- Directive: use `/research` for unfamiliar patterns
- List of reference repos or internal docs to consult (with "don't copy blindly" caveat)

### 12. Scripts vs Skills
Include a rule that ad-hoc wrapper scripts around the API are forbidden. If a
task would benefit from driving multiple API calls in sequence (testing,
debugging, batch operations), propose a Claude Code skill instead and ask the
user before building it. Skills are discoverable, composable, and version-
controlled; throwaway scripts get rewritten every time. One-shot shell
commands are fine; *sequences* should become skills.

### 13. DO NOT list
A short list of forbidden patterns specific to this project's architecture,
including "no ad-hoc API wrapper scripts — propose a skill instead".
