"""Code Analyst Agent: symbols, imports and complexity of the relevant files."""
import re

from app.agents.base import AgentContext, AgentReport, code_index, complexity_index, fmt_list


def _symbol_map(index: dict[str, dict]) -> dict[str, list[tuple[str, str, int]]]:
    symbols: dict[str, list[tuple[str, str, int]]] = {}
    for path, a in index.items():
        for kind, key in (("class", "classes"), ("function", "functions"), ("method", "methods")):
            for item in a.get(key, []):
                symbols.setdefault(item["name"].lower(), []).append((path, kind, item["start_line"]))
    return symbols


class CodeAgent:
    name = "CodeAgent"

    def run(self, ctx: AgentContext) -> AgentReport:
        index, cx = code_index(ctx.analysis), complexity_index(ctx.analysis)
        lines: list[str] = []
        files: list[str] = []

        # 1) symbols mentioned in the question, e.g. "Explain the Session class"
        symbols = _symbol_map(index)
        for token in dict.fromkeys(re.findall(r"[A-Za-z_][A-Za-z0-9_]{2,}", ctx.question)):
            for path, kind, line in symbols.get(token.lower(), [])[:3]:
                lines.append(f"Symbol '{token}' is a {kind} defined in {path} at line {line}")
                files.append(path)
            if len(lines) >= 8:
                break

        # 2) structure of the files retrieved by the RAG agent
        seen: list[str] = []
        for r in ctx.rag_results:
            if r["file"] not in seen:
                seen.append(r["file"])
        for path in seen[:4]:
            a = index.get(path)
            if not a:
                continue
            files.append(path)
            m = cx.get(path, {})
            lines.append(
                f"{path} ({a['language']}, {a['lines']} lines, approx. complexity {m.get('complexity', '?')}): "
                f"classes [{fmt_list([c['name'] for c in a['classes']], 6)}], "
                f"functions [{fmt_list([f['name'] for f in a['functions']], 8)}], "
                f"methods [{fmt_list([x['class'] + '.' + x['name'] for x in a['methods']], 8)}], "
                f"imports [{fmt_list(a['imports'], 8)}]")

        # 3) complexity questions
        if re.search(r"complex|hardest|largest|biggest", ctx.question, re.I):
            top = ctx.analysis.get("complexity", {}).get("summary", {}).get("most_complex_files", [])[:6]
            lines.append("Most complex files (approximate, heuristic): " + fmt_list(
                [f"{t['file']} (complexity {t['complexity']}, {t['lines']} lines, {t['functions']} functions)"
                 for t in top], 6))
            files += [t["file"] for t in top[:3]]

        if not lines:
            lines.append("No specific symbols or files could be matched to the question.")
        return AgentReport(self.name, "\n".join(lines), files=list(dict.fromkeys(files)))
