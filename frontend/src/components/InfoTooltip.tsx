import { useState } from "react";
import "./InfoTooltip.css";

interface Props {
  term: string;
  description: string;
}

export function InfoTooltip({ term, description }: Props) {
  const [isVisible, setIsVisible] = useState(false);

  return (
    <span className="info-tooltip-wrapper">
      <span className="term">{term}</span>
      <span
        className="info-icon"
        onMouseEnter={() => setIsVisible(true)}
        onMouseLeave={() => setIsVisible(false)}
      >
        ⓘ
      </span>
      {isVisible && <span className="info-tooltip-popup">{description}</span>}
    </span>
  );
}
