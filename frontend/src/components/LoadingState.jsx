import { CheckCircle2, Circle, Loader2 } from "lucide-react";
import { ANALYSIS_STEPS } from "../utils/formatters";

/** Shows the real backend stage while a repository is being analysed. */
export default function LoadingState({ step = 0, title = "Analyzing repository" }) {
  return (
    <div className="card loading-card">
      <div className="loading-title"><Loader2 className="spin" size={20} /> {title}</div>
      <ul className="steps">
        {ANALYSIS_STEPS.map((label, i) => (
          <li key={label} className={i < step ? "done" : i === step ? "current" : ""}>
            {i < step ? <CheckCircle2 size={16} /> : i === step ? <Loader2 className="spin" size={16} /> : <Circle size={16} />}
            {label}
          </li>
        ))}
      </ul>
      <p className="muted small">The first analysis downloads the embedding model and can take a few minutes.</p>
    </div>
  );
}

export function InlineLoading({ text = "Loading..." }) {
  return <div className="inline-loading"><Loader2 className="spin" size={16} /> {text}</div>;
}
