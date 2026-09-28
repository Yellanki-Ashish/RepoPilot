import logging

from fastapi import APIRouter

from app.agents import onboarding_agent
from app.agents.issue_agent import analyze_issue
from app.api.deps import require_analysis
from app.errors import AppError
from app.ingestion import github_client
from app.schemas.onboarding import RoadmapRequest, RoadmapResponse

logger = logging.getLogger("repopilot.routes")
router = APIRouter(prefix="/api/onboarding", tags=["onboarding"])


def _suggest_first_issue(repo_id: str, analysis: dict, notes: list[str]):
    """Pick the lowest-difficulty open issue (heuristic). Best effort: GitHub may be unreachable."""
    info = analysis["repository"]
    try:
        issues = github_client.get_issues(info["owner"], info["name"], "open", 15)
    except AppError as exc:
        notes.append(f"Could not load issues: {exc.message}")
        return None
    if not issues:
        notes.append("No open issues were found.")
        return None
    good = {"good first issue", "good-first-issue", "help wanted", "beginner"}
    analyzed = [analyze_issue(i, repo_id, analysis, use_rag=False) for i in issues]
    best = min(analyzed, key=lambda r: (r["complexity_points"], not (set(l.lower() for l in r["labels"]) & good)))
    return {k: best[k] for k in ("number", "title", "html_url", "labels", "estimated_complexity",
                                 "potential_files", "reasoning")}


@router.post("/roadmap", response_model=RoadmapResponse)
def create_roadmap(req: RoadmapRequest):
    repo_id, analysis = require_analysis(req.repository)
    roadmap = onboarding_agent.build_roadmap(analysis)
    roadmap["suggested_first_issue"] = _suggest_first_issue(repo_id, analysis, roadmap["notes"])
    if req.include_ai_summary:
        onboarding_agent.add_ai_summary(roadmap, analysis)
    return roadmap
