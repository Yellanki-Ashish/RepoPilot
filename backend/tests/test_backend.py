"""Backend tests. They need no network, GitHub, Ollama or embedding model."""
import pytest
from fastapi.testclient import TestClient

from app.analysis.code_analyzer import analyze_code
from app.analysis.complexity import compute_complexity
from app.analysis.dependency_graph import build_dependency_graph
from app.errors import GitHubError
from app.ingestion.github_client import parse_github_url
from app.main import app
from app.rag.chunker import create_code_chunks
from app.rag.context_builder import build_context
from app.agents.orchestrator import plan_agents
from app.utils import collection_name, is_safe_relative_path, sanitize_name

client = TestClient(app)

PY_SOURCE = '''
import os
from .helpers import util
from . import auth

class Session:
    def send(self, data):
        if data and self.ok:
            for item in data:
                pass

async def fetch(url):
    return url
'''

JS_SOURCE = '''import React from "react";
import { api } from "./api/client";
const legacy = require("./legacy");
export class Store {
  constructor(x) { this.x = x; }
  async load(id) { return id; }
}
export function hello(name) { return name; }
export const arrow = async (a, b) => { return a + b; };
'''

JAVA_SOURCE = '''package demo;
import java.util.List;
import com.demo.model.User;
public class UserService {
    public UserService() { }
    public User find(String id) throws Exception {
        if (id == null) { return null; }
        return lookup(id);
    }
}
'''


def test_health_endpoint():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"
    assert "ollama" in resp.json()


def test_root_endpoint():
    assert client.get("/").json()["name"] == "RepoPilot"


def test_github_url_parsing():
    assert parse_github_url("https://github.com/psf/requests") == ("psf", "requests")
    assert parse_github_url("https://github.com/psf/requests.git") == ("psf", "requests")
    assert parse_github_url("https://github.com/psf/requests/tree/main/src") == ("psf", "requests")
    for bad in ["", "not a url", "https://gitlab.com/a/b", "https://github.com/onlyowner"]:
        with pytest.raises(GitHubError):
            parse_github_url(bad)


def test_name_sanitizing_and_path_safety():
    assert sanitize_name("psf/requests") == "psf_requests"
    assert collection_name("psf_requests") == "repo_psf_requests"
    assert not is_safe_relative_path("../secret")
    assert not is_safe_relative_path("/etc/passwd")
    assert is_safe_relative_path("src/app.py")


def test_python_analyzer_and_complexity():
    result = analyze_code("pkg/session.py", "Python", PY_SOURCE)
    assert [c["name"] for c in result["classes"]] == ["Session"]
    assert [f["name"] for f in result["functions"]] == ["fetch"]
    assert result["functions"][0]["async"] is True
    assert result["methods"][0]["name"] == "send"
    assert "os" in result["imports"] and ".helpers" in result["imports"]
    assert result["errors"] == []
    cx = compute_complexity("pkg/session.py", "Python", PY_SOURCE, result)
    assert cx["complexity"] >= 4 and cx["classes"] == 1


def test_bad_python_file_does_not_crash():
    result = analyze_code("broken.py", "Python", "def (:")
    assert result["errors"] and result["classes"] == []


def test_javascript_analyzer():
    result = analyze_code("src/store.js", "JavaScript", JS_SOURCE)
    assert [c["name"] for c in result["classes"]] == ["Store"]
    assert {f["name"] for f in result["functions"]} == {"hello", "arrow"}
    assert {m["name"] for m in result["methods"]} == {"constructor", "load"}
    assert {"react", "./api/client", "./legacy"} <= set(result["imports"])


def test_java_analyzer():
    result = analyze_code("src/UserService.java", "Java", JAVA_SOURCE)
    assert [c["name"] for c in result["classes"]] == ["UserService"]
    assert {m["name"] for m in result["methods"]} == {"UserService", "find"}
    assert "com.demo.model.User" in result["imports"]


def test_chunker_overlap_and_metadata():
    source = "\n".join(f"def f{i}():\n    return {i}\n" for i in range(60))
    analysis = analyze_code("big.py", "Python", source)
    chunks = create_code_chunks("big.py", "Python", source, analysis, max_lines=40, overlap=5)
    assert len(chunks) > 2
    assert chunks[0]["start_line"] == 1
    assert chunks[1]["start_line"] <= chunks[0]["end_line"]          # overlap
    assert chunks[-1]["end_line"] == len(source.splitlines())
    assert all(c["file"] == "big.py" and c["section"] and c["content"] for c in chunks)
    assert [c["chunk_index"] for c in chunks] == list(range(len(chunks)))


def test_dependency_graph():
    files = {"pkg/__init__.py": "", "pkg/a.py": "from . import b\nfrom pkg.c import X", "pkg/b.py": "",
             "pkg/c.py": "import os", "web/app.js": "import x from './lib/util'", "web/lib/util.js": "",
             "lonely.py": ""}
    analyses = [analyze_code(p, "JavaScript" if p.endswith(".js") else "Python", c) for p, c in files.items()]
    graph = build_dependency_graph(analyses)
    edges = {(e["source"], e["target"]) for e in graph["graph"]["edges"]}
    assert ("pkg/a.py", "pkg/b.py") in edges and ("pkg/a.py", "pkg/c.py") in edges
    assert ("web/app.js", "web/lib/util.js") in edges
    assert "lonely.py" in graph["statistics"]["isolated_files"]
    assert graph["statistics"]["nodes"] == len(files)
    assert graph["statistics"]["most_connected_files"][0]["file"] == "pkg/a.py"


def test_context_builder_limits_size():
    results = [{"file": f"f{i}.py", "start_line": 1, "end_line": 50, "section": "s", "content": "x = 1\n" * 300}
               for i in range(5)]
    built = build_context(results, max_chars=2500)
    assert len(built["context"]) <= 2500
    assert built["context"].startswith("--- SOURCE 1 ---")
    assert "File: f0.py" in built["context"] and "Lines: 1-50" in built["context"]


def test_agent_routing():
    assert plan_agents("Explain this repository architecture")[1] == ["RepositoryAgent", "ArchitectureAgent"]
    assert plan_agents("Which file is most important?")[1] == ["RepositoryAgent", "DependencyAgent"]
    assert plan_agents("How do I add Google login?")[1] == ["RAGAgent", "DependencyAgent", "CodeAgent",
                                                            "OnboardingAgent"]
    assert plan_agents("How does authentication work?")[1] == ["RAGAgent", "CodeAgent"]


def test_api_validation():
    assert client.post("/api/repository/analyze", json={}).status_code == 422
    bad = client.post("/api/repository/analyze", json={"url": "not-a-github-url"})
    assert bad.status_code == 400 and "Invalid GitHub URL" in bad.json()["detail"]
    assert client.post("/api/assistant/ask", json={"repository": "x", "question": "hi"}).status_code == 422
    assert client.get("/api/repository/never_analyzed_repo/graph").status_code == 404
    missing = client.post("/api/assistant/ask", json={"repository": "never_analyzed_repo",
                                                      "question": "How does auth work?"})
    assert missing.status_code == 404
