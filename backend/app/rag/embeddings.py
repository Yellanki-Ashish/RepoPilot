"""Local embeddings with sentence-transformers (no API key). The model is loaded lazily, once."""
import logging
import threading
from typing import Any

from app.config import settings
from app.errors import EmbeddingError

logger = logging.getLogger("repopilot.embeddings")
_model: Any = None
_lock = threading.Lock()


def get_model() -> Any:
    global _model
    if _model is None:
        with _lock:
            if _model is None:
                try:
                    from sentence_transformers import SentenceTransformer  # heavy import: keep lazy
                    logger.info("Loading embedding model %s ...", settings.EMBEDDING_MODEL)
                    model = SentenceTransformer(settings.EMBEDDING_MODEL)
                    model.max_seq_length = min(settings.EMBEDDING_MAX_TOKENS, 512)
                    _model = model
                except Exception as exc:
                    print("REPOPILOT ERROR:", repr(exc))
                    raise EmbeddingError(
                        f"Could not load embedding model '{settings.EMBEDDING_MODEL}'. The first run needs "
                        "internet access to download it. Check backend logs.", 500, "embedding_model_error",
                    ) from exc
    return _model


def embed_texts(texts: list[str], batch_size: int = 32) -> list[list[float]]:
    if not texts:
        return []
    model = get_model()
    try:
        vectors = model.encode(texts, batch_size=batch_size, show_progress_bar=False,
                               normalize_embeddings=True, convert_to_numpy=True)
    except Exception as exc:
        print("REPOPILOT ERROR:", repr(exc))
        raise EmbeddingError("Embedding generation failed. Check backend logs.", 500, "embedding_error") from exc
    return vectors.tolist()


def embed_query(text: str) -> list[float]:
    return embed_texts([text])[0]
