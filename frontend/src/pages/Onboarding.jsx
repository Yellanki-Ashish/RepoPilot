import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { describeError, getRoadmap } from "../api/api";
import { useRepository } from "../hooks/useRepository";
import OnboardingRoadmap from "../components/OnboardingRoadmap";
import CodeViewer from "../components/CodeViewer";
import ErrorMessage from "../components/ErrorMessage";
import { InlineLoading } from "../components/LoadingState";

export default function Onboarding() {
  const { repo } = useRepository();
  const [roadmap, setRoadmap] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [file, setFile] = useState(null);
  const [aiSummary, setAiSummary] = useState(true);

  const id = repo?.repository_id;
  useEffect(() => { setRoadmap(null); setFile(null); }, [id]);

  if (!repo) {
    return (
      <div className="card center-msg">
        <p>Analyze a repository first to generate a roadmap.</p>
        <Link className="btn primary" to="/">Analyze a repository</Link>
      </div>
    );
  }

  const generate = async () => {
    setLoading(true);
    setError("");
    try {
      setRoadmap(await getRoadmap(id, aiSummary));
    } catch (err) {
      setError(describeError(err, "Could not generate the roadmap. Check backend logs."));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page">
      <div className="card toolbar">
        <div>
          <h3>Developer onboarding for {repo.repository.full_name}</h3>
          <p className="muted small">Built from the actual file structure, dependencies and complexity of this repository.</p>
        </div>
        <div className="toolbar-actions">
          <label className="small"><input type="checkbox" checked={aiSummary} onChange={(e) => setAiSummary(e.target.checked)} /> Include AI summary (needs Ollama)</label>
          <button className="btn primary" onClick={generate} disabled={loading}>{roadmap ? "Regenerate" : "Generate roadmap"}</button>
        </div>
      </div>
      <ErrorMessage message={error} onClose={() => setError("")} />
      {loading && <InlineLoading text="Building roadmap (this may take a moment)..." />}
      {roadmap && (
        <div className="assistant-layout">
          <OnboardingRoadmap roadmap={roadmap} onSelectFile={setFile} />
          {file && <CodeViewer repositoryId={id} file={file} onClose={() => setFile(null)} />}
        </div>
      )}
    </div>
  );
}
