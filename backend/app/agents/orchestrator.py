"""Orchestrator: decides which agents handle a question, runs them, and lets DeveloperAgent answer."""
import logging
import re

from app.agents.architecture_agent import ArchitectureAgent
from app.agents.base import AgentContext, AgentReport
from app.agents.code_agent import CodeAgent
from app.agents.dependency_agent import DependencyAgent
from app.agents.developer_agent import DeveloperAgent
from app.agents.issue_agent import IssueAgent
from app.agents.onboarding_agent import OnboardingAgent
from app.agents.rag_agent import RAGAgent
from app.agents.repository_agent import RepositoryAgent
from app.errors import AppError

logger = logging.getLogger("repopilot.orchestrator")

_REGISTRY = {a.name: a for a in (RAGAgent(), RepositoryAgent(), ArchitectureAgent(), DependencyAgent(),
                                 CodeAgent(), OnboardingAgent(), IssueAgent())}
_ORDER = ["RAGAgent", "RepositoryAgent", "ArchitectureAgent", "DependencyAgent", "CodeAgent",
          "OnboardingAgent", "IssueAgent"]  # RAG runs first so later agents can use its results

_RULES: list[tuple[str, str, list[str]]] = [
    ("issue_analysis", r"\bissues?\b|#\d+", ["RAGAgent", "IssueAgent", "DependencyAgent"]),
    ("change_planning",
     r"how (do|can|should|would) i (add|implement|integrate|build|create|extend|modify|change)"
     r"|which files? (should|do|would) i (modify|change|edit|touch)|\b(add|implement|integrate)\b.*\b(login|oauth|feature|support|endpoint|payment)\b",
     ["RAGAgent", "CodeAgent", "DependencyAgent", "OnboardingAgent"]),
    ("onboarding", r"read first|where (do|should) i start|roadmap|onboard|getting started|\blearn|contribut",
     ["RepositoryAgent", "OnboardingAgent"]),
    ("architecture", r"architecture|data flow|layers|tech stack|technologies|overall structure",
     ["RepositoryAgent", "ArchitectureAgent"]),
    ("dependency_analysis",
     r"most connected|most important|central|important (file|module)|depend|coupl|imported by|related modules",
     ["DependencyAgent", "RepositoryAgent"]),
    ("complexity_analysis", r"complex|hardest|largest|biggest", ["CodeAgent", "RepositoryAgent"]),
]
_DEFAULT = ("code_question", ["RAGAgent", "CodeAgent"])


def plan_agents(question: str) -> tuple[str, list[str]]:
    """Return (intent, ordered agent names) for a question."""
    q = question.lower()
    intent, agents = _DEFAULT
    for name, pattern, chosen in _RULES:
        if re.search(pattern, q):
            intent, agents = name, list(chosen)
            break
    if intent == "architecture" and "flow" in q and "RAGAgent" not in agents:
        agents.append("RAGAgent")  # data flow questions need actual code evidence
    return intent, [a for a in _ORDER if a in agents]


def answer_question(repo_id: str, question: str, analysis: dict, top_k: int) -> dict:
    intent, plan = plan_agents(question)
    ctx = AgentContext(repository_id=repo_id, question=question, analysis=analysis, top_k=top_k)
    reports: list[AgentReport] = []
    for name in plan:
        try:
            reports.append(_REGISTRY[name].run(ctx))
        except AppError:
            raise  # embedding / vector-store problems must reach the user with a clear message
        except Exception as exc:
            print("REPOPILOT ERROR:", repr(exc))
            logger.exception("Agent %s failed", name)
            reports.append(AgentReport(name, f"{name} failed internally and produced no findings."))
    developer = DeveloperAgent()
    answer, sources = developer.answer(ctx, reports)
    return {"answer": answer, "sources": sources, "agents_used": plan + [developer.name], "intent": intent}
