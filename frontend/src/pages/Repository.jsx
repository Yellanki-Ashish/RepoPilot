import { useState } from "react";
import { Link } from "react-router-dom";
import { RefreshCw, Trash2 } from "lucide-react";
import { useRepository } from "../hooks/useRepository";
import RepositoryOverview from "../components/RepositoryOverview";
import LanguageStats from "../components/LanguageStats";
import ComplexityPanel from "../components/ComplexityPanel";
import ArchitecturePanel from "../components/ArchitecturePanel";
import DependencyGraph from "../components/DependencyGraph";
import FileExplorer from "../components/FileExplorer";
import CodeViewer from "../components/CodeViewer";
import LoadingState from "../components/LoadingState";
import ErrorMessage from "../components/ErrorMessage";

export default function Repository() {
  const { repo, loading, progress, error, setError, analyze, remove } = useRepository();
  const [file, setFile] = useState(null);

  if (loading) return <LoadingState step={progress.step} />;
  if (!repo) {
    return (
      <div className="card center-msg">
        <p>No repository loaded yet.</p>
        <Link className="btn primary" to="/">Analyze a repository</Link>
      </div>
    );
  }

  const refresh = () => analyze(repo.repository.html_url, true);
  const languages = repo.analysis.languages;

  return (
    <div className="dashboard">
      <ErrorMessage message={error} onClose={() => setError("")} />
      <div className="toolbar">
        <span className="muted small">
          {repo.from_cache ? "Loaded from local cache" : "Freshly analyzed"}
          {repo.analyzed_at ? ` · ${new Date(repo.analyzed_at).toLocaleString()}` : ""}
        </span>
        <div>
          <button className="btn" onClick={refresh}><RefreshCw size={14} /> Re-analyze</button>{" "}
          <button className="btn danger" onClick={() => window.confirm("Delete this repository's data?") && remove()}>
            <Trash2 size={14} /> Delete
          </button>
        </div>
      </div>
      <RepositoryOverview repo={repo} />
      <div className="grid-2">
        <LanguageStats languages={languages} />
        <ArchitecturePanel architecture={repo.architecture} />
      </div>
      <div className="grid-2">
        <ComplexityPanel complexity={repo.complexity} onSelectFile={setFile} />
        <DependencyGraph dependency={repo.dependency_graph} onSelectFile={setFile} />
      </div>
      <div className="grid-explorer">
        <FileExplorer files={repo.code_analysis} selected={file} onSelect={setFile} />
        <CodeViewer repositoryId={repo.repository_id} file={file} onClose={() => setFile(null)} />
      </div>
    </div>
  );
}
