"""Central configuration. All values come from environment variables / backend/.env."""
import os
from pathlib import Path

from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BACKEND_DIR / ".env")


def _get_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def _get_float(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        return float(raw)
    except ValueError:
        return default


def _get_path(name: str, default: str) -> Path:
    """Relative paths are resolved against the backend folder (not the shell's cwd)."""
    path = Path(os.getenv(name) or default)
    if not path.is_absolute():
        path = (BACKEND_DIR / path).resolve()
    return path


class Settings:
    def __init__(self) -> None:
        # GitHub (token is optional; public repositories work without it)
        self.GITHUB_TOKEN: str = os.getenv("GITHUB_TOKEN", "").strip()
        self.GITHUB_API_URL: str = "https://api.github.com"
        self.GITHUB_RAW_URL: str = "https://raw.githubusercontent.com"

        # Ollama (local LLM)
        self.OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
        self.OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "llama3.1:8b")
        self.OLLAMA_TIMEOUT: int = _get_int("OLLAMA_TIMEOUT", 300)
        self.OLLAMA_NUM_CTX: int = _get_int("OLLAMA_NUM_CTX", 8192)

        # Embeddings / vector DB
        self.EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
        self.EMBEDDING_MAX_TOKENS: int = _get_int("EMBEDDING_MAX_TOKENS", 512)
        self.CHROMA_DIR: Path = _get_path("CHROMA_DIR", "./data/chroma")
        self.REPOS_DIR: Path = _get_path("REPOS_DIR", "./data/repos")

        # Limits
        self.MAX_FILE_SIZE_KB: int = _get_int("MAX_FILE_SIZE_KB", 500)
        self.MAX_FILES_TO_ANALYZE: int = _get_int("MAX_FILES_TO_ANALYZE", 100)
        self.TOP_K_RESULTS: int = _get_int("TOP_K_RESULTS", 5)
        self.MAX_CONTEXT_CHARACTERS: int = _get_int("MAX_CONTEXT_CHARACTERS", 12000)
        self.MAX_CHUNK_LINES: int = _get_int("MAX_CHUNK_LINES", 80)
        self.OVERLAP_LINES: int = _get_int("OVERLAP_LINES", 10)
        self.MIN_RELEVANCE: float = _get_float("MIN_RELEVANCE", 0.05)
        self.DOWNLOAD_WORKERS: int = _get_int("DOWNLOAD_WORKERS", 8)

        # CORS
        frontend = os.getenv("FRONTEND_URL", "http://localhost:5173")
        origins = {o.strip().rstrip("/") for o in frontend.split(",") if o.strip()}
        origins.update({"http://localhost:5173", "http://127.0.0.1:5173"})
        self.ALLOWED_ORIGINS: list[str] = sorted(origins)

    def ensure_dirs(self) -> None:
        self.CHROMA_DIR.mkdir(parents=True, exist_ok=True)
        self.REPOS_DIR.mkdir(parents=True, exist_ok=True)


settings = Settings()
