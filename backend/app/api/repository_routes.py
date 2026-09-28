import logging

from fastapi import APIRouter, HTTPException, Query

from app import pipeline, progress, storage
from app.api.deps import get_repo_id, require_analysis
from app.config import settings
from app.errors import AppError, NotFoundError
from app.rag import retriever, vector_store
from app.schemas.repository import AnalyzeRequest, AnalyzeResponse, SearchRequest, SearchResponse
from app.utils import is_safe_relative_path

logger = logging.getLogger("repopilot.routes")
router = APIRouter(prefix="/api", tags=["repository"])


@router.post("/repository/analyze", response_model=AnalyzeResponse)
def analyze_repository(req: AnalyzeRequest):
    """Download, analyze, chunk, embed and index a public GitHub repository."""
    try:
        return pipeline.analyze_repository(req.url, req.progress_id, req.force_refresh)
    except AppError:
        raise  # already user-friendly; main.py turns it into JSON
    except Exception as e:
        print("REPOPILOT ERROR:", repr(e))
        logger.exception("Repository analysis failed")
        raise HTTPException(status_code=500, detail="Repository analysis failed. Check backend logs.")


@router.get("/progress/{progress_id}")
def get_progress(progress_id: str):
    return progress.get(progress_id)


@router.get("/repositories")
def list_repositories():
    return {"repositories": storage.list_repositories()}


@router.post("/repository/search", response_model=SearchResponse)
def search_repository(req: SearchRequest):
    repo_id, _ = require_analysis(req.repository)
    results = retriever.retrieve(repo_id, req.query, req.top_k or settings.TOP_K_RESULTS)
    return {"repository": repo_id, "query": req.query, "results": results}


@router.get("/repository/{repository}", response_model=AnalyzeResponse)
def get_repository(repository: str):
    _, data = require_analysis(repository)
    data["from_cache"] = True
    return data


@router.get("/repository/{repository}/graph")
def get_graph(repository: str):
    _, data = require_analysis(repository)
    return data["dependency_graph"]


@router.get("/repository/{repository}/complexity")
def get_complexity(repository: str):
    _, data = require_analysis(repository)
    return data["complexity"]


@router.get("/repository/{repository}/architecture")
def get_architecture(repository: str):
    _, data = require_analysis(repository)
    return data["architecture"]


@router.get("/repository/{repository}/file")
def get_file(repository: str, path: str = Query(..., min_length=1)):
    """Source of an analyzed file (from the local cache) with its analysis and complexity."""
    repo_id, data = require_analysis(repository)
    if not is_safe_relative_path(path):
        raise HTTPException(status_code=400, detail="Invalid file path.")
    info = next((a for a in data["code_analysis"] if a["file"] == path), None)
    if info is None:
        raise NotFoundError("That file was not part of the analysis.")
    content = storage.read_cached_file(repo_id, path)
    if content is None:
        raise NotFoundError("The source file is no longer in the local cache. Re-analyze the repository.")
    cx = next((c for c in data["complexity"]["files"] if c["file"] == path), None)
    return {"file": path, "language": info["language"], "content": content, "analysis": info, "complexity": cx}


@router.delete("/repository/{repository}")
def delete_repository(repository: str):
    repo_id = get_repo_id(repository)
    removed_index = vector_store.delete_repository(repo_id)
    removed_files = storage.delete_repository_files(repo_id)
    if not (removed_index or removed_files):
        raise NotFoundError(f"Repository '{repo_id}' was not found.")
    return {"deleted": True, "repository": repo_id}
