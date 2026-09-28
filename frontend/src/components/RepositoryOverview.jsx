import { Database, FileCode, Folder, GitBranch, Layers, Star } from "lucide-react";
import { formatNumber } from "../utils/formatters";

const Stat = ({ icon: Icon, label, value }) => (
  <div className="stat">
    <Icon size={18} />
    <div><strong>{value}</strong><span>{label}</span></div>
  </div>
);

export default function RepositoryOverview({ repo }) {
  const { repository: r, analysis: a, rag } = repo;
  return (
    <div className="card overview">
      <div className="overview-head">
        <div>
          <h2><a href={r.html_url} target="_blank" rel="noreferrer">{r.full_name}</a></h2>
          <p className="muted">{r.description || "No description provided."}</p>
          <div className="chips">
            <span className="chip">Owner: {r.owner}</span>
            {r.license && <span className="chip">{r.license}</span>}
            {(r.topics || []).slice(0, 5).map((t) => <span className="chip" key={t}>{t}</span>)}
          </div>
        </div>
      </div>
      <div className="stat-grid">
        <Stat icon={Star} label="Stars" value={formatNumber(r.stars)} />
        <Stat icon={GitBranch} label="Default branch" value={r.default_branch} />
        <Stat icon={FileCode} label="Files" value={formatNumber(a.files)} />
        <Stat icon={Folder} label="Folders" value={formatNumber(a.folders)} />
        <Stat icon={Layers} label="Analyzed files" value={`${a.analyzed_files} / ${a.source_files}`} />
        <Stat icon={Database} label="Indexed chunks" value={formatNumber(rag.indexed_chunks)} />
      </div>
      {a.warnings?.length > 0 && (
        <details className="warnings">
          <summary>{a.warnings.length} analysis warning(s)</summary>
          <ul>{a.warnings.map((w, i) => <li key={i}>{w}</li>)}</ul>
        </details>
      )}
    </div>
  );
}
