"""Static code analysis. Python uses the AST; JavaScript/TypeScript/Java use regular expressions.
Repository code is only READ as text - it is never executed or imported."""
import ast
import logging
import re
import warnings
from typing import Any

logger = logging.getLogger("repopilot.analyzer")

JS_LIKE = {"JavaScript", "JSX", "TypeScript", "TSX"}


def analyze_code(file: str, language: str, content: str) -> dict[str, Any]:
    """Return classes/functions/methods/imports for one file. Never raises: errors go into "errors"."""
    result: dict[str, Any] = {
        "file": file, "language": language, "lines": len(content.splitlines()),
        "classes": [], "functions": [], "methods": [],
        "imports": [], "import_targets": [], "errors": [],
    }
    try:
        if language == "Python":
            _analyze_python(content, result)
        elif language in JS_LIKE:
            _analyze_javascript(content, result)
        elif language == "Java":
            _analyze_java(content, result)
        else:
            result["errors"].append(f"Unsupported language: {language}")
    except Exception as exc:  # one bad file must never crash the whole repository analysis
        logger.warning("Could not fully analyze %s: %r", file, exc)
        result["errors"].append(f"{type(exc).__name__}: {exc}")
    result["imports"] = _unique(result["imports"])
    result["import_targets"] = _unique(result["import_targets"])
    return result


def _unique(items: list[str]) -> list[str]:
    return list(dict.fromkeys(items))


def _line_of(content: str, index: int) -> int:
    return content.count("\n", 0, index) + 1


def _block_end(content: str, start: int) -> int:
    """Index of the '}' closing the first '{' after start (approximate: ignores braces in strings)."""
    open_idx = content.find("{", start)
    if open_idx == -1:
        return start
    depth = 0
    for i in range(open_idx, len(content)):
        char = content[i]
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return i
    return len(content) - 1


# ----------------------------------------------------------------------------- Python
_PY_COMPOUND = (ast.If, ast.For, ast.AsyncFor, ast.While, ast.With, ast.AsyncWith, ast.Try)


def _analyze_python(content: str, result: dict) -> None:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")  # invalid escape sequences etc. in third-party code
        tree = ast.parse(content)

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                result["imports"].append(alias.name)
                result["import_targets"].append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            module = "." * node.level + (node.module or "")
            result["imports"].append(module)
            result["import_targets"].append(module)
            for alias in node.names:  # "from pkg import submodule" may point to a file
                if alias.name != "*":
                    joiner = "" if module.endswith(".") else "."
                    result["import_targets"].append(f"{module}{joiner}{alias.name}")
    _collect_python_definitions(tree.body, None, result)


def _collect_python_definitions(body: list, class_name: str | None, result: dict) -> None:
    for node in body:
        if isinstance(node, ast.ClassDef):
            result["classes"].append({
                "name": node.name, "start_line": node.lineno,
                "end_line": getattr(node, "end_lineno", node.lineno),
            })
            _collect_python_definitions(node.body, node.name, result)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            doc = (ast.get_docstring(node) or "").strip().split("\n")[0][:120]
            entry = {
                "name": node.name, "start_line": node.lineno,
                "end_line": getattr(node, "end_lineno", node.lineno),
                "async": isinstance(node, ast.AsyncFunctionDef),
                "args": [a.arg for a in node.args.args][:8], "docstring": doc,
            }
            if class_name:
                entry["class"] = class_name
                result["methods"].append(entry)
            else:
                result["functions"].append(entry)
        elif isinstance(node, _PY_COMPOUND):  # definitions inside if/try/with blocks
            for field in ("body", "orelse", "finalbody"):
                child = getattr(node, field, None)
                if isinstance(child, list):
                    _collect_python_definitions(child, class_name, result)
            for handler in getattr(node, "handlers", []):
                _collect_python_definitions(handler.body, class_name, result)


# ------------------------------------------------------------------- JavaScript / TypeScript
_JS_IMPORT_PATTERNS = [
    re.compile(r"""import\s+[^'";]*?\s*from\s*['"]([^'"]+)['"]"""),
    re.compile(r"""import\s*['"]([^'"]+)['"]"""),
    re.compile(r"""export\s+(?:\*|\{[^}]*\})\s*from\s*['"]([^'"]+)['"]"""),
    re.compile(r"""require\(\s*['"]([^'"]+)['"]\s*\)"""),
    re.compile(r"""import\(\s*['"]([^'"]+)['"]\s*\)"""),
]
_JS_CLASS_RE = re.compile(r"^[ \t]*(?:export\s+)?(?:default\s+)?(?:abstract\s+)?class\s+([A-Za-z_$][\w$]*)", re.M)
_JS_FUNCTION_RE = re.compile(
    r"^[ \t]*(?:export\s+)?(?:default\s+)?(?:async\s+)?function\s*\*?\s*([A-Za-z_$][\w$]*)\s*[<(]", re.M)
_JS_ARROW_RE = re.compile(
    r"^[ \t]*(?:export\s+)?(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*(?::[^=\n]+)?=\s*(?:async\s+)?"
    r"(?:\([^)]*\)|[A-Za-z_$][\w$]*)\s*(?::\s*[\w<>\[\]|,. ]+)?\s*=>", re.M)
_JS_METHOD_RE = re.compile(
    r"^[ \t]+(?:(?:public|private|protected|static|async|readonly|override|get|set|abstract)\s+)*"
    r"([A-Za-z_$#][\w$]*)\s*(?:<[^>\n]*>)?\s*\([^)]*\)\s*(?::\s*[^{;=\n]+)?\s*\{", re.M)
_JS_PROPERTY_ARROW_RE = re.compile(
    r"^[ \t]+(?:static\s+)?([A-Za-z_$][\w$]*)\s*=\s*(?:async\s+)?\([^)]*\)\s*=>", re.M)
_JS_KEYWORDS = {"if", "for", "while", "switch", "catch", "function", "return", "with", "else", "do", "try"}


def _analyze_javascript(content: str, result: dict) -> None:
    for pattern in _JS_IMPORT_PATTERNS:
        result["imports"].extend(pattern.findall(content))
    result["import_targets"] = list(result["imports"])

    for match in _JS_CLASS_RE.finditer(content):
        name = match.group(1)
        end_idx = _block_end(content, match.end())
        result["classes"].append({"name": name, "start_line": _line_of(content, match.start(1)),
                                  "end_line": _line_of(content, end_idx)})
        body_start = content.find("{", match.end())
        if body_start == -1 or body_start > end_idx:
            continue
        body = content[body_start:end_idx + 1]
        for regex in (_JS_METHOD_RE, _JS_PROPERTY_ARROW_RE):
            for m in regex.finditer(body):
                if m.group(1) in _JS_KEYWORDS:
                    continue
                depth = body.count("{", 0, m.start()) - body.count("}", 0, m.start())
                if depth != 1:  # only direct members of the class body
                    continue
                result["methods"].append({"name": m.group(1), "class": name,
                                          "start_line": _line_of(content, body_start + m.start(1))})

    for match in _JS_FUNCTION_RE.finditer(content):
        result["functions"].append({"name": match.group(1), "start_line": _line_of(content, match.start(1)),
                                    "kind": "function"})
    for match in _JS_ARROW_RE.finditer(content):
        result["functions"].append({"name": match.group(1), "start_line": _line_of(content, match.start(1)),
                                    "kind": "arrow"})
    result["functions"].sort(key=lambda f: f["start_line"])


# ------------------------------------------------------------------------------------ Java
_JAVA_IMPORT_RE = re.compile(r"^\s*import\s+(?:static\s+)?([\w.]+(?:\.\*)?)\s*;", re.M)
_JAVA_CLASS_RE = re.compile(
    r"^[ \t]*(?:@\w+(?:\([^)]*\))?\s+)*(?:(?:public|protected|private|abstract|final|static|sealed|strictfp)\s+)*"
    r"(?:class|interface|enum|record|@interface)\s+(?P<name>[A-Za-z_]\w*)", re.M)
_JAVA_METHOD_RE = re.compile(
    r"^[ \t]+(?:@\w+(?:\([^)]*\))?[ \t]+)*(?P<rtype>(?:[\w<>\[\],.?&]+[ \t]+)+?)(?P<name>[A-Za-z_]\w*)[ \t]*"
    r"\((?P<args>[^)]*)\)\s*(?:throws\s+[\w.,\s]+?\s*)?[{;]", re.M)
_JAVA_MODIFIERS = {"public", "protected", "private", "static", "final", "abstract", "synchronized", "native",
                   "default", "strictfp"}
_JAVA_NOT_TYPES = {"return", "new", "else", "throw", "case", "assert", "yield", "await"}
_JAVA_STATEMENTS = {"if", "for", "while", "switch", "catch", "synchronized", "return", "try"}


def _analyze_java(content: str, result: dict) -> None:
    result["imports"].extend(_JAVA_IMPORT_RE.findall(content))
    result["import_targets"] = list(result["imports"])

    spans: list[tuple[int, int, str]] = []
    for match in _JAVA_CLASS_RE.finditer(content):
        start = _line_of(content, match.start("name"))
        end = _line_of(content, _block_end(content, match.end()))
        spans.append((start, end, match.group("name")))
        result["classes"].append({"name": match.group("name"), "start_line": start, "end_line": end})

    for match in _JAVA_METHOD_RE.finditer(content):
        name = match.group("name")
        tokens = match.group("rtype").split()
        if name in _JAVA_STATEMENTS or tokens[-1] in _JAVA_NOT_TYPES or tokens[0] in _JAVA_NOT_TYPES:
            continue
        line = _line_of(content, match.start("name"))
        owners = [s for s in spans if s[0] <= line <= s[1]]
        if not owners:  # a "method" outside any class is almost certainly a false positive
            continue
        owner = min(owners, key=lambda s: s[1] - s[0])[2]
        is_constructor = all(t in _JAVA_MODIFIERS for t in tokens)
        result["methods"].append({"name": name, "class": owner, "start_line": line,
                                  "constructor": is_constructor})
