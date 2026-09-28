"""GitHub REST API client. The token (if any) stays on the backend."""
import logging
import re
from pathlib import Path
from typing import Any, Optional
from urllib.parse import quote

import requests

from app.config import settings
from app.errors import GitHubError
from app.utils import is_safe_relative_path, safe_join

logger = logging.getLogger("repopilot.github")

_URL_RE = re.compile(r"^https?://(?:www\.)?github\.com/([A-Za-z0-9-]{1,39})/([A-Za-z0-9._-]+)(?:/.*)?$")


def parse_github_url(url: str) -> tuple[str, str]:
    """Return (owner, repo) for URLs like https://github.com/psf/requests[.git|/tree/main]."""
    cleaned = (url or "").strip().split("#")[0].split("?")[0].rstrip("/")
    match = _URL_RE.match(cleaned)
    if not match:
        raise GitHubError(
            "Invalid GitHub URL. Use a link like https://github.com/psf/requests",
            status_code=400, code="invalid_url",
        )
    owner, repo = match.group(1), match.group(2)
    if repo.endswith(".git"):
        repo = repo[:-4]
    if repo in ("", ".", ".."):
        raise GitHubError("Invalid GitHub repository name.", status_code=400, code="invalid_url")
    return owner, repo


def _api_headers() -> dict[str, str]:
    headers = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28",
               "User-Agent": "RepoPilot"}
    if settings.GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {settings.GITHUB_TOKEN}"
    return headers


def _request(path: str, params: Optional[dict] = None) -> Any:
    url = f"{settings.GITHUB_API_URL}{path}"
    try:
        resp = requests.get(url, headers=_api_headers(), params=params, timeout=20)
    except requests.Timeout as exc:
        raise GitHubError("GitHub did not respond in time. Try again shortly.", 504, "github_timeout") from exc
    except requests.RequestException as exc:
        logger.error("GitHub network error: %r", exc)
        raise GitHubError("Could not reach GitHub. Check your internet connection.", 502, "github_network") from exc

    if resp.status_code == 200:
        return resp.json()
    if resp.status_code == 404:
        raise GitHubError("Repository or resource not found on GitHub (is it public?).", 404, "not_found")
    if resp.status_code == 409:
        raise GitHubError("This repository is empty.", 400, "empty_repository")
    if resp.status_code == 401:
        raise GitHubError("GitHub rejected the configured GITHUB_TOKEN. Fix or remove it in backend/.env.", 502, "github_auth")
    if resp.status_code in (403, 429):
        if resp.headers.get("X-RateLimit-Remaining") == "0" or resp.status_code == 429:
            raise GitHubError(
                "GitHub API rate limit reached. Add a GITHUB_TOKEN to backend/.env or try again later.",
                429, "github_rate_limit",
            )
        raise GitHubError("GitHub denied access to this resource.", 403, "github_forbidden")
    logger.error("GitHub API %s -> HTTP %s: %s", path, resp.status_code, resp.text[:200])
    raise GitHubError(f"GitHub API returned an unexpected status ({resp.status_code}).", 502, "github_error")


def get_repository(owner: str, repo: str) -> dict:
    data = _request(f"/repos/{owner}/{repo}")
    license_info = data.get("license") or {}
    return {
        "name": data.get("name", repo),
        "owner": (data.get("owner") or {}).get("login", owner),
        "full_name": data.get("full_name", f"{owner}/{repo}"),
        "description": data.get("description"),
        "default_branch": data.get("default_branch", "main"),
        "stars": data.get("stargazers_count", 0),
        "forks": data.get("forks_count", 0),
        "open_issues": data.get("open_issues_count", 0),
        "language": data.get("language"),
        "topics": data.get("topics", []),
        "html_url": data.get("html_url", f"https://github.com/{owner}/{repo}"),
        "license": license_info.get("spdx_id") or license_info.get("name"),
    }


def get_repository_tree(owner: str, repo: str, branch: str) -> dict:
    """Return {"tree": [{path, type, size}, ...], "truncated": bool}."""
    data = _request(f"/repos/{owner}/{repo}/git/trees/{quote(branch, safe='')}", {"recursive": "1"})
    return {"tree": data.get("tree", []), "truncated": bool(data.get("truncated", False))}


def get_file_content(owner: str, repo: str, path: str, branch: str,
                     cache_dir: Optional[Path] = None) -> str:
    """Download one text file (raw.githubusercontent.com, so it does not use API rate limit)."""
    if not is_safe_relative_path(path):
        raise GitHubError(f"Unsafe file path rejected: {path}", 400, "unsafe_path")

    cache_file = None
    if cache_dir is not None:
        cache_file = safe_join(cache_dir, path)
        if cache_file.is_file():
            return cache_file.read_text(encoding="utf-8", errors="replace")

    url = f"{settings.GITHUB_RAW_URL}/{owner}/{repo}/{quote(branch, safe='/')}/{quote(path)}"
    headers = {"User-Agent": "RepoPilot"}
    if settings.GITHUB_TOKEN:
        headers["Authorization"] = f"token {settings.GITHUB_TOKEN}"
    try:
        resp = requests.get(url, headers=headers, timeout=30)
    except requests.Timeout as exc:
        raise GitHubError(f"Timed out downloading {path}", 504, "github_timeout") from exc
    except requests.RequestException as exc:
        raise GitHubError(f"Network error downloading {path}", 502, "github_network") from exc

    if resp.status_code == 404:
        raise GitHubError(f"File not found: {path}", 404, "file_not_found")
    if resp.status_code != 200:
        raise GitHubError(f"Could not download {path} (HTTP {resp.status_code})", 502, "github_error")

    raw = resp.content
    if len(raw) > settings.MAX_FILE_SIZE_KB * 1024:
        raise GitHubError(f"File too large, skipped: {path}", 413, "file_too_large")
    if b"\x00" in raw[:8000]:
        raise GitHubError(f"Binary file skipped: {path}", 415, "binary_file")

    text = raw.decode("utf-8-sig", errors="replace").replace("\r\n", "\n")
    if cache_file is not None:
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        cache_file.write_text(text, encoding="utf-8")
    return text


def _simplify_issue(item: dict) -> dict:
    return {
        "number": item.get("number"),
        "title": item.get("title", ""),
        "body": (item.get("body") or "")[:4000],
        "labels": [l.get("name", "") for l in item.get("labels", []) if isinstance(l, dict)],
        "comments": item.get("comments", 0),
        "state": item.get("state", "open"),
        "html_url": item.get("html_url"),
        "user": (item.get("user") or {}).get("login"),
        "created_at": item.get("created_at"),
    }


def get_issues(owner: str, repo: str, state: str = "open", limit: int = 20) -> list[dict]:
    """List issues (pull requests are filtered out because GitHub mixes them in)."""
    per_page = min(100, max(limit * 2, 30))
    data = _request(f"/repos/{owner}/{repo}/issues", {"state": state, "per_page": per_page})
    issues = [_simplify_issue(i) for i in data if "pull_request" not in i]
    return issues[:limit]


def get_issue(owner: str, repo: str, number: int) -> dict:
    return _simplify_issue(_request(f"/repos/{owner}/{repo}/issues/{number}"))


def get_pull_request(owner: str, repo: str, number: int) -> dict:
    data = _request(f"/repos/{owner}/{repo}/pulls/{number}")
    return {
        "number": data.get("number"), "title": data.get("title", ""),
        "body": (data.get("body") or "")[:4000], "state": data.get("state"),
        "merged": data.get("merged", False), "html_url": data.get("html_url"),
        "changed_files": data.get("changed_files", 0),
    }


def get_pull_request_files(owner: str, repo: str, number: int) -> list[dict]:
    data = _request(f"/repos/{owner}/{repo}/pulls/{number}/files", {"per_page": 100})
    return [{"filename": f.get("filename"), "status": f.get("status"),
             "additions": f.get("additions", 0), "deletions": f.get("deletions", 0)} for f in data]
