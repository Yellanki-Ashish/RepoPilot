"""Turn retrieved chunks into a size-limited context block for the LLM."""
from typing import Optional

from app.config import settings

_TRUNCATED = "\n... [truncated]"


def build_context(results: list[dict], max_chars: Optional[int] = None) -> dict:
    """Return {"context": str, "included": [chunks actually included]}."""
    limit = max_chars or settings.MAX_CONTEXT_CHARACTERS
    parts: list[str] = []
    included: list[dict] = []
    used = 0
    for number, item in enumerate(results, start=1):
        header = (f"--- SOURCE {number} ---\nFile: {item['file']}\n"
                  f"Lines: {item['start_line']}-{item['end_line']}\nSection: {item['section']}\n\n")
        remaining = limit - used - len(header)
        if remaining < 200:  # not enough room for something useful
            break
        code = item["content"]
        if len(code) > remaining:
            code = code[: remaining - len(_TRUNCATED)] + _TRUNCATED
        block = header + code + "\n\n"
        parts.append(block)
        included.append(item)
        used += len(block)
    return {"context": "".join(parts).strip(), "included": included}
