from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


class IssueAnalyzeRequest(BaseModel):
    repository: str = Field(..., min_length=1, examples=["psf_requests"])
    issue_number: Optional[int] = Field(None, ge=1, description="Analyze one issue; omit to analyze the latest ones")
    state: Literal["open", "closed", "all"] = "open"
    limit: int = Field(10, ge=1, le=30)


class IssueAnalyzeResponse(BaseModel):
    repository: str
    count: int
    issues: list[dict[str, Any]]


class IssueListResponse(BaseModel):
    repository: str
    count: int
    issues: list[dict[str, Any]]
