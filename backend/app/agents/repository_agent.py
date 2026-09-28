"""Repository Analyst Agent: structure, technologies and important directories."""
from app.agents.base import AgentContext, AgentReport, clip, fmt_list, graph_stats


class RepositoryAgent:
    name = "RepositoryAgent"

    def run(self, ctx: AgentContext) -> AgentReport:
        a = ctx.analysis
        info, scan, arch = a["repository"], a["analysis"], a.get("architecture", {})
        langs = ", ".join(f"{k} ({v})" for k, v in list(scan.get("languages", {}).items())[:6])
        important = [f["file"] for f in graph_stats(a).get("most_connected_files", [])[:5]]
        lines = [
            f"Repository: {info.get('full_name')} - {info.get('description') or 'no description'}",
            f"Stars: {info.get('stars')}, default branch: {info.get('default_branch')}",
            f"Files: {scan.get('files')}, folders: {scan.get('folders')}, "
            f"source files analyzed: {scan.get('analyzed_files')} of {scan.get('source_files')}",
            f"Languages (file counts): {langs or 'n/a'}",
            f"Top-level directories: {fmt_list(scan.get('top_level_directories', []), 15)}",
            f"Technologies detected: {fmt_list(arch.get('technologies', []), 12)}",
            f"Entry point candidates: {fmt_list(arch.get('entry_points', []))}",
            f"Most connected files: {fmt_list(important)}",
            f"Tests detected: {scan.get('counts', {}).get('tests', 0)} files; "
            f"docs: {scan.get('counts', {}).get('documentation', 0)}; "
            f"CI/CD files: {scan.get('counts', {}).get('ci_cd_files', 0)}",
        ]
        readme = a.get("key_files", {}).get("readme")
        if readme:
            lines.append("README excerpt:\n" + clip(readme, 1200))
        return AgentReport(self.name, "\n".join(lines),
                           files=arch.get("entry_points", [])[:3] + important)
