"""Architecture Agent: layers, components and communication flow, from detected evidence only."""
from app.agents.base import AgentContext, AgentReport, fmt_list


class ArchitectureAgent:
    name = "ArchitectureAgent"

    def run(self, ctx: AgentContext) -> AgentReport:
        arch = ctx.analysis.get("architecture", {})
        lines = [arch.get("summary", "No architecture information available."),
                 f"Technologies: {fmt_list(arch.get('technologies', []), 12)}",
                 f"Entry points: {fmt_list(arch.get('entry_points', []))}"]
        files: list[str] = list(arch.get("entry_points", [])[:2])
        for layer in arch.get("layers", []):
            if not layer["detected"]:
                continue
            evidence = fmt_list(layer["evidence"], 4)
            imports = fmt_list(layer["imports"], 4)
            lines.append(f"- {layer['name']}: evidence files [{evidence}]; imports [{imports}]")
            files += layer["evidence"][:1]
        lines.append("Only layers with evidence are listed; anything not listed was not detected.")
        return AgentReport(self.name, "\n".join(lines), files=files[:8], data={"layers": arch.get("layers", [])})
