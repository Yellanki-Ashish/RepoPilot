"""Structure-aware code chunker with overlapping windows."""
from typing import Optional

from app.config import settings


def _definitions(analysis: Optional[dict]) -> list[tuple[int, Optional[int], str]]:
    """(start_line, end_line|None, label) for every class / function / method, sorted by line."""
    defs: list[tuple[int, Optional[int], str]] = []
    if not analysis:
        return defs
    for c in analysis.get("classes", []):
        defs.append((c["start_line"], c.get("end_line"), c["name"]))
    for f in analysis.get("functions", []):
        defs.append((f["start_line"], f.get("end_line"), f["name"]))
    for m in analysis.get("methods", []):
        defs.append((m["start_line"], m.get("end_line"), f"{m.get('class', '?')}.{m['name']}"))
    return sorted(defs, key=lambda d: d[0])


def _boundaries(analysis: Optional[dict]) -> list[int]:
    """Lines where a top-level class/function starts: good places to begin a new chunk."""
    if not analysis:
        return []
    lines = [c["start_line"] for c in analysis.get("classes", [])]
    lines += [f["start_line"] for f in analysis.get("functions", [])]
    return sorted(set(lines))


def _section(defs: list, start: int, end: int) -> str:
    labels: list[str] = []
    enclosing = [d for d in defs if d[0] <= start and (d[1] is None or d[1] >= start)]
    if enclosing:
        labels.append(enclosing[-1][2])
    labels += [d[2] for d in defs if start < d[0] <= end]
    labels = list(dict.fromkeys(labels))
    return ", ".join(labels[:4]) if labels else "module level"


def create_code_chunks(file: str, language: str, content: str, analysis: Optional[dict] = None,
                       max_lines: Optional[int] = None, overlap: Optional[int] = None) -> list[dict]:
    """Split a file into overlapping chunks, preferring to break right before a class/function."""
    max_lines = max_lines or settings.MAX_CHUNK_LINES
    overlap = settings.OVERLAP_LINES if overlap is None else overlap
    if overlap >= max_lines:
        overlap = max_lines // 4

    lines = content.splitlines()
    total = len(lines)
    if total == 0:
        return []

    defs = _definitions(analysis)
    boundaries = _boundaries(analysis)
    chunks: list[dict] = []
    start = 1
    while start <= total:
        end = min(start + max_lines - 1, total)
        if end < total:
            # break just before a definition if one starts in the second half of the window
            candidates = [b - 1 for b in boundaries if start + max_lines // 2 <= b - 1 <= end]
            if candidates:
                end = max(candidates)
        text = "\n".join(lines[start - 1:end])
        if text.strip():
            chunks.append({
                "file": file, "language": language, "start_line": start, "end_line": end,
                "section": _section(defs, start, end), "chunk_index": len(chunks), "content": text,
            })
        if end >= total:
            break
        start = max(end - overlap + 1, start + 1)
    return chunks
