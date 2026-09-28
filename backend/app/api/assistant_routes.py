from fastapi import APIRouter

from app.agents import orchestrator
from app.api.deps import require_analysis
from app.config import settings
from app.schemas.assistant import AskRequest, AskResponse

router = APIRouter(prefix="/api/assistant", tags=["assistant"])


@router.post("/ask", response_model=AskResponse)
def ask(req: AskRequest):
    """Answer a developer question using RAG + specialised agents + the local Ollama model."""
    repo_id, analysis = require_analysis(req.repository)
    return orchestrator.answer_question(repo_id, req.question, analysis, req.top_k or settings.TOP_K_RESULTS)
