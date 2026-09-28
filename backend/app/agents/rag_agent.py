"""RAG Agent: retrieves relevant code chunks for the question."""
from app.agents.base import AgentContext, AgentReport
from app.rag import rag_service


class RAGAgent:
    name = "RAGAgent"

    def run(self, ctx: AgentContext) -> AgentReport:
        retrieved = rag_service.retrieve_repository_context(ctx.repository_id, ctx.question, ctx.top_k)
        ctx.rag_results = retrieved["results"]
        ctx.rag_context = retrieved["context"]
        files = list(dict.fromkeys(r["file"] for r in ctx.rag_results))
        summary = (f"Retrieved {retrieved['retrieved']} relevant code chunks from files: {', '.join(files) or 'none'}."
                   if files else "No relevant code chunks were retrieved.")
        return AgentReport(self.name, summary, files=files)
