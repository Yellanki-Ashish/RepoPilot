import { useEffect, useRef, useState } from "react";
import { Bot, Send, User } from "lucide-react";
import { askAssistant, describeError } from "../api/api";
import { SUGGESTED_QUESTIONS } from "../utils/formatters";
import SourceReference from "./SourceReference";
import { InlineLoading } from "./LoadingState";

export default function ChatPanel({ repositoryId, onSelectSource, activeSource }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const endRef = useRef(null);

  useEffect(() => { setMessages([]); }, [repositoryId]);
  useEffect(() => { endRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages, busy]);

  const send = async (text) => {
    const question = (text ?? input).trim();
    if (question.length < 3 || busy) return;
    setInput("");
    setMessages((m) => [...m, { role: "user", text: question }]);
    setBusy(true);
    try {
      const res = await askAssistant(repositoryId, question);
      setMessages((m) => [...m, { role: "assistant", text: res.answer, sources: res.sources, agents: res.agents_used, intent: res.intent }]);
    } catch (err) {
      setMessages((m) => [...m, { role: "assistant", error: true, text: describeError(err, "The assistant could not answer. Check backend logs.") }]);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="card chat">
      <div className="chat-scroll">
        {messages.length === 0 && (
          <div className="chat-empty">
            <Bot size={32} />
            <p>Ask anything about this repository. Answers cite the files and lines they came from.</p>
            <div className="suggestions">
              {SUGGESTED_QUESTIONS.map((q) => <button key={q} className="chip" onClick={() => send(q)}>{q}</button>)}
            </div>
          </div>
        )}
        {messages.map((m, i) => (
          <div key={i} className={`msg ${m.role} ${m.error ? "err" : ""}`}>
            <div className="msg-icon">{m.role === "user" ? <User size={16} /> : <Bot size={16} />}</div>
            <div className="msg-body">
              <div className="msg-text">{m.text}</div>
              {m.agents?.length > 0 && (
                <div className="agents small muted">Agents: {m.agents.join(" → ")}{m.intent ? ` · intent: ${m.intent}` : ""}</div>
              )}
              {m.sources?.length > 0 && (
                <div className="sources">
                  <span className="small muted">Sources</span>
                  {m.sources.map((s, k) => (
                    <SourceReference key={k} source={s} onSelect={onSelectSource}
                      active={activeSource?.file === s.file && activeSource?.start_line === s.start_line} />
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}
        {busy && <div className="msg assistant"><div className="msg-icon"><Bot size={16} /></div><InlineLoading text="Agents are working on your question..." /></div>}
        <div ref={endRef} />
      </div>
      <form className="chat-input" onSubmit={(e) => { e.preventDefault(); send(); }}>
        <input value={input} onChange={(e) => setInput(e.target.value)} placeholder="Ask about this repository..." disabled={busy} />
        <button className="btn primary" type="submit" disabled={busy || input.trim().length < 3}><Send size={16} /> Ask</button>
      </form>
    </div>
  );
}
