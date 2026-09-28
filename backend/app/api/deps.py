"""Shared helpers for route handlers."""
from fastapi import HTTPException

from app import storage
from app.errors import NotFoundError
from app.utils import sanitize_name


def get_repo_id(repository: str) -> str:
    try:
        return sanitize_name(repository)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid repository identifier.")


def require_analysis(repository: str) -> tuple[str, dict]:
    """Return (repo_id, saved analysis) or raise a 404 asking the user to analyze first."""
    repo_id = get_repo_id(repository)
    data = storage.load_analysis(repo_id)
    if data is None:
        raise NotFoundError(f"Repository '{repo_id}' has not been analyzed yet. Analyze it first.")
    return repo_id, data
