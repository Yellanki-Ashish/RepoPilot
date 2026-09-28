"""Issue Analysis Agent: maps a GitHub issue to likely files and a transparent difficulty estimate."""
import logging
import re
from typing import Optional

from app.agents.base import AgentContext, AgentReport, code_index, complexity_index, fmt_list
from app.config import settings
from app.errors import AppError
from app.ingestion import github_client
from app.rag import retriever

logger = logging.getLogger("repopilot.issue_agent")

_EASY_LABELS = {"good first issue", "good-first-issue", "beginner", "easy", "documentation", "docs", "typo"}
_HARD_LABELS = {"security", "performance", "breaking change", "breaking", "refactor", "architecture"}
_FEATURE_LABELS = {"feature", "enhancement", "feature request"}
_PATH_RE = re.compile(r"[\w./-]+\.(?:py|js|jsx|ts|tsx|java)\b")
_CAMEL_RE = re.compile(r"\b[A-Z][a-z0-9]+(?:[A-Z][a-z0-9]+)+\b")
_SNAKE_RE = re.compile(r"\b[a-z]+(?:_[a-z0-9]+)+\b")


def analyze_issue(issue: dict, repo_id: str, analysis: dict, top_k: int = 5, use_rag: bool = True) -> dict:
    """Heuristic issue analysis. Returns files with reasons and Low/Medium/High with the rules used."""
    index, cx = code_index(analysis), complexity_index(analysis)
    text = f"{issue.get('title', '')}\n{issue.get('body', '')}"
    scores: dict[str, dict] = {}
    notes: list[str] = []

    def bump(path: str, points: float, reason: str) -> None:
        entry = scores.setdefault(path, {"score": 0.0, "reasons": []})
        entry["score"] += points
        if reason not in entry["reasons"]:
            entry["reasons"].append(reason)

    # explicit file paths mentioned in the issue
    for mention in _PATH_RE.findall(text):
        clean = mention.lstrip("./")
        for path in index:
            if path == clean or path.endswith("/" + clean):
                bump(path, 4.0, f"file is mentioned in the issue ({mention})")

    # identifiers (`code`, CamelCase, snake_case) that match known symbols
    names = {t.lower() for t in re.findall(r"`([^`\n]{2,60})`", text)}
    names |= {t.lower() for t in _CAMEL_RE.findall(text) + _SNAKE_RE.findall(text)}
    if names:
        for path, a in index.items():
            for key in ("classes", "functions", "methods"):
                for item in a[key]:
                    if item["name"].lower() in names:
                        bump(path, 2.5, f"defines '{item['name']}' which the issue mentions")

    # semantic similarity through the vector index
    if use_rag:
        try:
            for r in retriever.retrieve(repo_id, text[:1200], top_k):
                bump(r["file"], 2.0 * r["relevance"] + 0.5,
                     f"code similar to the issue text (lines {r['start_line']}-{r['end_line']})")
        except AppError as exc:
            notes.append(f"Semantic search unavailable: {exc.message}")

    ranked = sorted(scores.items(), key=lambda kv: -kv[1]["score"])[:5]
    potential_files = [{"file": p, "score": round(v["score"], 2), "reasons": v["reasons"][:3]} for p, v in ranked]
    modules = list(dict.fromkeys((p.rsplit("/", 1)[0] if "/" in p else "(root)") for p, _ in ranked))[:4]

    level, points, reasoning = _estimate(issue, potential_files, modules, cx)
    return {
        "number": issue.get("number"), "title": issue.get("title"), "html_url": issue.get("html_url"),
        "labels": issue.get("labels", []), "comments": issue.get("comments", 0),
        "body_excerpt": (issue.get("body") or "")[:400],
        "potential_files": potential_files, "potential_modules": modules,
        "estimated_complexity": level, "complexity_points": points, "reasoning": reasoning,
        "disclaimer": "Heuristic estimate from labels, text length and code metrics. Not a guarantee.",
        "notes": notes,
    }


def _estimate(issue: dict, files: list[dict], modules: list[str], cx: dict) -> tuple[str, int, list[str]]:
    points, reasons = 0, []
    labels = {l.lower() for l in issue.get("labels", [])}
    if labels & _EASY_LABELS:
        points -= 2
        reasons.append(f"-2: easy-looking label ({fmt_list(sorted(labels & _EASY_LABELS))})")
    if labels & _FEATURE_LABELS:
        points += 1
        reasons.append("+1: labelled as a feature/enhancement")
    if labels & _HARD_LABELS:
        points += 2
        reasons.append(f"+2: label suggests wider impact ({fmt_list(sorted(labels & _HARD_LABELS))})")
    if len(issue.get("body") or "") > 1500:
        points += 1
        reasons.append("+1: long description (>1500 characters)")
    if (issue.get("comments") or 0) > 10:
        points += 1
        reasons.append("+1: long discussion (>10 comments)")
    if len(files) >= 4:
        points += 1
        reasons.append("+1: many potentially related files (>=4)")
    if len(modules) >= 3:
        points += 1
        reasons.append("+1: touches 3 or more modules")
    top = max((cx.get(f["file"], {}).get("complexity", 0) for f in files), default=0)
    if top > 100:
        points += 2
        reasons.append(f"+2: a related file has high approximate complexity ({top})")
    elif top > 50:
        points += 1
        reasons.append(f"+1: a related file has moderate approximate complexity ({top})")
    level = "Low" if points <= 1 else "Medium" if points <= 3 else "High"
    reasons.append(f"Total points: {points} (Low <= 1, Medium 2-3, High >= 4)")
    return level, points, reasons


class IssueAgent:
    name = "IssueAgent"

    def run(self, ctx: AgentContext) -> AgentReport:
        match = re.search(r"(?:#|issue\s+(?:number\s+)?)(\d+)", ctx.question, re.I)
        if not match:
            return AgentReport(self.name, "The question mentions issues but no issue number (like #123).")
        info = ctx.analysis["repository"]
        try:
            issue = github_client.get_issue(info["owner"], info["name"], int(match.group(1)))
        except AppError as exc:
            logger.warning("IssueAgent could not fetch the issue: %s", exc.message)
            return AgentReport(self.name, f"Could not fetch issue #{match.group(1)}: {exc.message}")
        result = analyze_issue(issue, ctx.repository_id, ctx.analysis, ctx.top_k)
        lines = [f"Issue #{result['number']}: {result['title']}", f"Labels: {fmt_list(result['labels'])}",
                 f"Description: {result['body_excerpt']}",
                 "Potentially relevant files: " + fmt_list(
                     [f"{f['file']} ({'; '.join(f['reasons'][:1])})" for f in result["potential_files"]], 5),
                 f"Estimated complexity (heuristic): {result['estimated_complexity']}"]
        return AgentReport(self.name, "\n".join(lines), files=[f["file"] for f in result["potential_files"]])
