"""Developer Assistant Agent: combines every agent's findings with RAG context and asks the local LLM."""
from app.agents.base import AgentContext, AgentReport, clip, repo_label
from app.llm import ollama_client
from app.rag import rag_service

_MAX_FINDINGS_CHARS = 6000


class DeveloperAgent:
    name = "DeveloperAgent"

    def answer(self, ctx: AgentContext, reports: list[AgentReport]) -> tuple[str, list[dict]]:
        """Return (answer, sources)."""
        findings = "\n\n".join(f"[{r.agent}]\n{clip(r.summary, 2500)}" for r in reports if r.summary)
        findings = clip(findings, _MAX_FINDINGS_CHARS)
        wanted_rag = any(r.agent == "RAGAgent" for r in reports)

        if wanted_rag and not ctx.rag_results and len(reports) == 1:
            return rag_service.INSUFFICIENT_MESSAGE, []

        prompt = rag_service.build_prompt(repo_label(ctx.analysis), ctx.question, ctx.rag_context, findings)
        answer = ollama_client.chat([
            {"role": "system", "content": rag_service.RAG_SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ])
        return answer, self._sources(ctx, reports)

    @staticmethod
    def _sources(ctx: AgentContext, reports: list[AgentReport]) -> list[dict]:
        sources: list[dict] = []
        seen: set = set()
        for r in ctx.rag_results:
            key = (r["file"], r["start_line"], r["end_line"])
            if key not in seen:
                seen.add(key)
                sources.append({"file": r["file"], "start_line": r["start_line"], "end_line": r["end_line"],
                                "section": r["section"], "language": r["language"], "relevance": r["relevance"]})
        covered = {s["file"] for s in sources}
        for rep in reports:  # files highlighted by other agents (no line range)
            for path in rep.files:
                if path not in covered and len(sources) < 10:
                    covered.add(path)
                    sources.append({"file": path, "start_line": None, "end_line": None,
                                    "section": f"suggested by {rep.agent}", "language": None, "relevance": None})
        return sources
