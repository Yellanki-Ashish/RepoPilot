import { useState } from "react";
import { ExternalLink } from "lucide-react";
import { complexityBadge } from "../utils/formatters";

export default function IssuePanel({ issue, onSelectFile }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="card issue">
      <div className="issue-head">
        <div>
          <h4>
            <a href={issue.html_url} target="_blank" rel="noreferrer">#{issue.number} {issue.title} <ExternalLink size={12} /></a>
          </h4>
          <div className="chips">{(issue.labels || []).map((l) => <span className="chip" key={l}>{l}</span>)}</div>
        </div>
        <span className={`badge ${complexityBadge(issue.estimated_complexity)}`}>{issue.estimated_complexity}</span>
      </div>
      {issue.body_excerpt && <p className="small muted">{issue.body_excerpt}{issue.body_excerpt.length >= 400 ? "…" : ""}</p>}
      <p className="small"><b>Potentially related files</b></p>
      {issue.potential_files?.length ? (
        <ul className="plain-list small">
          {issue.potential_files.slice(0, 6).map((f, i) => {
            const path = f.file || f;
            return (
              <li key={i}>
                <button className="link-btn mono" onClick={() => onSelectFile?.(path)}>{path}</button>
                {f.reasons?.[0] && <span className="muted"> — {f.reasons[0]}</span>}
              </li>
            );
          })}
        </ul>
      ) : <p className="muted small">No matching files found.</p>}
      <button className="link-btn small" onClick={() => setOpen(!open)}>{open ? "Hide" : "Show"} complexity reasoning</button>
      {open && (
        <div className="small">
          <ul className="plain-list">{issue.reasoning?.map((r, i) => <li key={i}>{r}</li>)}</ul>
          <p className="muted">{issue.disclaimer}</p>
        </div>
      )}
    </div>
  );
}
