"""Minimal Ollama client (local LLM, no API key)."""
import logging
from typing import Optional

import requests

from app.config import settings
from app.errors import OllamaError

logger = logging.getLogger("repopilot.ollama")


def _post(path: str, payload: dict) -> dict:
    url = f"{settings.OLLAMA_BASE_URL}{path}"
    model = payload.get("model")
    try:
        resp = requests.post(url, json=payload, timeout=settings.OLLAMA_TIMEOUT)
    except requests.ConnectionError as exc:
        raise OllamaError(f"Cannot connect to Ollama at {settings.OLLAMA_BASE_URL}. "
                          "Start it with `ollama serve` (or the Docker service).", 503, "ollama_unavailable") from exc
    except requests.Timeout as exc:
        raise OllamaError("Ollama took too long to answer. Try a smaller model or increase OLLAMA_TIMEOUT.",
                          504, "ollama_timeout") from exc
    except requests.RequestException as exc:
        raise OllamaError(f"Ollama request failed: {exc}", 502, "ollama_error") from exc

    if resp.status_code == 404:
        raise OllamaError(f"Ollama model '{model}' is not installed. Run: ollama pull {model}",
                          503, "ollama_model_missing")
    if resp.status_code != 200:
        logger.error("Ollama HTTP %s: %s", resp.status_code, resp.text[:300])
        raise OllamaError(f"Ollama returned HTTP {resp.status_code}. Check the Ollama logs.", 502, "ollama_error")
    try:
        return resp.json()
    except ValueError as exc:
        raise OllamaError("Ollama returned an invalid response.", 502, "ollama_error") from exc


def _options(temperature: float) -> dict:
    return {"temperature": temperature, "num_ctx": settings.OLLAMA_NUM_CTX}


def generate(prompt: str, system: Optional[str] = None, model: Optional[str] = None,
             temperature: float = 0.2) -> str:
    payload = {"model": model or settings.OLLAMA_MODEL, "prompt": prompt, "stream": False,
               "options": _options(temperature)}
    if system:
        payload["system"] = system
    text = (_post("/api/generate", payload).get("response") or "").strip()
    if not text:
        raise OllamaError("Ollama returned an empty response.", 502, "ollama_empty")
    return text


def chat(messages: list[dict], model: Optional[str] = None, temperature: float = 0.2) -> str:
    payload = {"model": model or settings.OLLAMA_MODEL, "messages": messages, "stream": False,
               "options": _options(temperature)}
    text = ((_post("/api/chat", payload).get("message") or {}).get("content") or "").strip()
    if not text:
        raise OllamaError("Ollama returned an empty response.", 502, "ollama_empty")
    return text


def check_status() -> dict:
    """Quick health probe used by /health (never raises)."""
    try:
        resp = requests.get(f"{settings.OLLAMA_BASE_URL}/api/tags", timeout=2)
        resp.raise_for_status()
        names = [m.get("name", "") for m in resp.json().get("models", [])]
        wanted = settings.OLLAMA_MODEL
        installed = any(n == wanted or n.split(":")[0] == wanted.split(":")[0] and ":" not in wanted for n in names)
        return {"available": True, "model": wanted, "model_installed": installed}
    except Exception:
        return {"available": False, "model": settings.OLLAMA_MODEL, "model_installed": False}
