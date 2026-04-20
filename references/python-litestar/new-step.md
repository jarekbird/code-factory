---
name: new-step
description: Scaffold a new pipeline step with model, service, controller, and engine module
disable-model-invocation: true
allowed-tools: "Write Read Bash(mkdir *)"
argument-hint: "[step-name]"
---

# Scaffold Pipeline Step: $ARGUMENTS

Create all files for a new pipeline step called `$0`.

## Steps

1. Read the templates in `${CLAUDE_SKILL_DIR}/../engineer/templates/`
2. Read existing implementations for reference:
   - `src/app/models/project.py` (model pattern)
   - `src/app/services/project_service.py` (service pattern)
   - `src/app/api/projects.py` (controller pattern)

3. Create the following files:

### Model
- `src/app/models/$0.py` — following model template
- Add import to `src/app/models/__init__.py`

### Service
- `src/app/services/$0_service.py` — following service template
- Must call engine/ for computation, persist results to DB

### Controller
- `src/app/api/$0s.py` — following controller template
- CRUD endpoints + approve endpoint for pipeline step
- Register in `src/app/main.py` route_handlers

### Engine module
- `src/app/engine/$0s/` — create directory with `__init__.py`
- Add placeholder module files as needed
- Remember: NO database or framework imports in engine/

4. Verify all files follow conventions:
   - Model inherits AuditMixin
   - Controller delegates to service
   - Service is the only DB layer
   - Engine is pure computation
