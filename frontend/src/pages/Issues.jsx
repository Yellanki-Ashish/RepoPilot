import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { analyzeIssue, describeError } from "../api/api";
import { useRepository } from "../hooks/useRepository";
import IssuePanel from "../components/IssuePanel";
import CodeViewer from "../components/CodeViewer";
import ErrorMessage from "../components/ErrorMessage";
import { InlineLoading } from "../components/LoadingState";

export default function Issues() {
  const { repo } = useRepository();
  const [issues, setIssues] = useState([]);
  const [number, setNumber] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [file, setFile] = useState(null);
  const id = repo?.repository_id;

  useEffect(() => { setIssues([]); setFile(null); setError(""); }, [id]);

  if (!repo) {
    return (
      <div className="card center-msg">
        <p>Analyze a repository first to analyze its issues.</p>
        <Link className="btn primary" to="/">Analyze a repository</Link>
      </div>
    );
  }

  const run = async (single) => {
    setLoading(true);
    setError("");
    try {
      const n = single ? parseInt(number, 10) : null;
      if (single && (!n || n < 1)) throw new Error("Enter a valid issue number.");
      const res = await analyzeIssue(id, n, 10);
      setIssues(res.issues);
      if (res.issues.length === 0) setError("No issues were found.");
    } catch (err) {
      setError(err.response ? describeError(err, "Issue analysis failed. Check backend logs.") : err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page">
      <div className="card toolbar">
        <div>
          <h3>Issue analyzer</h3>
          <p className="muted small">Finds related files and gives a transparent difficulty estimate. GitHub rate limits apply without a token.</p>
        </div>
        <div className="toolbar-actions">
          <input className="num-input" type="number" min="1" placeholder="Issue #" value={number} onChange={(e) => setNumber(e.target.value)} />
          <button className="btn" onClick={() => run(true)} disabled={loading || !number}>Analyze issue</button>
          <button className="btn primary" onClick={() => run(false)} disabled={loading}>Analyze latest open issues</button>
        </div>
      </div>
      <ErrorMessage message={error} onClose={() => setError("")} />
      {loading && <InlineLoading text="Analyzing issues..." />}
      <div className="assistant-layout">
        <div className="issue-list">
          {issues.map((i) => <IssuePanel key={i.number} issue={i} onSelectFile={setFile} />)}
        </div>
        {file && <CodeViewer repositoryId={id} file={file} onClose={() => setFile(null)} />}
      </div>
    </div>
  );
}
