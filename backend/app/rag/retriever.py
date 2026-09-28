"""Semantic retrieval: question -> embedding -> ChromaDB top-k."""
from typing import Optional

from app.config import settings
from app.errors import NotFoundError
from app.rag import embeddings, vector_store


def retrieve(repo_id: str, question: str, top_k: Optional[int] = None) -> list[dict]:
    if not vector_store.repository_exists(repo_id):
        raise NotFoundError(f"No vector index found for '{repo_id}'. Analyze the repository first.")
    query_vector = embeddings.embed_query(question)
    results = vector_store.search_code(repo_id, query_vector, top_k or settings.TOP_K_RESULTS)
    return [r for r in results if r["relevance"] >= settings.MIN_RELEVANCE]
