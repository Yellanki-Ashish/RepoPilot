"""RAG service: retrieval + context building + the grounded prompt used with the local LLM."""
from typing import Optional

from app.config import settings
from app.rag import context_builder, retriever

INSUFFICIENT_MESSAGE = ("The repository evidence is insufficient to answer this question. "
                        "No relevant code was retrieved from the index.")

RAG_SYSTEM_PROMPT = (
    "You are RepoPilot, a senior engineer who explains a GitHub repository to a developer.\n"
    "Rules:\n"
    "1. Answer ONLY from the repository evidence provided (analysis findings and source excerpts).\n"
    "2. Cite files as `path/to/file.py` and line ranges like (lines 20-60) taken from the SOURCE headers.\n"
    "3. If the evidence does not contain the answer, say exactly: 'The repository evidence is insufficient' "
    "and explain what is missing. Never invent files, functions, or behaviour.\n"
    "4. Be concise and practical. Use short paragraphs or bullet points."
)


def retrieve_repository_context(repo_id: str, question: str, top_k: Optional[int] = None) -> dict:
    """Question -> embedding -> ChromaDB -> top-k chunks -> formatted context."""
    results = retriever.retrieve(repo_id, question, top_k or settings.TOP_K_RESULTS)
    built = context_builder.build_context(results)
    return {"context": built["context"], "results": built["included"], "retrieved": len(results)}


def build_prompt(repository: str, question: str, context: str, findings: str) -> str:
    sections = [f"Repository: {repository}", f"Question: {question}"]
    if findings:
        sections.append("=== ANALYSIS FINDINGS (static analysis of the repository) ===\n" + findings)
    sections.append("=== RETRIEVED SOURCE CODE ===\n" + (context or "(no code was retrieved)"))
    sections.append("Answer the question using only the evidence above.")
    return "\n\n".join(sections)
