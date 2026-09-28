"""Dependency Analyst Agent: connectivity of modules from the dependency graph."""
from app.agents.base import AgentContext, AgentReport, find_file_in_text, fmt_list, graph_stats
from app.analysis.dependency_graph import neighbors


class DependencyAgent:
    name = "DependencyAgent"

    def run(self, ctx: AgentContext) -> AgentReport:
        graph = ctx.analysis.get("dependency_graph", {})
        stats = graph_stats(ctx.analysis)
        lines = [f"Dependency graph: {stats.get('nodes', 0)} files, {stats.get('edges', 0)} internal import edges."]
        connected = stats.get("most_connected_files", [])[:6]
        imported = stats.get("most_imported_files", [])[:6]
        central = stats.get("central_files", [])[:5]
        lines.append("Most connected (in+out): " + fmt_list(
            [f"{f['file']} ({f['connections']})" for f in connected], 6))
        lines.append("Most imported by other files: " + fmt_list(
            [f"{f['file']} ({f['in_degree']})" for f in imported], 6))
        lines.append("Central bridge files (betweenness): " + fmt_list([f["file"] for f in central], 5))
        lines.append(f"Isolated files (no internal imports either way): {stats.get('isolated_count', 0)}")

        files = [f["file"] for f in connected[:3]]
        paths = [n["id"] for n in graph.get("graph", {}).get("nodes", [])]
        mentioned = find_file_in_text(ctx.question, paths)
        if mentioned:
            rel = neighbors(graph, mentioned)
            lines.append(f"{mentioned} imports: {fmt_list(rel['imports'], 10)}")
            lines.append(f"{mentioned} is imported by: {fmt_list(rel['imported_by'], 10)}")
            files.insert(0, mentioned)
        return AgentReport(self.name, "\n".join(lines), files=files)
