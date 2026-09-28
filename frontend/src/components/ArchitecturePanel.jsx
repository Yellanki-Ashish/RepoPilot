import { CheckCircle2, MinusCircle } from "lucide-react";

const LABELS = { ci_cd: "CI/CD", controllers_routes: "Controllers / Routes", api: "API" };
const label = (n) => LABELS[n] || n.charAt(0).toUpperCase() + n.slice(1);

export default function ArchitecturePanel({ architecture }) {
  return (
    <div className="card">
      <h3>Architecture</h3>
      <p className="muted small">{architecture.summary}</p>
      {architecture.technologies.length > 0 && (
        <div className="chips">{architecture.technologies.map((t) => <span className="chip accent" key={t}>{t}</span>)}</div>
      )}
      <ul className="layer-list">
        {architecture.layers.map((l) => (
          <li key={l.name} className={l.detected ? "on" : "off"}>
            {l.detected ? <CheckCircle2 size={15} /> : <MinusCircle size={15} />}
            <span className="layer-name">{label(l.name)}</span>
            <span className="muted small layer-evidence" title={[...l.evidence, ...l.imports].join("\n")}>
              {l.detected ? l.evidence[0] || l.imports[0] : "not detected"}
            </span>
          </li>
        ))}
      </ul>
      {architecture.entry_points.length > 0 && (
        <p className="small"><b>Entry points:</b> {architecture.entry_points.join(", ")}</p>
      )}
    </div>
  );
}
