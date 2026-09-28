import { useEffect, useRef, useState } from "react";
import { X } from "lucide-react";
import { describeError, getFile } from "../api/api";
import ErrorMessage from "./ErrorMessage";
import { InlineLoading } from "./LoadingState";

const MAX_RENDERED_LINES = 1500;

/** Shows a file with line numbers, highlights an optional range, and lists its symbols. */
export default function CodeViewer({ repositoryId, file, highlight, onClose }) {
  const [data, setData] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const markRef = useRef(null);

  useEffect(() => {
    if (!file) return;
    let cancelled = false;
    setLoading(true);
    setError("");
    getFile(repositoryId, file)
      .then((d) => !cancelled && setData(d))
      .catch((e) => !cancelled && (setData(null), setError(describeError(e, "Could not load this file."))))
      .finally(() => !cancelled && setLoading(false));
    return () => { cancelled = true; };
  }, [repositoryId, file]);

  useEffect(() => {
    markRef.current?.scrollIntoView({ block: "center" });
  }, [data, highlight]);

  if (!file) return <div className="card muted center-msg">Select a file or a source reference to view its code.</div>;

  const lines = data ? data.content.split("\n") : [];
  const focus = highlight?.start_line || 1;
  const from = lines.length > MAX_RENDERED_LINES ? Math.max(1, focus - 100) : 1;
  const to = Math.min(lines.length, from + MAX_RENDERED_LINES - 1);
  const a = data?.analysis;
  const cx = data?.complexity;

  return (
    <div className="card viewer">
      <div className="viewer-head">
        <div>
          <h3 className="mono">{file}</h3>
          {data && <span className="muted small">{data.language} · {a.lines} lines{cx ? ` · complexity ${cx.complexity}` : ""}</span>}
        </div>
        {onClose && <button className="icon-btn" onClick={onClose} aria-label="Close"><X size={16} /></button>}
      </div>
      <ErrorMessage message={error} />
      {loading && <InlineLoading text="Loading file..." />}
      {data && (
        <>
          <div className="symbols">
            <SymbolList title="Classes" items={a.classes.map((c) => c.name)} />
            <SymbolList title="Functions" items={a.functions.map((f) => f.name)} />
            <SymbolList title="Methods" items={a.methods.map((m) => `${m.class}.${m.name}`)} />
            <SymbolList title="Imports" items={a.imports} />
            {a.errors.length > 0 && <p className="small warn">Parsing issue: {a.errors[0]}</p>}
          </div>
          {lines.length > MAX_RENDERED_LINES && (
            <p className="muted small">Large file: showing lines {from}-{to} of {lines.length}.</p>
          )}
          <pre className="code">
            {lines.slice(from - 1, to).map((text, i) => {
              const n = from + i;
              const hit = highlight && n >= highlight.start_line && n <= highlight.end_line;
              return (
                <div key={n} className={`code-line ${hit ? "hit" : ""}`} ref={n === focus ? markRef : null}>
                  <span className="ln">{n}</span><code>{text || " "}</code>
                </div>
              );
            })}
          </pre>
        </>
      )}
    </div>
  );
}

function SymbolList({ title, items }) {
  if (!items.length) return null;
  return (
    <details>
      <summary>{title} ({items.length})</summary>
      <div className="chips">{items.slice(0, 60).map((i, k) => <span className="chip mono" key={k}>{i}</span>)}</div>
    </details>
  );
}
