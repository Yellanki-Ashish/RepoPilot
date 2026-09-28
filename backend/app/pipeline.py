"""The full repository analysis pipeline (GitHub -> scan -> analyze -> graph -> chunks -> embeddings -> Chroma)."""
import logging
import shutil
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from typing import Optional

from app import progress, storage
from app.analysis import architecture, complexity, dependency_graph
from app.analysis.code_analyzer import analyze_code
from app.config import settings
from app.errors import AnalysisError, AppError
from app.ingestion import github_client, scanner
from app.rag import chunker, embeddings, vector_store
from app.utils import collection_name, make_repo_id

logger = logging.getLogger("repopilot.pipeline")
_MANIFESTS = {"package.json", "requirements.txt", "pyproject.toml", "pom.xml", "build.gradle", "setup.py"}


def _download(owner: str, repo: str, branch: str, paths: list[str], cache_dir, warnings: list[str]) -> dict[str, str]:
    """Download files in parallel. A failing file becomes a warning, not a crash."""
    def fetch(path: str) -> tuple[str, Optional[str], Optional[str]]:
        try:
            return path, github_client.get_file_content(owner, repo, path, branch, cache_dir), None
        except AppError as exc:
            return path, None, exc.message

    contents: dict[str, str] = {}
    with ThreadPoolExecutor(max_workers=max(1, settings.DOWNLOAD_WORKERS)) as pool:
        for path, text, error in pool.map(fetch, paths):
            if text is not None:
                contents[path] = text
            else:
                warnings.append(error or f"Could not download {path}")
    return contents


def _run(url: str, progress_id: Optional[str], force_refresh: bool) -> dict:
    owner, repo = github_client.parse_github_url(url)      # validates before any network call
    repo_id = make_repo_id(owner, repo)

    if not force_refresh:
        saved = storage.load_analysis(repo_id)
        if saved and vector_store.repository_exists(repo_id):
            saved["from_cache"] = True
            return saved
    else:
        storage.clear_file_cache(repo_id)
        shutil.rmtree(storage.repo_dir(repo_id) / "key_files", ignore_errors=True)

    started = time.time()
    warnings: list[str] = []

    progress.set_step(progress_id, 0)
    meta = github_client.get_repository(owner, repo)
    branch = meta["default_branch"]
    tree = github_client.get_repository_tree(owner, repo, branch)
    if tree["truncated"]:
        warnings.append("GitHub returned a truncated file tree (very large repository); results are partial.")
    scan = scanner.scan_repository(tree["tree"])
    selected, skipped = scanner.select_files_for_analysis(
        tree["tree"], settings.MAX_FILES_TO_ANALYZE, settings.MAX_FILE_SIZE_KB)
    if scan["files"] == 0:
        raise AnalysisError("This repository has no files.")
    if not selected:
        raise AnalysisError("No supported source files (Python, JavaScript, JSX, TypeScript, TSX, Java) "
                            "were found in this repository.")
    if skipped["over_limit"]:
        warnings.append(f"Only {len(selected)} files were analyzed (MAX_FILES_TO_ANALYZE); "
                        f"{skipped['over_limit']} more were skipped.")

    progress.set_step(progress_id, 1)
    cache_dir = storage.files_dir(repo_id)
    language_of = {e["path"]: scanner.language_for_path(e["path"]) for e in selected}
    contents = _download(owner, repo, branch, list(language_of), cache_dir, warnings)
    if not contents:
        raise AnalysisError("None of the source files could be downloaded. Check backend logs and GitHub limits.")
    # key files (README + manifests) used for architecture and onboarding
    manifest_paths = [p for p in scan["package_files"] + scan["requirements"]
                      if p.rsplit("/", 1)[-1] in _MANIFESTS or p.rsplit("/", 1)[-1].startswith("requirements")][:6]
    key_paths = ([scan["readme"]] if scan["readme"] else []) + manifest_paths
    key_texts = _download(owner, repo, branch, key_paths, cache_dir.parent / "key_files", [])
    key_files = {"readme": (key_texts.get(scan["readme"], "")[:6000] if scan["readme"] else ""),
                 "manifests": {p: key_texts[p][:4000] for p in manifest_paths if p in key_texts}}

    progress.set_step(progress_id, 2)
    analyses, complexities = [], []
    for path, text in contents.items():
        a = analyze_code(path, language_of[path], text)
        analyses.append(a)
        complexities.append(complexity.compute_complexity(path, language_of[path], text, a))
        if a["errors"]:
            warnings.append(f"{path}: {a['errors'][0]}")

    progress.set_step(progress_id, 3)
    graph = dependency_graph.build_dependency_graph(analyses)
    arch = architecture.detect_architecture([e["path"] for e in tree["tree"] if e["type"] == "blob"],
                                            analyses, key_files)

    progress.set_step(progress_id, 4)
    analysis_by_file = {a["file"]: a for a in analyses}
    chunks: list[dict] = []
    for path, text in contents.items():
        chunks.extend(chunker.create_code_chunks(path, language_of[path], text, analysis_by_file[path]))
    if not chunks:
        raise AnalysisError("No code chunks could be created from this repository.")

    progress.set_step(progress_id, 5)
    vectors = embeddings.embed_texts([f"{c['file']} | {c['section']}\n{c['content']}" for c in chunks])

    progress.set_step(progress_id, 6)
    indexed = vector_store.add_chunks(repo_id, chunks, vectors)

    progress.set_step(progress_id, 7)
    result = {
        "repository_id": repo_id,
        "repository": meta,
        "analysis": {
            **scan, "analyzed_files": len(contents), "skipped": skipped, "warnings": warnings[:30],
            "analysis_seconds": round(time.time() - started, 1),
        },
        "code_analysis": analyses,
        "complexity": {"summary": complexity.summarize_complexity(complexities), "files": complexities},
        "dependency_graph": graph,
        "architecture": arch,
        "key_files": key_files,
        "rag": {"indexed_chunks": indexed, "embedding_model": settings.EMBEDDING_MODEL,
                "collection": collection_name(repo_id)},
        "from_cache": False,
        "analyzed_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    storage.save_analysis(repo_id, result)
    return result


def analyze_repository(url: str, progress_id: Optional[str] = None, force_refresh: bool = False) -> dict:
    try:
        result = _run(url, progress_id, force_refresh)
    except AppError as exc:
        progress.finish(progress_id, False, exc.message)
        raise
    except Exception as exc:
        progress.finish(progress_id, False, "Repository analysis failed.")
        logger.exception("Analysis crashed: %r", exc)
        raise
    progress.finish(progress_id, True)
    return result
