from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


class AnalyzeRequest(BaseModel):
    url: str = Field(..., min_length=1, max_length=300, examples=["https://github.com/psf/requests"])
    progress_id: Optional[str] = Field(None, pattern=r"^[A-Za-z0-9_-]{6,64}$",
                                       description="Optional id used to poll GET /api/progress/{id}")
    force_refresh: bool = Field(False, description="Ignore the saved analysis and re-download everything")


class RepositoryInfo(BaseModel):
    model_config = ConfigDict(extra="allow")
    name: str
    owner: str
    full_name: str
    description: Optional[str] = None
    default_branch: str
    stars: int = 0


class RagInfo(BaseModel):
    indexed_chunks: int
    embedding_model: str
    collection: str


class AnalyzeResponse(BaseModel):
    repository_id: str
    repository: RepositoryInfo
    analysis: dict[str, Any]
    code_analysis: list[dict[str, Any]]
    complexity: dict[str, Any]
    dependency_graph: dict[str, Any]
    architecture: dict[str, Any]
    key_files: dict[str, Any] = {}
    rag: RagInfo
    from_cache: bool = False
    analyzed_at: Optional[str] = None


class SearchRequest(BaseModel):
    repository: str = Field(..., min_length=1, examples=["psf_requests"])
    query: str = Field(..., min_length=2, max_length=1000, examples=["where is authentication implemented"])
    top_k: Optional[int] = Field(None, ge=1, le=20)


class SearchResult(BaseModel):
    content: str
    file: str
    language: str
    start_line: int
    end_line: int
    section: str
    chunk_index: int
    relevance: Optional[float] = None
    distance: Optional[float] = None


class SearchResponse(BaseModel):
    repository: str
    query: str
    results: list[SearchResult]
