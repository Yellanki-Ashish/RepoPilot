"""Dependency graph: nodes are analyzed files, edges are resolved import relationships."""
import posixpath
from typing import Optional

import networkx as nx

_JS_EXTS = [".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs", ".json"]


def _python_index(paths: list[str]) -> dict[str, str]:
    """Map dotted module names -> file path, including suffixes so src/ and monorepo layouts resolve."""
    index: dict[str, str] = {}
    for path in sorted((p for p in paths if p.endswith(".py")), key=lambda p: (p.count("/"), p)):
        parts = path[:-3].split("/")
        is_package = parts[-1] == "__init__"
        if is_package:
            parts = parts[:-1]
        if not parts:
            continue
        for start in range(len(parts)):
            suffix = parts[start:]
            # single-name suffixes only for packages / top-level modules, to avoid matching stdlib names
            if len(suffix) == 1 and not (is_package or start == 0):
                continue
            index.setdefault(".".join(suffix), path)
    return index


def _resolve_python(source: str, target: str, index: dict[str, str], pathset: set[str]) -> Optional[str]:
    if target.startswith("."):
        level = len(target) - len(target.lstrip("."))
        rest = target[level:]
        base = source.split("/")[:-1]
        if level - 1 > len(base):
            return None
        if level - 1:
            base = base[: len(base) - (level - 1)]
        parts = base + (rest.split(".") if rest else [])
        joined = "/".join(parts)
        for candidate in (f"{joined}.py", f"{joined}/__init__.py"):
            if candidate in pathset:
                return candidate
        return None
    return index.get(target)


def _resolve_js(source: str, spec: str, pathset: set[str]) -> Optional[str]:
    if not spec.startswith("."):
        return None  # bare imports are external packages
    base = posixpath.normpath(posixpath.join(posixpath.dirname(source), spec))
    candidates = [base] + [base + e for e in _JS_EXTS] + [f"{base}/index{e}" for e in _JS_EXTS]
    if base.endswith(".js"):  # TypeScript ESM style: import "./a.js" refers to a.ts
        candidates += [base[:-3] + e for e in (".ts", ".tsx", ".jsx")]
    return next((c for c in candidates if c in pathset), None)


def _java_index(paths: list[str]) -> dict[str, str]:
    index: dict[str, str] = {}
    for path in sorted((p for p in paths if p.endswith(".java")), key=lambda p: (p.count("/"), p)):
        parts = path[:-5].split("/")
        for start in range(len(parts) - 1):
            index.setdefault(".".join(parts[start:]), path)
    return index


def _resolve_java(spec: str, index: dict[str, str]) -> Optional[str]:
    if spec.endswith(".*"):
        return None
    parts = spec.split(".")
    while len(parts) >= 2:  # also handles nested classes and static imports
        found = index.get(".".join(parts))
        if found:
            return found
        parts = parts[:-1]
    return None


def build_dependency_graph(analyses: list[dict]) -> dict:
    """Build the graph and statistics from per-file analysis results."""
    paths = [a["file"] for a in analyses]
    pathset = set(paths)
    py_index = _python_index(paths)
    java_index = _java_index(paths)

    graph = nx.DiGraph()
    for a in analyses:
        graph.add_node(a["file"], language=a["language"])

    for a in analyses:
        source = a["file"]
        targets = a.get("import_targets") or a.get("imports") or []
        for target in targets:
            if a["language"] == "Python":
                resolved = _resolve_python(source, target, py_index, pathset)
            elif a["language"] == "Java":
                resolved = _resolve_java(target, java_index)
            else:
                resolved = _resolve_js(source, target, pathset)
            if resolved and resolved != source:
                graph.add_edge(source, resolved)

    n_nodes, n_edges = graph.number_of_nodes(), graph.number_of_edges()
    in_deg, out_deg = dict(graph.in_degree()), dict(graph.out_degree())

    def entry(node: str) -> dict:
        return {"file": node, "connections": in_deg[node] + out_deg[node],
                "in_degree": in_deg[node], "out_degree": out_deg[node]}

    most_connected = sorted((entry(n) for n in graph.nodes), key=lambda e: (-e["connections"], e["file"]))
    most_imported = sorted((entry(n) for n in graph.nodes), key=lambda e: (-e["in_degree"], e["file"]))
    betweenness = nx.betweenness_centrality(graph) if n_edges else {}
    central = sorted(((n, s) for n, s in betweenness.items() if s > 0), key=lambda kv: -kv[1])[:10]
    isolated = sorted(n for n in graph.nodes if in_deg[n] == 0 and out_deg[n] == 0)

    return {
        "statistics": {
            "nodes": n_nodes, "edges": n_edges,
            "density": round(nx.density(graph), 4) if n_nodes > 1 else 0,
            "most_connected_files": [e for e in most_connected if e["connections"] > 0][:10],
            "most_imported_files": [e for e in most_imported if e["in_degree"] > 0][:10],
            "central_files": [{"file": n, "centrality": round(s, 4), **{
                "in_degree": in_deg[n], "out_degree": out_deg[n]}} for n, s in central],
            "isolated_files": isolated[:50], "isolated_count": len(isolated),
        },
        "graph": {
            "nodes": [{"id": n, "language": graph.nodes[n].get("language"),
                       "in_degree": in_deg[n], "out_degree": out_deg[n]} for n in graph.nodes],
            "edges": [{"source": s, "target": t} for s, t in graph.edges],
        },
    }


def neighbors(graph_data: dict, file: str) -> dict:
    """Files imported by `file` and files that import it."""
    edges = graph_data.get("graph", {}).get("edges", [])
    return {"imports": sorted(e["target"] for e in edges if e["source"] == file),
            "imported_by": sorted(e["source"] for e in edges if e["target"] == file)}
