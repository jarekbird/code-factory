"""Whitelist loader for AI checks.

Loads .claude/whitelist.yaml and provides a simple API:
    from whitelist import is_whitelisted
    if is_whitelisted("complexity", file_path, function_name):
        skip
"""

from __future__ import annotations

import fnmatch
from pathlib import Path
from typing import Any

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[2]
WHITELIST_PATH = PROJECT_ROOT / ".claude" / "whitelist.yaml"


_cache: dict[str, Any] | None = None


def load_whitelist() -> dict[str, Any]:
    global _cache
    if _cache is not None:
        return _cache
    if not WHITELIST_PATH.exists():
        _cache = {}
        return _cache
    with WHITELIST_PATH.open() as f:
        data = yaml.safe_load(f) or {}
    _cache = data
    return data


def _matches(entry: dict, file_path: str, function_name: str | None) -> bool:
    # Match by path (exact or glob)
    entry_path = entry.get("path")
    entry_pattern = entry.get("pattern")
    entry_fn = entry.get("function")

    path_ok = True
    if entry_path:
        path_ok = file_path == entry_path or file_path.endswith("/" + entry_path)
    elif entry_pattern:
        path_ok = fnmatch.fnmatch(file_path, entry_pattern)

    if not path_ok:
        return False

    # Match by function if specified
    if entry_fn and function_name != entry_fn:
        return False

    return True


def is_whitelisted(check: str, file_path: str, function_name: str | None = None) -> bool:
    """Check if a (check, file_path, function_name) tuple is whitelisted."""
    wl = load_whitelist()
    entries = wl.get(check, []) or []
    return any(_matches(e, file_path, function_name) for e in entries)


def reason(check: str, file_path: str, function_name: str | None = None) -> str | None:
    """Get the whitelist reason for a match, if any."""
    wl = load_whitelist()
    entries = wl.get(check, []) or []
    for e in entries:
        if _matches(e, file_path, function_name):
            return e.get("reason", "(no reason provided)")
    return None
