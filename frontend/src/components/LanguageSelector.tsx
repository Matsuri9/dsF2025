import { LANGUAGE_NAMES } from "../constants";
import "./LanguageSelector.css";

interface Props {
  selectedLang1: string;
  selectedLang2: string;
  availableLanguages: string[];
  onLang1Change: (lang: string) => void;
  onLang2Change: (lang: string) => void;
}

export function LanguageSelector({
  selectedLang1,
  selectedLang2,
  availableLanguages,
  onLang1Change,
  onLang2Change,
}: Props) {
  return (
    <div className="language-selector">
      <div className="selector-group">
        <label htmlFor="lang1">言語 1:</label>
        <select
          id="lang1"
          className="language-select"
          value={selectedLang1}
          onChange={(e) => onLang1Change(e.target.value)}
        >
          <option value="">選択してください</option>
          {availableLanguages.map((code) => (
            <option key={code} value={code}>
              {LANGUAGE_NAMES[code] || code}
            </option>
          ))}
        </select>
      </div>
      <div className="selector-group">
        <label htmlFor="lang2">言語 2:</label>
        <select
          id="lang2"
          className="language-select"
          value={selectedLang2}
          onChange={(e) => onLang2Change(e.target.value)}
        >
          <option value="">選択してください</option>
          {availableLanguages.map((code) => (
            <option key={code} value={code}>
              {LANGUAGE_NAMES[code] || code}
            </option>
          ))}
        </select>
      </div>
    </div>
  );
}
