"""Onboarding Agent: builds a learning roadmap from the real repository analysis."""
import logging
from typing import Optional

from app.agents.base import AgentContext, AgentReport, complexity_index, fmt_list, graph_stats, repo_label
from app.errors import AppError
from app.llm import ollama_client

logger = logging.getLogger("repopilot.onboarding")


def _difficulty(analysis: dict) -> dict:
    scan, stats = analysis["analysis"], graph_stats(analysis)
    summary = analysis.get("complexity", {}).get("summary", {})
    points, reasons = 0, []
    if scan.get("source_files", 0) > 200:
        points += 2
        reasons.append(f"+2: large codebase ({scan['source_files']} source files)")
    elif scan.get("source_files", 0) > 50:
        points += 1
        reasons.append(f"+1: medium codebase ({scan['source_files']} source files)")
    if summary.get("average_complexity", 0) > 30:
        points += 1
        reasons.append(f"+1: high average file complexity ({summary['average_complexity']})")
    if summary.get("max_complexity", 0) > 150:
        points += 1
        reasons.append(f"+1: some files are very complex (max {summary['max_complexity']})")
    if stats.get("nodes") and stats.get("edges", 0) / stats["nodes"] > 3:
        points += 1
        reasons.append("+1: densely connected modules")
    if len(scan.get("languages", {})) >= 5:
        points += 1
        reasons.append("+1: many languages in the repository")
    level = "Low" if points <= 1 else "Medium" if points <= 3 else "High"
    return {"level": level, "reasons": reasons or ["No factors increased the difficulty score."]}


def _setup_steps(scan: dict) -> list[str]:
    steps = []
    if scan.get("requirements") or any(p.endswith(("pyproject.toml", "setup.py")) for p in scan.get("package_files", [])):
        steps.append("Create a Python virtual environment and install the dependencies "
                     f"(detected: {fmt_list(scan.get('requirements', []) + scan.get('package_files', []), 4)}).")
    if any(p.endswith("package.json") for p in scan.get("package_files", [])):
        steps.append("Install JavaScript dependencies with npm (package.json detected).")
    if any(p.endswith(("pom.xml", "build.gradle")) for p in scan.get("package_files", [])):
        steps.append("Build the Java project with Maven or Gradle (build file detected).")
    return steps


def build_roadmap(analysis: dict) -> dict:
    scan, arch, stats = analysis["analysis"], analysis.get("architecture", {}), graph_stats(analysis)
    cx = complexity_index(analysis)
    entry = arch.get("entry_points", [])[:3]
    imported = [f["file"] for f in stats.get("most_imported_files", [])[:4]]
    central = [f["file"] for f in stats.get("central_files", [])[:3]]
    connected = [f["file"] for f in stats.get("most_connected_files", [])[:4]]
    tests = scan.get("tests", [])[:4]
    docs = scan.get("documentation", [])[:3]
    readme = scan.get("readme")

    reading: list[dict] = []

    def add(path: Optional[str], reason: str) -> None:
        if path and all(r["file"] != path for r in reading):
            reading.append({"file": path, "reason": reason})

    add(readme, "Project overview and setup instructions")
    for d in docs[:2]:
        add(d, "Project documentation")
    for e in entry:
        add(e, "Likely entry point of the application")
    for f in imported:
        add(f, "Imported by many other files: a core building block")
    for f in central:
        add(f, "Bridges different parts of the codebase (high betweenness)")
    for f in connected:
        add(f, "Highly connected module")
    for t in tests[:2]:
        add(t, "Tests show how the code is meant to be used")

    non_test = [c for c in analysis.get("complexity", {}).get("files", [])
                if c["file"] not in scan.get("tests", []) and c["lines"] >= 20]
    gentle = [c["file"] for c in sorted(non_test, key=lambda c: c["complexity"])[:3]]

    days = [
        {"day": 1, "title": "Understand the README and project structure",
         "description": "Get the big picture before reading any code.",
         "tasks": ["Read the README and documentation.",
                   f"Browse the top-level directories: {fmt_list(scan.get('top_level_directories', []), 10)}.",
                   f"Note the technologies: {fmt_list(arch.get('technologies', []), 8)}."],
         "files": [f for f in [readme] + docs if f]},
        {"day": 2, "title": "Understand the entry points",
         "description": "Find where execution starts and how the app is wired together.",
         "tasks": ["Read the entry point files and trace what they import.",
                   "Write down the main request/data flow in your own words."],
         "files": entry or connected[:2]},
        {"day": 3, "title": "Understand the core modules",
         "description": "Study the modules other files depend on most.",
         "tasks": ["Read the most imported modules first.", "List the main classes and functions in each."],
         "files": imported or connected[:3]},
        {"day": 4, "title": "Understand the dependencies",
         "description": "Learn how modules relate to each other.",
         "tasks": [f"The graph has {stats.get('nodes', 0)} files and {stats.get('edges', 0)} internal imports.",
                   "Open the dependency graph and follow the edges around the central files."],
         "files": central or connected[:3]},
        {"day": 5, "title": "Understand the tests",
         "description": "Tests document expected behaviour and show how to run checks.",
         "tasks": [f"{scan.get('counts', {}).get('tests', 0)} test files were detected.",
                   "Run the test suite locally and read a few tests for the core modules."],
         "files": tests},
        {"day": 6, "title": "Study contribution opportunities",
         "description": "Find small, well-scoped places to start.",
         "tasks": ["Read the contribution guide." if scan.get("contributing") else
                   "No CONTRIBUTING file was detected: check the README.",
                   "Files with lower approximate complexity are gentler places for a first change."],
         "files": ([scan["contributing"]] if scan.get("contributing") else []) + gentle},
        {"day": 7, "title": "Select an issue and begin implementation",
         "description": "Turn what you learned into a first contribution.",
         "tasks": ["Open the Issues page and pick an issue with a Low estimated complexity.",
                   "Reproduce it, make a small change, run the tests and open a pull request."],
         "files": []},
    ]

    steps = [f"Fork {repo_label(analysis)} and clone your fork."] + _setup_steps(scan)
    steps.append(f"Read {scan['contributing']} before making changes." if scan.get("contributing")
                 else "Check the README for contribution rules.")
    if scan.get("counts", {}).get("tests"):
        steps.append("Run the tests before and after your change.")
    steps += ["Create a branch, make a focused change, and commit with a clear message.",
              "Open a pull request that references the issue."]

    return {
        "repository": analysis.get("repository_id", ""),
        "difficulty": _difficulty(analysis),
        "architecture_overview": arch.get("summary", ""),
        "reading_order": reading[:12], "days": days, "contribution_steps": steps,
        "suggested_first_issue": None, "ai_summary": None, "notes": [],
    }


def add_ai_summary(roadmap: dict, analysis: dict) -> None:
    """Optional LLM narrative. Failure is reported in notes; the roadmap itself never depends on it."""
    facts = [f"Repository: {repo_label(analysis)}", f"Description: {analysis['repository'].get('description')}",
             f"Technologies: {fmt_list(analysis.get('architecture', {}).get('technologies', []), 10)}",
             f"Difficulty: {roadmap['difficulty']['level']}",
             "Reading order: " + fmt_list([r["file"] for r in roadmap["reading_order"]], 8),
             roadmap["architecture_overview"]]
    prompt = ("Write a short, friendly welcome (max 120 words) for a new developer joining this project. "
              "Use only these facts and do not invent anything:\n" + "\n".join(facts))
    try:
        roadmap["ai_summary"] = ollama_client.generate(prompt, temperature=0.3)
    except AppError as exc:
        logger.warning("AI summary skipped: %s", exc.message)
        roadmap["notes"].append(f"AI summary unavailable: {exc.message}")


class OnboardingAgent:
    name = "OnboardingAgent"

    def run(self, ctx: AgentContext) -> AgentReport:
        roadmap = build_roadmap(ctx.analysis)
        lines = [f"Estimated repository difficulty (heuristic): {roadmap['difficulty']['level']}",
                 "Recommended reading order:"]
        lines += [f"{i}. {r['file']} - {r['reason']}" for i, r in enumerate(roadmap["reading_order"][:8], 1)]
        lines.append("Contribution steps: " + " | ".join(roadmap["contribution_steps"][:6]))
        return AgentReport(self.name, "\n".join(lines), files=[r["file"] for r in roadmap["reading_order"][:6]])
