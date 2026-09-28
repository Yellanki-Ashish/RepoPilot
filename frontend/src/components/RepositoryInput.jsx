import { useState } from "react";
import { Search } from "lucide-react";

export default function RepositoryInput({ onSubmit, disabled }) {
  const [url, setUrl] = useState("");
  const submit = (e) => {
    e.preventDefault();
    if (url.trim()) onSubmit(url.trim());
  };
  return (
    <form className="repo-input" onSubmit={submit}>
      <Search size={18} className="repo-input-icon" />
      <input
        value={url}
        onChange={(e) => setUrl(e.target.value)}
        placeholder="https://github.com/psf/requests"
        disabled={disabled}
        aria-label="GitHub repository URL"
      />
      <button className="btn primary" type="submit" disabled={disabled || !url.trim()}>
        Analyze Repository
      </button>
    </form>
  );
}
