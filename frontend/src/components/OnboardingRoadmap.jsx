import { ExternalLink } from "lucide-react";
import { complexityBadge } from "../utils/formatters";

export default function OnboardingRoadmap({ roadmap, onSelectFile }) {
  const issue = roadmap.suggested_first_issue;
  return (
    <div className="roadmap">
      <div className="card">
        <h3>Difficulty: <span className={`badge ${complexityBadge(roadmap.difficulty.level)}`}>{roadmap.difficulty.level}</span></h3>
        <ul className="plain-list small">{roadmap.difficulty.reasons.map((r, i) => <li key={i}>{r}</li>)}</ul>
        <p className="small">{roadmap.architecture_overview}</p>
        {roadmap.ai_summary && <blockquote className="ai-summary">{roadmap.ai_summary}</blockquote>}
      </div>

      <div className="card">
        <h3>Files to read, in order</h3>
        <ol className="reading-list">
          {roadmap.reading_order.map((r) => (
            <li key={r.file}>
              <button className="link-btn mono" onClick={() => onSelectFile?.(r.file)}>{r.file}</button>
              <span className="muted small"> — {r.reason}</span>
            </li>
          ))}
        </ol>
      </div>

      <div className="card">
        <h3>7-day plan</h3>
        <div className="day-grid">
          {roadmap.days.map((d) => (
            <div className="day" key={d.day}>
              <span className="day-num">Day {d.day}</span>
              <h4>{d.title}</h4>
              <p className="small muted">{d.description}</p>
              <ul className="plain-list small">{d.tasks.map((t, i) => <li key={i}>{t}</li>)}</ul>
              {d.files?.length > 0 && (
                <div className="chips">{d.files.map((f) => (
                  <button key={f} className="chip mono" onClick={() => onSelectFile?.(f)}>{f.split("/").pop()}</button>
                ))}</div>
              )}
            </div>
          ))}
        </div>
      </div>

      <div className="card">
        <h3>Contribution steps</h3>
        <ol className="small">{roadmap.contribution_steps.map((s, i) => <li key={i}>{s}</li>)}</ol>
        {issue && (
          <div className="first-issue">
            <b>Suggested first issue:</b>{" "}
            <a href={issue.html_url} target="_blank" rel="noreferrer">#{issue.number} {issue.title} <ExternalLink size={12} /></a>
            <span className={`badge ${complexityBadge(issue.estimated_complexity)}`}>{issue.estimated_complexity}</span>
          </div>
        )}
      </div>

      {roadmap.notes?.length > 0 && (
        <div className="card muted small"><b>Notes</b><ul className="plain-list">{roadmap.notes.map((n, i) => <li key={i}>{n}</li>)}</ul></div>
      )}
    </div>
  );
}
