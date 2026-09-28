"""Small helpers: name sanitizing and path-traversal protection."""
import re
from pathlib import Path


def sanitize_name(value: str) -> str:
    """Turn arbitrary text into a safe identifier ([A-Za-z0-9_-] only)."""
    cleaned = re.sub(r"[^A-Za-z0-9_-]", "_", (value or "").strip())
    cleaned = re.sub(r"_+", "_", cleaned).strip("_-")
    if not cleaned:
        raise ValueError("Identifier is empty after sanitizing.")
    return cleaned[:60]


def make_repo_id(owner: str, repo: str) -> str:
    """psf + requests -> psf_requests"""
    return sanitize_name(f"{owner}_{repo}")


def collection_name(repo_id: str) -> str:
    """ChromaDB collection name (3-63 chars, alphanumeric at both ends)."""
    name = f"repo_{sanitize_name(repo_id)}"[:63]
    return name.rstrip("_-")


def is_safe_relative_path(path: str) -> bool:
    """Reject absolute paths, drive letters, backslashes and '..' segments."""
    if not path or path.startswith("/") or "\\" in path or ":" in path or "\x00" in path:
        return False
    return ".." not in path.split("/")


def safe_join(base: Path, relative: str) -> Path:
    """Join base + relative and make sure the result stays inside base."""
    base_resolved = base.resolve()
    target = (base_resolved / relative).resolve()
    if target != base_resolved and base_resolved not in target.parents:
        raise ValueError("Path traversal detected.")
    return target
