# Code Embeddings Hook Specification (language-agnostic)

Generate a script that powers the embedding-based DRY check. The script has two subcommands:

## Subcommands

### `embed <file_path>`
- Parse the source file and extract named symbols (functions, methods, classes)
- For each symbol, compute a content hash (sha256 of the source text)
- Compare against the stored hash. If unchanged, skip.
- For changed symbols, batch-call the **voyage-code-3** embedding model (via the voyage-python or voyage-node SDK, or direct HTTPS call)
- Store the embedding, role (layer tag), and content in the `code_embeddings` table
- Output JSON: `{"embedded": <count>}`

### `query <file_path> <symbol_name>`
- Look up the symbol's embedding
- Perform a cosine-similarity KNN search against the rest of the table (excluding the symbol itself)
- Return the top N (default 5) matches where similarity ≥ 0.90
- Output JSON list of `{file_path, symbol_name, role, similarity, content_preview}`

## Language-specific adapters

- **Symbol extraction**: use the target language's AST or tree-sitter grammar
  - Python: tree-sitter-python + `function_definition` / `class_definition` nodes
  - TS/JS: tree-sitter-typescript / typescript compiler API
  - Go: go/ast + inspect FuncDecl/GenDecl
  - Rust: syn crate or tree-sitter-rust
  - Java: JavaParser or tree-sitter-java

- **Vector store**: use what's available
  - If Postgres is already a dep: pgvector with HNSW index
  - Otherwise: sqlite-vss, chroma, or a flat file with numpy

- **Implementation language**: whatever is already in the project's toolchain. Python is fine if Python is already a dep, otherwise use the project's native language. The script just needs to be executable from a shell hook.

## Role tagging

When storing an embedding, tag it with the layer it came from (based on file path):
- `api` — controllers, handlers, routers
- `service` — business logic + DB access
- `engine` — pure computation modules
- `model` — ORM entities
- `worker` — background jobs
- `test` — test code

The DRY-check skill uses this to filter (don't flag test↔test similarity, cross-role matches are stronger signals, etc.).

## Reference implementation

See `references/python-litestar/code_embeddings.py` for a working Python version with tree-sitter-python, voyageai SDK, and pgvector.

## Schema

```sql
CREATE TABLE code_embeddings (
    id UUID PRIMARY KEY,
    file_path TEXT NOT NULL,
    symbol_name TEXT NOT NULL,
    symbol_kind TEXT NOT NULL,  -- function | method | class
    role TEXT,                  -- api | service | engine | model | worker | test
    content_hash TEXT NOT NULL,
    content TEXT NOT NULL,
    embedding VECTOR(1024) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (file_path, symbol_name)
);
CREATE INDEX ON code_embeddings USING hnsw (embedding vector_cosine_ops);
```

## Dependencies

- `VOYAGE_API_KEY` environment variable
- 1024-dim output from voyage-code-3 (int8 quantization optional for storage)
