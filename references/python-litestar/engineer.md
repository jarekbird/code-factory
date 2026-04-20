---
name: engineer
description: Architecture conventions for electrical-floorplan-back. Enforces layer boundaries, pipeline flow, and coding standards. Auto-loads when editing Python files.
user-invocable: false
paths: "src/**/*.py"
---

# Engineering Conventions

You are working on **electrical-floorplan-back**, a Python API backend for electrical floor plan symbol detection. Follow these conventions strictly.

## Layer Boundaries (strict, enforced by hooks)

```
api/ → services/ → engine/
```

- **api/** — Controllers. Thin. Parse request, delegate to service, return response. NO business logic, NO direct DB queries, NO SQLAlchemy imports.
- **services/** — Business logic + DB access. Orchestrates engine calls and persists results. The ONLY layer that touches the database.
- **engine/** — Pure computation. ZERO imports from `sqlalchemy`, `litestar`, `celery`, `app.models`, or `app.services`. Takes inputs (dicts, lists, arrays), returns outputs. Internal only.
- **models/** — SQLAlchemy ORM models. All must inherit `AuditMixin` from `app.models.base`.
- **workers/** — Celery task definitions. Thin wrappers that call services. No business logic.

## Pipeline Flow (Human-in-the-Loop)

Every step writes results to DB, then **pauses for human/AI review and approval**. No auto-progression.

```
Upload → [pause] → Region Extraction → [pause] → Legend Extraction → [pause] → Floorplan Matching → [pause] → (Circuitry Building - future)
```

Pipeline status values per step:
- `uploaded`
- `regions_pending` → `regions_extracted` → `regions_approved`
- `legend_pending` → `legend_extracted` → `legend_approved`
- `matching_pending` → `matching_complete` → `matching_approved`

## Engine Sub-modules

Each pipeline step has its own sub-folder under `engine/`:
- `engine/regions/` — Region extraction algorithm
- `engine/legends/` — Legend extraction + signature building
- `engine/matching/` — Segment graph, walker, seed candidates, scoring, NMS
- `engine/circuitry/` — Future: circuit path building
- `engine/pdf.py` — Shared PDF parsing (PyMuPDF)

## Model Conventions

- All models inherit `AuditMixin` (provides `id`, `created_at`, `updated_at`)
- All editable pipeline data must support revision history
- Use UUID primary keys
- Use `mapped_column` with explicit types

## Service Conventions

- Services are the ONLY layer that touches the database
- Each service corresponds to a pipeline step or domain object
- Services call into `engine/` for computation, then persist results
- Use structlog for logging with context (project_id, etc.)

## Controller Conventions

- Controllers are thin: parse input, call service, return response
- All endpoints under `/api/v1/`
- Each pipeline step has CRUD + approve endpoints
- Use Litestar dependency injection for DB sessions

## Worker Conventions

- Tasks are thin wrappers calling services
- Fan out per-page tasks via `celery.group()` for matching
- Configure `task_acks_late=True` for reliability

## Testing Conventions

- **Framework**: pytest + httpx + Litestar TestClient
- **Directory**: `tests/` at project root, mirroring `src/app/` structure
  - `tests/unit/` — unit tests for services, engine modules
  - `tests/integration/` — API endpoint tests with real DB
  - `tests/perf/` — performance / Big O verification (bigO decorator)
- **Naming**: `test_<module>.py` matching the module being tested
- **What to test**:
  - Every service function — unit test with isolated DB
  - Every API endpoint — integration test covering happy path + error cases
  - Every engine function — unit test with known inputs/outputs
- **Fixtures** (from `tests/conftest.py`):
  - `db` — isolated test DB session that rolls back after each test
  - `client` — Litestar TestClient
  - `query_count` — context manager that counts SQL queries; use `assert query_count < N` on endpoint tests to catch N+1 queries
- **When writing new code, write the test alongside it.** Don't skip tests on the grounds of speed.

## Performance Awareness

Think about performance when writing code. Flag your own code for review if it:
- Contains nested loops over the same collection (potential O(n²))
- Iterates to find something when a dict/set lookup would work
- Does SQLAlchemy relationship access inside a loop (N+1 — use `selectinload` or `joinedload`)
- Calls `list.append` inside a loop instead of using a comprehension
- Does all-pairs geometric comparison instead of spatial indices (KD-tree, R-tree)
- Adds a filter on a column that has no index

Some algorithms are inherently expensive (graph matching, turning function alignment). That's fine — note them with a comment explaining why, and add to `.claude/whitelist.yaml` if applicable. The AI checks will respect the whitelist.

For hot paths, add a `tests/perf/test_<module>.py` that uses the `bigO` decorator to verify empirical complexity.

## Research and References

- **When stuck, use `/research`** instead of guessing. Especially for library API usage, architecture patterns, or infrastructure decisions.
- **Aperture repo at `/Users/jarekbird/aprative/aperture`** can be read for reference, especially `packages/detector/` for detection algorithms:
  - `packages/detector/detector/primitive_reconstruction.py` — turning function, segment graph, walker
  - `packages/detector/detector/graph_match.py` — seed candidates, scoring, compound filter
  - `packages/detector/detector/legend.py` — legend extraction
  - `packages/detector/detector/geometric_matcher.py` — NMS, wall detection

  **Do NOT copy code blindly.** Aperture accumulated experimental paths and tech debt. Understand patterns, then rewrite cleanly.

## DO NOT

- Put business logic in controllers
- Import DB/SQLAlchemy/Litestar/Celery in engine/
- Skip the service layer (controller → engine directly)
- Auto-progress the pipeline without approval
- Hard delete records
- Use raw SQL in application code
- Generate code from scratch when templates exist in `.claude/skills/engineer/templates/`
