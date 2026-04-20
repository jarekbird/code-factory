# Code Factory — Claude Code Skill

A language- and framework-agnostic **Claude Code skill** that installs a complete AI-assisted engineering system into any project.

**Invoke with `/code-factory`** in Claude Code after dropping this into `~/.claude/skills/code-factory/`.

## What it installs

Three layers of enforcement in any project:

1. **CLAUDE.md + `engineer` skill** — architecture conventions, advisory
2. **AI review skills** — LLM-based checks on every Claude response Stop:
   - `complexity-check` — static linter rules + LLM Big O reasoning
   - `srp-check` — Single Responsibility Principle review
   - `dry-check` — semantic duplication via voyage-code-3 embeddings + pgvector
   - `benchmark` — empirical complexity verification (manual)
3. **Deterministic hooks** — shell/script enforcement that can't be ignored:
   - PreToolUse: architecture boundary check (e.g. engine can't import ORM)
   - PostToolUse: auto-format + lint-fix, async embedding index update
   - Stop: runs the 4 AI check agents

Plus:
- `.claude/whitelist.yaml` for accepted violations (complexity/SRP/DRY)
- Code factory skills (`new-model`, `new-step`) for scaffolding
- voyage-code-3 semantic duplicate detection

## Structure

```
code-factory/
├── SKILL.md                    # The installer (6-phase workflow)
├── templates/                  # Language-agnostic specs + skills
│   ├── benchmark.md
│   ├── check-imports.spec.md
│   ├── code-embeddings.spec.md
│   ├── complexity-check.md
│   ├── dry-check.md
│   ├── engineer.spec.md
│   ├── factory-skills.spec.md
│   ├── settings.spec.md
│   ├── srp-check.md
│   └── whitelist.yaml
└── references/                 # Concrete implementations
    └── python-litestar/        # Full working Python/Litestar example
        ├── check-imports.sh
        ├── code_embeddings.py
        ├── engineer.md
        ├── new-model.md
        ├── new-step.md
        ├── settings.json
        └── whitelist.py
```

**Spec files vs. concrete files:**
- `templates/*.spec.md` describe WHAT to build (language-agnostic)
- `templates/*.md` (check skills + whitelist.yaml) are pure LLM prompts or format definitions — copy as-is
- `references/<stack>/` are concrete working examples to pattern-match from

## Install

```bash
git clone https://github.com/jarekbird/code-factory.git ~/.claude/skills/code-factory
```

## Requirements

- **Claude Code** (Anthropic CLI)
- **`/research` skill** (for language-specific tool discovery) — part of the personal-assistant plugin, or any multi-source search skill
- **VOYAGE_API_KEY** env var (for the DRY check; [voyage.ai](https://voyage.ai))
- Language-specific package manager (detected per project)
- For embeddings: Postgres + pgvector if using the reference Python implementation

## Usage

In any project:

```
/code-factory              # Fresh install
/code-factory --update     # Re-sync after code changes
/code-factory --minimal    # Skip embeddings setup
```

The installer:
1. Detects language + framework
2. Uses `/research` to find language-specific equivalents of Ruff, import-linter, tree-sitter grammars, and voyage-code-3 integrations
3. Scaffolds `.claude/skills/`, `.claude/hooks/`, and `.claude/settings.json` in the target project
4. Installs dependencies via the project's package manager
5. Verifies by running static checks

## Adding a new reference implementation

When installing on a new stack (TS/Go/Rust/etc.), after verification, copy the generated files back into `references/<stack>/` and PR — helps the next install of the same stack skip the research phase.

## License

MIT
