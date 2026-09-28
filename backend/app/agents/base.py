"""Shared types and helpers for all agents."""
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class AgentContext:
    repository_id: str
    question: str
    analysis: dict
    top_k: int
    rag_results: list[dict] = field(default_factory=list)
    rag_context: str = ""


@dataclass
class AgentReport:
    agent: str
    summary: str                       # evidence text handed to the developer agent / LLM
    files: list[str] = field(default_factory=list)
    data: dict = field(default_factory=dict)


def code_index(analysis: dict) -> dict[str, dict]:
    return {a["file"]: a for a in analysis.get("code_analysis", [])}


def complexity_index(analysis: dict) -> dict[str, dict]:
    return {c["file"]: c for c in analysis.get("complexity", {}).get("files", [])}


def repo_label(analysis: dict) -> str:
    return analysis.get("repository", {}).get("full_name", analysis.get("repository_id", "repository"))


def graph_stats(analysis: dict) -> dict:
    return analysis.get("dependency_graph", {}).get("statistics", {})


def clip(text: str, limit: int) -> str:
    return text if len(text) <= limit else text[:limit] + "..."


def fmt_list(items: list[Any], limit: int = 8) -> str:
    return ", ".join(str(i) for i in items[:limit]) if items else "none"


def find_file_in_text(text: str, paths: list[str]) -> Optional[str]:
    """If the text mentions a repository file (full path or unique file name), return it."""
    lowered = text.lower()
    for path in paths:
        if path.lower() in lowered:
            return path
    by_name: dict[str, list[str]] = {}
    for path in paths:
        by_name.setdefault(path.rsplit("/", 1)[-1].lower(), []).append(path)
    for name, matches in by_name.items():
        if len(matches) == 1 and len(name) > 4 and name in lowered:
            return matches[0]
    return None
