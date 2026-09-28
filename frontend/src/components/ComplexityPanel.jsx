import { fileName, dirName, formatNumber } from "../utils/formatters";

export default function ComplexityPanel({ complexity, onSelectFile }) {
  const s = complexity.summary;
  const max = s.max_complexity || 1;
  return (
    <div className="card">
      <h3>Code Statistics &amp; Most Complex Files</h3>
      <div className="mini-stats">
        <div><strong>{formatNumber(s.total_lines)}</strong><span>lines</span></div>
        <div><strong>{formatNumber(s.total_functions)}</strong><span>functions</span></div>
        <div><strong>{formatNumber(s.total_classes)}</strong><span>classes</span></div>
        <div><strong>{formatNumber(s.total_methods)}</strong><span>methods</span></div>
        <div><strong>{s.average_complexity}</strong><span>avg complexity</span></div>
      </div>
      <ul className="rank-list">
        {s.most_complex_files.slice(0, 8).map((f) => (
          <li key={f.file}>
            <button className="link-btn" onClick={() => onSelectFile?.(f.file)} title={f.file}>
              <b>{fileName(f.file)}</b> <span className="muted">{dirName(f.file)}</span>
            </button>
            <div className="bar"><i style={{ width: `${(f.complexity / max) * 100}%` }} /></div>
            <span className="rank-value">{f.complexity}</span>
          </li>
        ))}
      </ul>
      <p className="muted small">Approximate complexity = 1 + branching constructs (heuristic, not exact).</p>
    </div>
  );
}
