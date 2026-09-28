from typing import Literal

from fastapi import APIRouter, Query

from app.agents.issue_agent import analyze_issue
from app.api.deps import require_analysis
from app.config import settings
from app.ingestion import github_client
from app.schemas.issues import IssueAnalyzeRequest, IssueAnalyzeResponse, IssueListResponse

router = APIRouter(prefix="/api/issues", tags=["issues"])


@router.get("/{repository}", response_model=IssueListResponse)
def list_issues(repository: str, state: Literal["open", "closed", "all"] = "open",
                limit: int = Query(20, ge=1, le=50)):
    repo_id, data = require_analysis(repository)
    info = data["repository"]
    issues = github_client.get_issues(info["owner"], info["name"], state, limit)
    return {"repository": repo_id, "count": len(issues), "issues": issues}


@router.post("/analyze", response_model=IssueAnalyzeResponse)
def analyze_issues(req: IssueAnalyzeRequest):
    repo_id, data = require_analysis(req.repository)
    info = data["repository"]
    if req.issue_number:
        issues = [github_client.get_issue(info["owner"], info["name"], req.issue_number)]
    else:
        issues = github_client.get_issues(info["owner"], info["name"], req.state, req.limit)
    results = [analyze_issue(i, repo_id, data, settings.TOP_K_RESULTS) for i in issues]
    return {"repository": repo_id, "count": len(results), "issues": results}
