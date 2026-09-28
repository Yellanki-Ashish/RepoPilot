import { useMemo, useState } from "react";
import { FileCode, Search } from "lucide-react";
import { dirName, fileName, languageColor } from "../utils/formatters";

export default function FileExplorer({ files, selected, onSelect }) {
  const [filter, setFilter] = useState("");
  const shown = useMemo(() => {
    const q = filter.toLowerCase();
    return [...files].filter((f) => f.file.toLowerCase().includes(q)).sort((a, b) => a.file.localeCompare(b.file));
  }, [files, filter]);
  return (
    <div className="card explorer">
      <h3>File Explorer <span className="muted small">({files.length} analyzed)</span></h3>
      <div className="search-box"><Search size={14} /><input placeholder="Filter files..." value={filter} onChange={(e) => setFilter(e.target.value)} /></div>
      <ul className="file-list">
        {shown.map((f) => (
          <li key={f.file}>
            <button className={`file-item ${selected === f.file ? "active" : ""}`} onClick={() => onSelect(f.file)} title={f.file}>
              <FileCode size={14} style={{ color: languageColor(f.language) }} />
              <b>{fileName(f.file)}</b>
              <span className="muted">{dirName(f.file)}</span>
            </button>
          </li>
        ))}
        {shown.length === 0 && <li className="muted small pad">No files match.</li>}
      </ul>
    </div>
  );
}
