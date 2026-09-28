import { useNavigate } from "react-router-dom";
import { Brain, GitBranch, Network, Route } from "lucide-react";
import { useRepository } from "../hooks/useRepository";
import RepositoryInput from "../components/RepositoryInput";
import LoadingState from "../components/LoadingState";
import ErrorMessage from "../components/ErrorMessage";

const FEATURES = [
  { icon: Network, title: "Dependency graph", text: "See how files import each other and which modules are central." },
  { icon: Brain, title: "Ask the code", text: "RAG over the repository with cited files and line ranges." },
  { icon: Route, title: "Onboarding roadmap", text: "A 7-day plan built from the real structure of the project." },
  { icon: GitBranch, title: "Issue analysis", text: "Find the files an issue likely touches and its difficulty." },
];

export default function Home() {
  const { analyze, loading, progress, error, setError, repo } = useRepository();
  const navigate = useNavigate();

  const submit = async (url) => {
    const data = await analyze(url);
    if (data) navigate("/repository");
  };

  return (
    <div className="home">
      <section className="hero">
        <h1>Understand any GitHub repository in minutes</h1>
        <p className="muted">RepoPilot analyzes code, maps dependencies, and lets you ask questions. It runs locally with Ollama, so no paid API keys are needed.</p>
        <RepositoryInput onSubmit={submit} disabled={loading} />
        <ErrorMessage message={error} onClose={() => setError("")} />
        {repo && !loading && (
          <p className="small">Currently loaded: <button className="link-btn" onClick={() => navigate("/repository")}>{repo.repository.full_name}</button></p>
        )}
      </section>
      {loading && <LoadingState step={progress.step} />}
      {!loading && (
        <section className="feature-grid">
          {FEATURES.map(({ icon: Icon, title, text }) => (
            <div className="card feature" key={title}>
              <Icon size={22} /><h4>{title}</h4><p className="muted small">{text}</p>
            </div>
          ))}
        </section>
      )}
    </div>
  );
}
