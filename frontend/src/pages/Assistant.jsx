import { useState } from "react";
import { Link } from "react-router-dom";
import { useRepository } from "../hooks/useRepository";
import ChatPanel from "../components/ChatPanel";
import CodeViewer from "../components/CodeViewer";

export default function Assistant() {
  const { repo } = useRepository();
  const [source, setSource] = useState(null);

  if (!repo) {
    return (
      <div className="card center-msg">
        <p>Analyze a repository first to use the assistant.</p>
        <Link className="btn primary" to="/">Analyze a repository</Link>
      </div>
    );
  }
  return (
    <div className="assistant-layout">
      <ChatPanel repositoryId={repo.repository_id} onSelectSource={setSource} activeSource={source} />
      <CodeViewer repositoryId={repo.repository_id} file={source?.file} highlight={source} onClose={() => setSource(null)} />
    </div>
  );
}
