"""In-memory progress tracking so the frontend can show real analysis stages."""
import threading
import time

STEPS = [
    "Scanning repository...",
    "Downloading source files...",
    "Analyzing source code...",
    "Building dependency graph...",
    "Creating code chunks...",
    "Generating embeddings...",
    "Indexing repository...",
    "Preparing AI assistant...",
]

_lock = threading.Lock()
_store: dict[str, dict] = {}
_MAX_ENTRIES = 200


def set_step(progress_id: str | None, step: int) -> None:
    if not progress_id:
        return
    with _lock:
        if len(_store) >= _MAX_ENTRIES:
            oldest = sorted(_store, key=lambda k: _store[k]["updated"])[: _MAX_ENTRIES // 2]
            for key in oldest:
                _store.pop(key, None)
        _store[progress_id] = {
            "status": "running", "step": step, "total": len(STEPS),
            "message": STEPS[step], "updated": time.time(),
        }


def finish(progress_id: str | None, ok: bool, message: str = "") -> None:
    if not progress_id:
        return
    with _lock:
        _store[progress_id] = {
            "status": "done" if ok else "error", "step": len(STEPS) - 1 if ok else -1,
            "total": len(STEPS), "message": message or ("Done" if ok else "Failed"),
            "updated": time.time(),
        }


def get(progress_id: str) -> dict:
    with _lock:
        entry = _store.get(progress_id)
    if entry is None:
        return {"status": "unknown", "step": -1, "total": len(STEPS), "message": ""}
    return {k: v for k, v in entry.items() if k != "updated"}
