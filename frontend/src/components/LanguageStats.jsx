import { formatNumber, languageColor } from "../utils/formatters";

export default function LanguageStats({ languages }) {
  const entries = Object.entries(languages || {}).slice(0, 8);
  const total = entries.reduce((sum, [, n]) => sum + n, 0) || 1;
  return (
    <div className="card">
      <h3>Language Distribution</h3>
      <div className="lang-bar">
        {entries.map(([lang, n]) => (
          <span key={lang} title={`${lang}: ${n}`} style={{ width: `${(n / total) * 100}%`, background: languageColor(lang) }} />
        ))}
      </div>
      <ul className="lang-list">
        {entries.map(([lang, n]) => (
          <li key={lang}>
            <i style={{ background: languageColor(lang) }} /> {lang}
            <span>{formatNumber(n)} files · {((n / total) * 100).toFixed(0)}%</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
