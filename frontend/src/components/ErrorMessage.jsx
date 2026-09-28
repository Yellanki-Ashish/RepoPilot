import { AlertTriangle, X } from "lucide-react";

export default function ErrorMessage({ message, onClose }) {
  if (!message) return null;
  return (
    <div className="error-box" role="alert">
      <AlertTriangle size={18} />
      <span>{message}</span>
      {onClose && <button className="icon-btn" onClick={onClose} aria-label="Dismiss"><X size={16} /></button>}
    </div>
  );
}
