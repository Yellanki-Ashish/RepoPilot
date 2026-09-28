import { useEffect, useMemo, useRef, useState } from "react";
import ForceGraph2D from "react-force-graph-2d";
import { fileName, languageColor } from "../utils/formatters";

const MAX_NODES = 250;

/** Interactive dependency view: force graph (capped) plus a ranked list with imports / imported-by. */
export default function DependencyGraph({ dependency, onSelectFile }) {
  const stats = dependency.statistics;
  const graph = dependency.graph;
  const [tab, setTab] = useState("list");
  const [focus, setFocus] = useState(null);
  const boxRef = useRef(null);
  const [width, setWidth] = useState(600);

  useEffect(() => {
    if (!boxRef.current) return;
    const update = () => setWidth(boxRef.current?.clientWidth || 600);
    update();
    window.addEventListener("resize", update);
    return () => window.removeEventListener("resize", update);
  }, [tab]);

  const data = useMemo(() => {
    const connected = graph.nodes.filter((n) => n.in_degree + n.out_degree > 0)
      .sort((a, b) => b.in_degree + b.out_degree - (a.in_degree + a.out_degree)).slice(0, MAX_NODES);
    const ids = new Set(connected.map((n) => n.id));
    return {
      nodes: connected.map((n) => ({ ...n })),
      links: graph.edges.filter((e) => ids.has(e.source) && ids.has(e.target)).map((e) => ({ ...e })),
    };
  }, [graph]);

  const details = useMemo(() => {
    if (!focus) return null;
    return {
      imports: graph.edges.filter((e) => e.source === focus).map((e) => e.target),
      importedBy: graph.edges.filter((e) => e.target === focus).map((e) => e.source),
    };
  }, [focus, graph]);

  const choose = (file) => {
    setFocus(file);
    onSelectFile?.(file);
  };

  return (
    <div className="card">
      <div className="tab-row">
        <h3>Dependency Graph</h3>
        <div className="tabs">
          <button className={tab === "list" ? "active" : ""} onClick={() => setTab("list")}>List</button>
          <button className={tab === "graph" ? "active" : ""} onClick={() => setTab("graph")}>Graph</button>
        </div>
      </div>
      <div className="mini-stats">
        <div><strong>{stats.nodes}</strong><span>files</span></div>
        <div><strong>{stats.edges}</strong><span>import links</span></div>
        <div><strong>{stats.density}</strong><span>density</span></div>
        <div><strong>{stats.isolated_files?.length ?? 0}</strong><span>isolated</span></div>
      </div>

      {tab === "graph" ? (
        <div ref={boxRef} className="graph-box">
          {data.nodes.length === 0 ? (
            <p className="muted center-msg">No resolvable internal imports were found.</p>
          ) : (
            <ForceGraph2D
              graphData={data}
              width={width}
              height={380}
              nodeLabel={(n) => n.id}
              nodeVal={(n) => 1 + n.in_degree}
              nodeColor={(n) => (n.id === focus ? "#f43f5e" : languageColor(n.language))}
              linkDirectionalArrowLength={3}
              linkColor={() => "rgba(148,163,184,0.4)"}
              onNodeClick={(n) => choose(n.id)}
            />
          )}
          {graph.nodes.length > MAX_NODES && (
            <p className="muted small">Showing the {MAX_NODES} most connected files.</p>
          )}
        </div>
      ) : (
        <div className="dep-columns">
          <div>
            <h4>Most connected files</h4>
            <ul className="rank-list">
              {stats.most_connected_files.slice(0, 8).map((f) => (
                <li key={f.file}>
                  <button className="link-btn" onClick={() => choose(f.file)} title={f.file}>
                    <b>{fileName(f.file)}</b>
                  </button>
                  <span className="rank-value">{f.connections}</span>
                </li>
              ))}
              {stats.most_connected_files.length === 0 && <li className="muted small">No internal dependencies detected.</li>}
            </ul>
            <h4>Most imported files</h4>
            <ul className="rank-list">
              {stats.most_imported_files.slice(0, 8).map((f) => (
                <li key={f.file}>
                  <button className="link-btn" onClick={() => choose(f.file)} title={f.file}>
                    <b>{fileName(f.file)}</b>
                  </button>
                  <span className="rank-value">{f.in_degree}</span>
                </li>
              ))}
            </ul>
          </div>
          <div>
            <h4>{focus ? fileName(focus) : "Select a file"}</h4>
            {details ? (
              <>
                <p className="small"><b>Imports ({details.imports.length})</b></p>
                <ul className="plain-list mono small">{details.imports.map((f) => <li key={f}>{f}</li>)}</ul>
                <p className="small"><b>Imported by ({details.importedBy.length})</b></p>
                <ul className="plain-list mono small">{details.importedBy.map((f) => <li key={f}>{f}</li>)}</ul>
              </>
            ) : <p className="muted small">Click a file to see what it imports and who imports it.</p>}
          </div>
        </div>
      )}
    </div>
  );
}
