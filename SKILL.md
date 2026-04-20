---
name: code-factory
description: Install an AI-assisted engineering code factory into the current project. Language and framework agnostic — researches the right tooling for the target stack and scaffolds skills, hooks, and static enforcement. Invoke with /code-factory.
disable-model-invocation: true
allowed-tools: "Read Write Bash Glob Grep Agent"
argument-hint: "[--update | --minimal]"
---

# Code Factory Installer

Install a three-layer AI-assisted engineering system into the current project:

1. **CLAUDE.md / engineer skill** — architecture conventions (advisory, project-specific)
2. **AI review skills** — complexity, SRP, DRY, meta-check (LLM review at Stop hook)
3. **Deterministic enforcement** — linter, formatter, architecture rules, import boundaries (always-on, blocking)

Plus: code embeddings for semantic DRY detection, whitelist for accepted violations, code factory skills for scaffolding new modules.

## Modes

- **Default** (no args) — full install. Detects language + framework, researches right tools, creates all files.
- **`--update`** — re-detect and update existing installations to match current state of the codebase
- **`--minimal`** — skip code embeddings (no voyage/pgvector setup). Useful if the project is too small to justify them.

## Phase 1: Detect the target stack

1. Identify the primary language:
   - Python: `pyproject.toml`, `requirements.txt`, `setup.py`
   - JavaScript/TypeScript: `package.json`
   - Go: `go.mod`
   - Rust: `Cargo.toml`
   - Java/Kotlin: `build.gradle`, `pom.xml`
   - Ruby: `Gemfile`
   - Elixir: `mix.exs`

2. Identify the framework (if any):
   - Python: Litestar, FastAPI, Django, Flask
   - TS: Next.js, NestJS, Express, Fastify, Hono
   - Go: Gin, Echo, Fiber, chi
   - Rust: axum, actix, rocket
   - Java: Spring Boot, Micronaut, Quarkus

3. Identify the package manager:
   - Python: uv, poetry, pip
   - JS: npm, pnpm, yarn, bun
   - Go: go modules
   - Rust: cargo

4. Identify testing framework already in use.

5. Write findings to `.claude/code-factory-stack.md` for reference.

## Phase 2: Research language-specific tooling

**You must use `/research`** (the multi-source research skill) to find current best-in-class tools for the target language. Do NOT guess. Research these:

1. **Linter + formatter** (fast, sub-second on edits):
   - What is the Ruff equivalent? (Python: ruff, TS: biome/eslint+prettier, Go: gofmt+golangci-lint, Rust: rustfmt+clippy, Ruby: rubocop, Java: checkstyle/spotless)

2. **Architecture enforcement** (layer/import rules):
   - What is the import-linter equivalent? (Python: import-linter, TS: dependency-cruiser/eslint-plugin-boundaries, Java: ArchUnit, Go: go-arch-lint/dep)

3. **Complexity rules** (cyclomatic, cognitive):
   - What rules exist in the linter for branches/statements/complexity?

4. **Testing**:
   - Standard testing framework + HTTP client for integration tests
   - Whether query-counting fixtures / N+1 detection tooling exists

5. **Duplicate detection** (beyond embeddings):
   - jscpd, PMD CPD equivalents

6. **Empirical Big O**:
   - bigO (Python), hyperfine (any), criterion (Rust), benchmark.js (JS)

## Phase 3: Install dependencies

Install the language-specific tools via the project's package manager. Never skip this — deterministic enforcement is the most important layer.

## Phase 4: Scaffold the factory files

Create the following in the target project (adapted per language):

### `.claude/skills/engineer/SKILL.md`
Project-specific architecture skill. See [templates/engineer.spec.md](templates/engineer.spec.md) for the required structure and placeholders. Uses `paths:` to auto-load when editing source files.

### `.claude/skills/complexity-check/SKILL.md`
**Copy as-is** from [templates/complexity-check.md](templates/complexity-check.md). Inside, substitute the linter invocation command with the language's equivalent (researched in Phase 2).

### `.claude/skills/srp-check/SKILL.md`
**Copy as-is** from [templates/srp-check.md](templates/srp-check.md). Language-independent — the check is pure LLM prompt.

### `.claude/skills/dry-check/SKILL.md`
**Copy as-is** from [templates/dry-check.md](templates/dry-check.md). Replace the hook script path in the skill body with the target language's script extension.

### `.claude/skills/benchmark/SKILL.md`
**Copy from** [templates/benchmark.md](templates/benchmark.md). Replace the bigO-specific example block with the language's equivalent benchmarking library (criterion for Rust, hyperfine for CLI, benchmark.js for JS, JMH for Java, go test -bench for Go).

### `.claude/skills/new-model/SKILL.md` and `.claude/skills/new-step/SKILL.md`
Code factory skills. See [templates/factory-skills.spec.md](templates/factory-skills.spec.md) for the abstract structure. Write language-appropriate versions; reference `references/python-litestar/new-model.md` for a concrete example.

### `.claude/whitelist.yaml`
**Copy as-is** from [templates/whitelist.yaml](templates/whitelist.yaml). YAML format is language-independent.

### `.claude/hooks/check-imports.<ext>`
Architecture enforcement script. See [templates/check-imports.spec.md](templates/check-imports.spec.md) for the interface contract. Write in whatever language fits the project. Reference `references/python-litestar/check-imports.sh`.

### `.claude/hooks/code_embeddings.<ext>`
Function extractor + voyage-code-3 indexer. See [templates/code-embeddings.spec.md](templates/code-embeddings.spec.md) for interface and schema. Use the target language's tree-sitter grammar. Reference `references/python-litestar/code_embeddings.py`.

### `.claude/hooks/whitelist.<ext>`
Whitelist loader (reads `.claude/whitelist.yaml`). Simple utility — use whatever language fits. Reference `references/python-litestar/whitelist.py`.

### `.claude/settings.json`
Hook wiring. See [templates/settings.spec.md](templates/settings.spec.md) for structure and per-language command substitutions. Reference `references/python-litestar/settings.json`.

### Project-level config
Add linter config with the research-recommended rules (complexity, unused imports, formatting) to the project's standard config file (`pyproject.toml`, `package.json`, `.eslintrc`, `golangci.yml`, `Cargo.toml`, etc.).
Add architecture rule config (import-linter contracts, dependency-cruiser config, ArchUnit tests, etc.).

## Phase 5: Verify

Run all static checks on the existing codebase:
- Linter: report any findings but don't block installation
- Architecture rules: report violations, ask user to fix or whitelist
- Run any existing tests to confirm we didn't break the toolchain

## Phase 6: Update CLAUDE.md

If `CLAUDE.md` exists, append or update:
- Reference to `.claude/skills/engineer/SKILL.md`
- Reference to the code-factory tooling
- Key commands added (uv, npm, go, etc.)

If not, create a minimal one.

## Dependencies

Required API keys:
- **`VOYAGE_API_KEY`** — for code embeddings (skip with `--minimal`)

Required local tools:
- `git`
- Language-specific package manager (detected in Phase 1)
- `jq` (for hook JSON parsing)
- For Python: `pgvector` extension on Postgres (if using embeddings)

## When to Use

- Starting a new project — full install
- Joining an existing project — `/code-factory` to bootstrap AI tooling
- After a major refactor — `/code-factory --update` to re-sync

## Philosophy

The three layers are complementary:
- **CLAUDE.md + engineer skill**: advisory knowledge. LLM reads and follows (usually).
- **AI check skills**: LLM review layer. Catches judgment-call issues (SRP, algorithmic intent).
- **Deterministic enforcement**: shell/lint scripts that cannot be ignored. Catches mechanical violations.

Each layer is necessary. None is sufficient alone. CLAUDE.md alone = hoping Claude remembers. Linters alone = no judgment. AI reviews alone = no hard guarantees.

## Reference Implementation

The first implementation was for a Python/Litestar project at `/Users/jarekbird/aprative/electrical-floorplan-back`. You can read its `.claude/` directory as a complete working example before adapting to a new language.
