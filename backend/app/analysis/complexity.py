"""Approximate complexity metrics. These are heuristics, NOT exact cyclomatic complexity for every language."""
import ast
import re
import warnings
from typing import Any, Optional

_NOTE = ("Approximate: 1 + number of branching constructs (if/for/while/case/catch/boolean operators). "
         "Python uses the AST; other languages use regular expressions.")

_C_BRANCH_RE = re.compile(r"\b(?:if|for|while|case|catch)\b|&&|\|\||\?\?")
_PY_BRANCH_RE = re.compile(r"\b(?:if|elif|for|while|except|and|or)\b")
_NESTING_NODES = (ast.If, ast.For, ast.AsyncFor, ast.While, ast.Try, ast.With, ast.AsyncWith)


def _python_metrics(content: str) -> dict:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        tree = ast.parse(content)
    state = {"complexity": 1, "depth": 0}

    def walk(node: ast.AST, depth: int) -> None:
        for child in ast.iter_child_nodes(node):
            child_depth = depth
            if isinstance(child, (ast.If, ast.For, ast.AsyncFor, ast.While, ast.ExceptHandler, ast.IfExp)):
                state["complexity"] += 1
            elif isinstance(child, ast.BoolOp):
                state["complexity"] += len(child.values) - 1
            elif isinstance(child, ast.comprehension):
                state["complexity"] += 1 + len(child.ifs)
            elif type(child).__name__ == "match_case":
                state["complexity"] += 1
            if isinstance(child, _NESTING_NODES):
                is_elif = isinstance(node, ast.If) and isinstance(child, ast.If) and child in node.orelse \
                    and len(node.orelse) == 1
                if not is_elif:  # an "elif" chain is flat, not nested
                    child_depth = depth + 1
                state["depth"] = max(state["depth"], child_depth)
            walk(child, child_depth)

    walk(tree, 0)
    return {"complexity": state["complexity"], "max_nesting_depth": state["depth"], "method": "ast"}


def _strip_noise(content: str, language: str) -> str:
    """Remove string literals and comments so keywords inside them are not counted."""
    if language == "Python":
        text = re.sub(r'"""[\s\S]*?"""|\'\'\'[\s\S]*?\'\'\'', "", content)
        text = re.sub(r'"(?:\\.|[^"\\\n])*"|\'(?:\\.|[^\'\\\n])*\'', '""', text)
        return re.sub(r"#.*", "", text)
    text = re.sub(r'"(?:\\.|[^"\\\n])*"|\'(?:\\.|[^\'\\\n])*\'|`(?:\\.|[^`\\])*`', '""', content)
    text = re.sub(r"/\*[\s\S]*?\*/", "", text)
    return re.sub(r"//.*", "", text)


def _regex_metrics(content: str, language: str) -> dict:
    clean = _strip_noise(content, language)
    pattern = _PY_BRANCH_RE if language == "Python" else _C_BRANCH_RE
    complexity = 1 + len(pattern.findall(clean))
    if language == "Python":  # indentation based, assuming 4 spaces
        depth = max((len(l) - len(l.lstrip(" ")) for l in clean.splitlines() if l.strip()), default=0) // 4
    else:  # brace depth
        depth = current = 0
        for char in clean:
            if char == "{":
                current += 1
                depth = max(depth, current)
            elif char == "}":
                current = max(0, current - 1)
    return {"complexity": complexity, "max_nesting_depth": depth, "method": "regex"}


def compute_complexity(file: str, language: str, content: str, analysis: Optional[dict] = None) -> dict[str, Any]:
    lines = content.splitlines()
    metrics = None
    if language == "Python":
        try:
            metrics = _python_metrics(content)
        except (SyntaxError, ValueError, RecursionError):
            metrics = None  # fall back to regex when the file cannot be parsed
    if metrics is None:
        metrics = _regex_metrics(content, language)
    analysis = analysis or {}
    return {
        "file": file, "language": language,
        "complexity": metrics["complexity"], "lines": len(lines),
        "code_lines": sum(1 for l in lines if l.strip()),
        "functions": len(analysis.get("functions", [])), "classes": len(analysis.get("classes", [])),
        "methods": len(analysis.get("methods", [])),
        "branches": metrics["complexity"] - 1, "max_nesting_depth": metrics["max_nesting_depth"],
        "method": metrics["method"], "note": _NOTE,
    }


def summarize_complexity(items: list[dict]) -> dict:
    """Aggregate per-file metrics for the dashboard."""
    if not items:
        return {"total_files": 0, "average_complexity": 0, "max_complexity": 0, "total_lines": 0,
                "total_functions": 0, "total_classes": 0, "most_complex_files": []}
    ranked = sorted(items, key=lambda i: i["complexity"], reverse=True)
    return {
        "total_files": len(items),
        "average_complexity": round(sum(i["complexity"] for i in items) / len(items), 1),
        "max_complexity": ranked[0]["complexity"],
        "total_lines": sum(i["lines"] for i in items),
        "total_functions": sum(i["functions"] for i in items),
        "total_classes": sum(i["classes"] for i in items),
        "total_methods": sum(i["methods"] for i in items),
        "most_complex_files": [{k: i[k] for k in ("file", "complexity", "lines", "functions", "classes")}
                               for i in ranked[:10]],
    }
