"""Code embedding utility — extracts functions via tree-sitter, embeds with voyage-code-3.

Invoked by hooks after file edits. Keeps the code_embeddings table up to date
so the dry-check hook can query for semantic duplicates.

Usage:
    python .claude/hooks/code_embeddings.py embed <file_path>
    python .claude/hooks/code_embeddings.py query <file_path> <symbol_name>
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path

# Make src/ importable
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from dotenv import load_dotenv

load_dotenv(PROJECT_ROOT / ".env")

import tree_sitter_python
import voyageai
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from tree_sitter import Language, Parser

from app import config
from app.models.code_embedding import CodeEmbedding

PY_LANGUAGE = Language(tree_sitter_python.language())
parser = Parser(PY_LANGUAGE)

_voyage_client = None


def get_voyage_client() -> voyageai.Client:
    global _voyage_client
    if _voyage_client is None:
        _voyage_client = voyageai.Client(api_key=config.VOYAGE_API_KEY)
    return _voyage_client


def get_db_session():
    engine = create_engine(config.DATABASE_URL, echo=False)
    return sessionmaker(bind=engine)()


def _role_from_path(file_path: str) -> str | None:
    """Tag embeddings with the layer they live in, so DRY checks can filter."""
    path = file_path.replace("\\", "/")
    if "/src/app/api/" in path:
        return "api"
    if "/src/app/services/" in path:
        return "service"
    if "/src/app/engine/" in path:
        return "engine"
    if "/src/app/models/" in path:
        return "model"
    if "/src/app/workers/" in path:
        return "worker"
    if "/tests/" in path:
        return "test"
    return None


def extract_symbols(source: str) -> list[dict]:
    """Extract functions, methods, and classes from Python source using tree-sitter.

    Returns a list of dicts: {name, kind, content, start_line, end_line}.
    """
    tree = parser.parse(source.encode("utf-8"))
    root = tree.root_node
    symbols = []

    def visit(node, class_name=None):
        if node.type == "function_definition":
            name_node = node.child_by_field_name("name")
            if name_node is None:
                return
            symbol_name = name_node.text.decode("utf-8")
            full_name = f"{class_name}.{symbol_name}" if class_name else symbol_name
            kind = "method" if class_name else "function"
            content = node.text.decode("utf-8")
            symbols.append({
                "name": full_name,
                "kind": kind,
                "content": content,
                "start_line": node.start_point[0] + 1,
                "end_line": node.end_point[0] + 1,
            })
        elif node.type == "class_definition":
            name_node = node.child_by_field_name("name")
            if name_node is None:
                return
            cls_name = name_node.text.decode("utf-8")
            content = node.text.decode("utf-8")
            symbols.append({
                "name": cls_name,
                "kind": "class",
                "content": content,
                "start_line": node.start_point[0] + 1,
                "end_line": node.end_point[0] + 1,
            })
            # Visit children for methods, with class context
            for child in node.children:
                visit(child, class_name=cls_name)
            return

        for child in node.children:
            visit(child, class_name=class_name)

    visit(root)
    return symbols


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Call voyage-code-3 to embed a batch of code texts."""
    client = get_voyage_client()
    result = client.embed(
        texts,
        model="voyage-code-3",
        input_type="document",
        output_dimension=1024,
    )
    return result.embeddings


def embed_file(file_path: str) -> int:
    """Extract symbols from a file, embed them, upsert to DB. Returns count updated."""
    path = Path(file_path).resolve()
    if not path.exists() or not str(path).endswith(".py"):
        return 0

    source = path.read_text(encoding="utf-8")
    symbols = extract_symbols(source)
    if not symbols:
        return 0

    role = _role_from_path(str(path))
    rel_path = str(path.relative_to(PROJECT_ROOT))

    session = get_db_session()
    try:
        # Get existing embeddings for this file to check hashes
        stmt = select(CodeEmbedding).where(CodeEmbedding.file_path == rel_path)
        existing = {e.symbol_name: e for e in session.execute(stmt).scalars()}

        to_embed = []
        for sym in symbols:
            h = hashlib.sha256(sym["content"].encode("utf-8")).hexdigest()
            existing_row = existing.get(sym["name"])
            if existing_row and existing_row.content_hash == h:
                continue  # unchanged
            to_embed.append((sym, h))

        if not to_embed:
            return 0

        # Batch embed
        texts = [
            f"# {rel_path}\n# {sym['kind']}: {sym['name']}\n\n{sym['content']}"
            for sym, _ in to_embed
        ]
        embeddings = embed_texts(texts)

        count = 0
        for (sym, h), emb in zip(to_embed, embeddings, strict=True):
            existing_row = existing.get(sym["name"])
            if existing_row:
                existing_row.content = sym["content"]
                existing_row.content_hash = h
                existing_row.embedding = emb
                existing_row.symbol_kind = sym["kind"]
                existing_row.role = role
            else:
                new = CodeEmbedding(
                    file_path=rel_path,
                    symbol_name=sym["name"],
                    symbol_kind=sym["kind"],
                    role=role,
                    content_hash=h,
                    content=sym["content"],
                    embedding=emb,
                )
                session.add(new)
            count += 1

        session.commit()
        return count
    finally:
        session.close()


def query_similar(
    file_path: str,
    symbol_name: str,
    top_k: int = 5,
    min_similarity: float = 0.90,
) -> list[dict]:
    """Find existing code similar to a given symbol. Returns list of
    {file_path, symbol_name, role, similarity, content_preview}.
    """
    rel_path = str(Path(file_path).resolve().relative_to(PROJECT_ROOT))
    session = get_db_session()
    try:
        target = session.execute(
            select(CodeEmbedding).where(
                CodeEmbedding.file_path == rel_path,
                CodeEmbedding.symbol_name == symbol_name,
            )
        ).scalar_one_or_none()

        if target is None:
            return []

        # Find nearest neighbors (excluding self)
        distance = CodeEmbedding.embedding.cosine_distance(target.embedding)
        stmt = (
            select(CodeEmbedding, distance.label("distance"))
            .where(
                ~(
                    (CodeEmbedding.file_path == rel_path)
                    & (CodeEmbedding.symbol_name == symbol_name)
                )
            )
            .order_by(distance)
            .limit(top_k)
        )
        results = []
        for row, dist in session.execute(stmt).all():
            similarity = 1.0 - float(dist)
            if similarity < min_similarity:
                continue
            results.append({
                "file_path": row.file_path,
                "symbol_name": row.symbol_name,
                "role": row.role,
                "similarity": round(similarity, 4),
                "content_preview": row.content[:500],
            })
        return results
    finally:
        session.close()


def main():
    if len(sys.argv) < 2:
        print("usage: code_embeddings.py embed <file> | query <file> <symbol>")
        sys.exit(1)

    cmd = sys.argv[1]
    if cmd == "embed":
        if len(sys.argv) < 3:
            print("usage: code_embeddings.py embed <file>")
            sys.exit(1)
        count = embed_file(sys.argv[2])
        print(json.dumps({"embedded": count}))
    elif cmd == "query":
        if len(sys.argv) < 4:
            print("usage: code_embeddings.py query <file> <symbol>")
            sys.exit(1)
        results = query_similar(sys.argv[2], sys.argv[3])
        print(json.dumps(results, indent=2))
    else:
        print(f"unknown command: {cmd}")
        sys.exit(1)


if __name__ == "__main__":
    main()
