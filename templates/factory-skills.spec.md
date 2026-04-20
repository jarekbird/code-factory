# Code Factory Skills Specification (language-agnostic)

Generate user-invocable skills that scaffold common artifacts in the target project. Adapt each to the detected stack (ORM, controller framework, test framework).

## `new-model/SKILL.md`

```yaml
---
name: new-model
description: Create a new {ORM_NAME} model following project conventions
disable-model-invocation: true
allowed-tools: "Write Read"
argument-hint: "[model-name]"
---
```

Steps the skill should perform:
1. Read the model template and existing models for reference
2. Create `<models_dir>/<name>.<ext>` with:
   - Correct class name (PascalCase) and table/collection name (snake_case plural)
   - Inherits the project's base/audit mixin
   - Explicit typed fields
   - Proper ID type (UUID, auto-inc, etc.) per convention
3. Register in the models index (if the project has one)
4. Confirm no architecture violations

## `new-step/SKILL.md` (only if the project has a pipeline)

```yaml
---
name: new-step
description: Scaffold a new pipeline step (model + service + controller + engine module)
disable-model-invocation: true
allowed-tools: "Write Read Bash(mkdir *)"
argument-hint: "[step-name]"
---
```

Steps:
1. Create model, service, controller, and engine sub-module
2. Each follows layer conventions (thin controller, service does DB, engine is pure)
3. Register controller routes in the app factory
4. Add a placeholder test file under `tests/integration/` or equivalent

## Other factory skills to consider (stack-dependent)

- `new-endpoint` — just a controller + service pair, no model
- `new-worker` — new background job (Celery/Sidekiq/Bull/etc.)
- `new-migration` — new DB migration file
- `new-test` — scaffold a test file matching an existing source file

## Reference implementations

See `references/python-litestar/new-model.md` and `references/python-litestar/new-step.md` for Python/Litestar examples.

## Template files

Put per-artifact templates under `.claude/skills/engineer/templates/` in the target project (e.g., `model.<ext>.md`, `service.<ext>.md`, `controller.<ext>.md`). These are the actual code shapes the factory skills reference.
