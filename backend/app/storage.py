"""Filesystem storage: cached source files and the saved analysis of each repository."""
import json
import logging
import os
import shutil
from pathlib import Path
from typing import Optional

from app.config import settings
from app.utils import safe_join, sanitize_name

logger = logging.getLogger("repopilot.storage")


def repo_dir(repo_id: str) -> Path:
    return safe_join(settings.REPOS_DIR, sanitize_name(repo_id))


def files_dir(repo_id: str) -> Path:
    return repo_dir(repo_id) / "files"


def _analysis_file(repo_id: str) -> Path:
    return repo_dir(repo_id) / "analysis.json"


def save_analysis(repo_id: str, data: dict) -> None:
    folder = repo_dir(repo_id)
    folder.mkdir(parents=True, exist_ok=True)
    tmp = folder / "analysis.json.tmp"
    tmp.write_text(json.dumps(data), encoding="utf-8")
    os.replace(tmp, _analysis_file(repo_id))  # atomic replace


def load_analysis(repo_id: str) -> Optional[dict]:
    path = _analysis_file(repo_id)
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print("REPOPILOT ERROR:", repr(exc))
        logger.error("Could not read saved analysis for %s: %r", repo_id, exc)
        return None


def read_cached_file(repo_id: str, relative_path: str) -> Optional[str]:
    try:
        path = safe_join(files_dir(repo_id), relative_path)
    except ValueError:
        return None
    if not path.is_file():
        return None
    return path.read_text(encoding="utf-8", errors="replace")


def clear_file_cache(repo_id: str) -> None:
    shutil.rmtree(files_dir(repo_id), ignore_errors=True)


def delete_repository_files(repo_id: str) -> bool:
    folder = repo_dir(repo_id)
    if not folder.exists():
        return False
    shutil.rmtree(folder, ignore_errors=True)
    return True


def list_repositories() -> list[dict]:
    items: list[dict] = []
    if not settings.REPOS_DIR.exists():
        return items
    for folder in sorted(settings.REPOS_DIR.iterdir()):
        if not folder.is_dir():
            continue
        data = load_analysis(folder.name)
        if not data:
            continue
        info = data.get("repository", {})
        items.append({
            "repository_id": folder.name,
            "full_name": info.get("full_name", folder.name),
            "description": info.get("description"),
            "stars": info.get("stars", 0),
            "analyzed_at": data.get("analyzed_at"),
            "indexed_chunks": data.get("rag", {}).get("indexed_chunks", 0),
        })
    return items
