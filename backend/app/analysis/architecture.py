"""Architecture detection based only on evidence found in the repository (paths, imports, manifests)."""
import posixpath
import re

# name -> (path segments, file extensions, imported package names)
_LAYER_RULES: dict[str, dict] = {
    "frontend": {"segments": {"frontend", "client", "components", "pages", "public", "static", "templates"},
                 "exts": {".jsx", ".tsx", ".vue"},
                 "imports": {"react", "react-dom", "vue", "svelte", "next", "@angular/core"}},
    "backend": {"segments": {"backend", "server", "api", "app"},
                "exts": set(),
                "imports": {"fastapi", "flask", "django", "express", "koa", "tornado", "aiohttp",
                            "org.springframework"}},
    "api": {"segments": {"api", "routes", "routers", "endpoints", "controllers", "rest"},
            "exts": set(), "imports": {"fastapi", "flask", "express", "rest_framework", "flask_restful"}},
    "database": {"segments": {"db", "database", "migrations", "alembic", "prisma", "sql", "dao"},
                 "exts": {".sql"},
                 "imports": {"sqlalchemy", "sqlite3", "psycopg2", "pymongo", "mongoose", "sequelize", "typeorm",
                             "prisma", "peewee", "javax.persistence", "org.hibernate", "mysql", "pg", "redis"}},
    "authentication": {"segments": {"auth", "authentication", "login", "oauth", "security", "session", "sessions"},
                       "exts": set(),
                       "imports": {"jwt", "jsonwebtoken", "passport", "oauthlib", "authlib", "bcrypt",
                                   "flask_login", "org.springframework.security"}},
    "configuration": {"segments": {"config", "configs", "settings", "conf"}, "exts": set(), "imports": {"dotenv"}},
    "tests": {"segments": {"test", "tests", "__tests__", "spec", "specs"}, "exts": set(),
              "imports": {"pytest", "unittest", "jest", "mocha", "org.junit"}},
    "deployment": {"segments": {"deploy", "deployment", "k8s", "kubernetes", "helm", "terraform"},
                   "exts": set(), "imports": set()},
    "ci_cd": {"segments": {".github", ".circleci"}, "exts": set(), "imports": set()},
    "services": {"segments": {"services", "service"}, "exts": set(), "imports": set()},
    "controllers_routes": {"segments": {"routes", "routers", "controllers", "handlers", "views", "urls"},
                           "exts": set(), "imports": set()},
    "models": {"segments": {"models", "model", "entities", "entity", "schemas", "domain"},
               "exts": set(), "imports": {"pydantic"}},
    "repositories": {"segments": {"repositories", "repository", "repos"}, "exts": set(), "imports": set()},
    "utilities": {"segments": {"utils", "util", "helpers", "common", "lib", "shared"}, "exts": set(),
                  "imports": set()},
}

_FILE_EVIDENCE = {
    "deployment": re.compile(r"(^|/)(Dockerfile[^/]*|docker-compose[^/]*|Procfile|serverless\.yml|.*\.tf)$"),
    "ci_cd": re.compile(r"(^|/)(\.github/workflows/.*|\.gitlab-ci\.yml|Jenkinsfile|\.travis\.yml|azure-pipelines\.yml)$"),
    "configuration": re.compile(r"(^|/)(config\.[a-z]+|settings\.[a-z]+|\.env\.example|application\.(yml|properties))$"),
    "authentication": re.compile(r"(^|/)(auth|login|oauth|jwt)[^/]*\.(py|js|jsx|ts|tsx|java)$", re.I),
}

_TECH = {
    "Python": r"pyproject\.toml|setup\.py", "FastAPI": "fastapi", "Flask": "flask", "Django": "django",
    "SQLAlchemy": "sqlalchemy", "Pydantic": "pydantic", "Pytest": "pytest", "React": "react", "Vue": "vue",
    "Angular": "@angular/core", "Next.js": "next", "Express": "express", "Vite": "vite", "Jest": "jest",
    "TypeScript": "typescript", "Spring": "springframework|spring-boot", "Hibernate": "hibernate",
    "JUnit": "junit", "MongoDB": "mongoose|pymongo|mongodb", "PostgreSQL": "psycopg2|pg|postgresql",
    "Redis": "redis", "Tailwind CSS": "tailwindcss", "Requests": "requests", "NumPy": "numpy", "Pandas": "pandas",
}
_ENTRY_NAMES = {"main.py", "app.py", "__main__.py", "manage.py", "wsgi.py", "asgi.py", "cli.py", "server.js",
                "index.js", "app.js", "main.js", "index.ts", "main.ts", "server.ts", "index.jsx", "main.jsx",
                "index.tsx", "main.tsx", "Main.java", "Application.java", "App.java"}


def _import_roots(analyses: list[dict]) -> set[str]:
    roots: set[str] = set()
    for a in analyses:
        for imp in a.get("imports", []):
            if imp.startswith("."):
                continue
            roots.add(imp)
            if imp.startswith("@"):
                roots.add("/".join(imp.split("/")[:2]))
            else:
                roots.add(re.split(r"[./]", imp)[0])
                if a["language"] == "Java":
                    roots.add(".".join(imp.split(".")[:3]))
    return roots


def detect_architecture(all_paths: list[str], analyses: list[dict], key_files: dict) -> dict:
    roots = _import_roots(analyses)
    file_paths = [p for p in all_paths if not p.endswith("/")]
    layers = []
    for name, rule in _LAYER_RULES.items():
        evidence: list[str] = []
        for path in file_paths:
            segments = set(path.split("/")[:-1])
            ext = posixpath.splitext(path)[1].lower()
            file_re = _FILE_EVIDENCE.get(name)
            if (segments & rule["segments"]) or ext in rule["exts"] or (file_re and file_re.search(path)):
                evidence.append(path)
        import_hits = sorted(rule["imports"] & roots)
        detected = bool(evidence or import_hits)
        layers.append({
            "name": name, "detected": detected,
            "evidence_count": len(evidence) + len(import_hits),
            "evidence": evidence[:8], "imports": import_hits[:8],
        })

    manifest_text = " ".join(key_files.get("manifests", {}).values()).lower()
    path_text = " ".join(file_paths).lower()
    technologies = []
    for tech, keys in _TECH.items():
        found = False
        for key in keys.split("|"):
            if key in roots or re.search(rf"(?<![\w-]){re.escape(key)}(?![\w-])", manifest_text):
                found = True
            if key.endswith((".toml", ".py")) and re.search(key, path_text):
                found = True
        if found:
            technologies.append(tech)

    entry_points = [p for p in file_paths if posixpath.basename(p) in _ENTRY_NAMES]
    entry_points.sort(key=lambda p: (p.count("/"), p))
    detected_names = [l["name"] for l in layers if l["detected"]]
    summary = ("Detected layers based on file paths and imports: " + ", ".join(detected_names)
               if detected_names else "No common architectural layers were detected from paths or imports.")
    return {"layers": layers, "detected_layers": detected_names, "technologies": technologies,
            "entry_points": entry_points[:10], "summary": summary,
            "note": "Detection is heuristic and based only on file/folder names, imports and manifest files."}
