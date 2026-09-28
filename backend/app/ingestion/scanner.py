"""Repository scanner: classifies files from the GitHub tree (no code is executed)."""
import posixpath
import re
from typing import Optional

LANGUAGE_BY_EXT = {
    ".py": "Python", ".js": "JavaScript", ".mjs": "JavaScript", ".cjs": "JavaScript",
    ".jsx": "JSX", ".ts": "TypeScript", ".tsx": "TSX", ".java": "Java",
    # Counted in statistics only (not analyzed in depth)
    ".go": "Go", ".rs": "Rust", ".rb": "Ruby", ".php": "PHP", ".c": "C", ".h": "C",
    ".cpp": "C++", ".cc": "C++", ".hpp": "C++", ".cs": "C#", ".kt": "Kotlin", ".swift": "Swift",
    ".scala": "Scala", ".html": "HTML", ".css": "CSS", ".scss": "SCSS", ".vue": "Vue",
    ".sh": "Shell", ".sql": "SQL", ".md": "Markdown", ".rst": "reStructuredText",
    ".json": "JSON", ".yml": "YAML", ".yaml": "YAML", ".toml": "TOML", ".xml": "XML",
}
SUPPORTED_LANGUAGES = {"Python", "JavaScript", "JSX", "TypeScript", "TSX", "Java"}

EXCLUDED_DIRS = {
    "node_modules", "vendor", "dist", "build", "target", ".git", "__pycache__", "venv", ".venv",
    "env", "site-packages", ".next", ".nuxt", "coverage", "third_party", "bower_components", ".tox",
}
SECONDARY_DIRS = {"docs", "doc", "examples", "example", "scripts", "benchmarks", "samples", "demo"}
TEST_DIRS = {"test", "tests", "__tests__", "spec", "specs", "testing"}
TEST_FILE_RE = re.compile(r"(^test_.*\.py$|_test\.(py|go)$|\.(test|spec)\.(js|jsx|ts|tsx)$|Tests?\.java$)")
CONFIG_NAMES = {".env.example", ".eslintrc", ".eslintrc.json", ".prettierrc", "tsconfig.json", "vite.config.js",
                "webpack.config.js", "babel.config.js", "tox.ini", "setup.cfg", "pytest.ini", "Makefile",
                "application.properties", "application.yml", ".editorconfig", "pyproject.toml"}
CONFIG_EXTS = {".yml", ".yaml", ".toml", ".ini", ".cfg", ".conf", ".properties"}
PACKAGE_NAMES = {"package.json", "pom.xml", "build.gradle", "setup.py", "pyproject.toml", "Pipfile", "setup.cfg"}
DOC_EXTS = {".md", ".rst", ".txt"}


def language_for_path(path: str) -> Optional[str]:
    return LANGUAGE_BY_EXT.get(posixpath.splitext(path)[1].lower())


def is_excluded(path: str) -> bool:
    parts = path.split("/")
    if any(p in EXCLUDED_DIRS for p in parts[:-1]):
        return True
    name = parts[-1]
    return name.endswith(".min.js") or name.endswith(".d.ts") or name.endswith(".bundle.js")


def is_test_file(path: str) -> bool:
    parts = path.split("/")
    return any(p in TEST_DIRS for p in parts[:-1]) or bool(TEST_FILE_RE.search(parts[-1]))


def scan_repository(tree: list[dict]) -> dict:
    """Summarize the repository tree: counts, languages and categorized file lists."""
    blobs = [e for e in tree if e.get("type") == "blob"]
    folders = [e for e in tree if e.get("type") == "tree"]
    languages: dict[str, int] = {}
    lists: dict[str, list[str]] = {k: [] for k in
                                   ("documentation", "configuration", "tests", "package_files",
                                    "requirements", "docker_files", "ci_cd_files")}
    readme: Optional[str] = None
    contributing: Optional[str] = None
    source_files = 0
    total_size = 0

    for entry in blobs:
        path = entry["path"]
        name = posixpath.basename(path)
        ext = posixpath.splitext(name)[1].lower()
        total_size += entry.get("size", 0) or 0
        if is_excluded(path):
            continue
        lang = language_for_path(path)
        if lang:
            languages[lang] = languages.get(lang, 0) + 1
        if lang in SUPPORTED_LANGUAGES:
            source_files += 1
        if readme is None and name.lower().startswith("readme") and path.count("/") == 0:
            readme = path
        if contributing is None and name.lower().startswith("contributing"):
            contributing = path
        if ext in DOC_EXTS and (path.count("/") == 0 or path.split("/")[0].lower() in {"docs", "doc"}):
            lists["documentation"].append(path)
        if name in CONFIG_NAMES or ext in CONFIG_EXTS:
            lists["configuration"].append(path)
        if is_test_file(path):
            lists["tests"].append(path)
        if name in PACKAGE_NAMES:
            lists["package_files"].append(path)
        if re.match(r"requirements.*\.txt$", name):
            lists["requirements"].append(path)
        if name.startswith("Dockerfile") or name.startswith("docker-compose") or name == ".dockerignore":
            lists["docker_files"].append(path)
        if (path.startswith(".github/workflows/") or name in {".gitlab-ci.yml", "Jenkinsfile", ".travis.yml",
                                                                "azure-pipelines.yml"}
                or path.startswith(".circleci/")):
            lists["ci_cd_files"].append(path)

    top_dirs = sorted({e["path"] for e in folders if "/" not in e["path"] and e["path"] not in EXCLUDED_DIRS})
    return {
        "files": len(blobs),
        "folders": len(folders),
        "languages": dict(sorted(languages.items(), key=lambda kv: kv[1], reverse=True)),
        "source_files": source_files,
        "readme": readme,
        "contributing": contributing,
        "top_level_directories": top_dirs[:40],
        "total_size_kb": round(total_size / 1024, 1),
        **{k: v[:60] for k, v in lists.items()},
        "counts": {k: len(v) for k, v in lists.items()},
    }


def _priority(path: str) -> tuple:
    parts = path.split("/")
    secondary = is_test_file(path) or any(p.lower() in SECONDARY_DIRS for p in parts[:-1])
    return (int(secondary), len(parts) - 1, path)


def select_files_for_analysis(tree: list[dict], max_files: int, max_size_kb: int) -> tuple[list[dict], dict]:
    """Pick supported source files, preferring shallow non-test files, within the configured limits."""
    skipped = {"excluded": 0, "too_large": 0, "empty": 0, "over_limit": 0}
    candidates: list[dict] = []
    for entry in tree:
        if entry.get("type") != "blob":
            continue
        path = entry["path"]
        if language_for_path(path) not in SUPPORTED_LANGUAGES:
            continue
        if is_excluded(path):
            skipped["excluded"] += 1
            continue
        size = entry.get("size", 0) or 0
        if size > max_size_kb * 1024:
            skipped["too_large"] += 1
            continue
        if size == 0:
            skipped["empty"] += 1
            continue
        candidates.append(entry)
    candidates.sort(key=lambda e: _priority(e["path"]))
    selected = candidates[:max_files]
    skipped["over_limit"] = len(candidates) - len(selected)
    return selected, skipped
