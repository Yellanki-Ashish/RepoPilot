import { FileText } from "lucide-react";
import { formatLines } from "../utils/formatters";

export default function SourceReference({ source, onSelect, active }) {
  return (
    <button className={`source-ref ${active ? "active" : ""}`} onClick={() => onSelect?.(source)}
      title={source.section || ""}>
      <FileText size={14} />
      <span className="mono">{source.file}</span>
      <em>{formatLines(source)}</em>
      {source.relevance != null && <small>{Math.round(source.relevance * 100)}%</small>}
    </button>
  );
}
