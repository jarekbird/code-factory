---
name: new-model
description: Create a new SQLAlchemy model following project conventions
disable-model-invocation: true
allowed-tools: "Write Read"
argument-hint: "[model-name]"
---

# Create New Model: $ARGUMENTS

Create a new SQLAlchemy model called `$0` following the project's conventions.

## Steps

1. Read the model template at `${CLAUDE_SKILL_DIR}/../engineer/templates/model.py.md`
2. Read existing models in `src/app/models/` for reference on current patterns
3. Create `src/app/models/$0.py` following the template:
   - Class name: PascalCase version of `$0`
   - Table name: snake_case plural of `$0`
   - Must inherit `AuditMixin, Base`
   - Use `mapped_column` with explicit types
   - Use UUID for foreign keys
4. Add the import to `src/app/models/__init__.py`
5. Confirm the model was created correctly

## Conventions
- All models inherit AuditMixin (provides id, created_at, updated_at)
- Use UUID primary keys
- Use String with max length for text fields
- Use ForeignKey with UUID for relationships
