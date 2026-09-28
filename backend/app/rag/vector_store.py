"""ChromaDB persistence. One isolated collection per repository (e.g. repo_psf_requests)."""
import logging
import threading
from typing import Any

from app.config import settings
from app.errors import AppError
from app.utils import collection_name

logger = logging.getLogger("repopilot.vector_store")
_client: Any = None
_lock = threading.Lock()
_BATCH = 200


def _get_client() -> Any:
    global _client
    if _client is None:
        with _lock:
            if _client is None:
                try:
                    import chromadb
                    from chromadb.config import Settings as ChromaSettings
                    settings.CHROMA_DIR.mkdir(parents=True, exist_ok=True)
                    _client = chromadb.PersistentClient(
                        path=str(settings.CHROMA_DIR),
                        settings=ChromaSettings(anonymized_telemetry=False),
                    )
                except Exception as exc:
                    print("REPOPILOT ERROR:", repr(exc))
                    raise AppError("Vector database (ChromaDB) could not be opened. Check backend logs.",
                                   500, "vector_store_error") from exc
    return _client


def get_collection(repo_id: str, create: bool = True) -> Any:
    client = _get_client()
    name = collection_name(repo_id)
    if create:
        return client.get_or_create_collection(name=name, metadata={"hnsw:space": "cosine"})
    return client.get_collection(name=name)


def repository_exists(repo_id: str) -> bool:
    try:
        return get_collection(repo_id, create=False).count() > 0
    except AppError:
        raise
    except Exception:  # chroma raises different errors depending on version when missing
        return False


def delete_repository(repo_id: str) -> bool:
    client = _get_client()
    try:
        client.delete_collection(name=collection_name(repo_id))
        return True
    except Exception as exc:
        logger.info("No collection to delete for %s (%r)", repo_id, exc)
        return False


def add_chunks(repo_id: str, chunks: list[dict], embeddings: list[list[float]]) -> int:
    """Replace the repository's collection with the given chunks."""
    if len(chunks) != len(embeddings):
        raise ValueError("chunks and embeddings must have the same length")
    delete_repository(repo_id)
    collection = get_collection(repo_id, create=True)
    for i in range(0, len(chunks), _BATCH):
        part = chunks[i:i + _BATCH]
        collection.add(
            ids=[f"{c['file']}::{c['chunk_index']}" for c in part],
            embeddings=embeddings[i:i + _BATCH],
            documents=[c["content"] for c in part],
            metadatas=[{"file": c["file"], "language": c["language"], "start_line": c["start_line"],
                        "end_line": c["end_line"], "section": c["section"],
                        "chunk_index": c["chunk_index"]} for c in part],
        )
    return collection.count()


def search_code(repo_id: str, query_embedding: list[float], top_k: int) -> list[dict]:
    try:
        collection = get_collection(repo_id, create=False)
    except AppError:
        raise
    except Exception:
        return []
    total = collection.count()
    if total == 0:
        return []
    raw = collection.query(query_embeddings=[query_embedding], n_results=min(top_k, total),
                           include=["documents", "metadatas", "distances"])
    results = []
    for doc, meta, dist in zip(raw["documents"][0], raw["metadatas"][0], raw["distances"][0]):
        results.append({
            "content": doc, "file": meta["file"], "language": meta["language"],
            "start_line": meta["start_line"], "end_line": meta["end_line"],
            "section": meta["section"], "chunk_index": meta["chunk_index"],
            "distance": round(float(dist), 4), "relevance": round(1.0 - float(dist), 4),  # cosine similarity
        })
    return results
