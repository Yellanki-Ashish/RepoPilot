export const ANALYSIS_STEPS = [
  "Scanning repository...",
  "Downloading source files...",
  "Analyzing source code...",
  "Building dependency graph...",
  "Creating code chunks...",
  "Generating embeddings...",
  "Indexing repository...",
  "Preparing AI assistant...",
];

export const formatNumber = (n) => new Intl.NumberFormat("en-US").format(n ?? 0);

export const formatCompact = (n) =>
  new Intl.NumberFormat("en-US", { notation: "compact", maximumFractionDigits: 1 }).format(n ?? 0);

export const fileName = (path = "") => path.split("/").pop();
export const dirName = (path = "") => (path.includes("/") ? path.slice(0, path.lastIndexOf("/")) : "");

export const formatLines = (s) => (s.start_line ? `Lines ${s.start_line}-${s.end_line}` : "Whole file");

export const LANGUAGE_COLORS = {
  Python: "#3776ab", JavaScript: "#f7df1e", JSX: "#61dafb", TypeScript: "#3178c6",
  TSX: "#38bdf8", Java: "#e76f00", Go: "#00add8", Rust: "#dea584", HTML: "#e34c26",
  CSS: "#563d7c", Markdown: "#94a3b8", JSON: "#a3a3a3", YAML: "#cb171e",
};
export const languageColor = (lang) => LANGUAGE_COLORS[lang] || "#818cf8";

export const complexityBadge = (level) =>
  ({ Low: "badge-green", Medium: "badge-amber", High: "badge-red" }[level] || "badge-gray");

export const SUGGESTED_QUESTIONS = [
  "How does authentication work?",
  "Explain the backend architecture.",
  "Which module is most connected?",
  "Find the most complex module.",
  "Which files should I read first?",
  "How does data flow through the application?",
  "Give me a contribution roadmap.",
  "Which files handle API requests?",
];
