import { useRef, useEffect, useMemo, useState } from "react";
import type {
  Sentence,
  PhraseSentence,
  LanguageData,
  PhraseData,
} from "../types";
import { UPOS_JA_MAP, DEPREL_JA_MAP, DEPREL_COLORS } from "../constants";
import { ZoomControls } from "./ZoomControls";
import "./ComparisonArea.css";

interface Props {
  lang1Data: LanguageData | null;
  lang2Data: LanguageData | null;
  lang1Code: string;
  lang2Code: string;
  phraseData1: PhraseData | null;
  phraseData2: PhraseData | null;
  sentenceIndex: number | null;
  showJapaneseTags: boolean;
  showDependencyGraph: boolean;
  zoom: number;
  onZoomChange: (delta: number) => void;
  onZoomReset: () => void;
}

function escapeHtml(text: string): string {
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}

// ツールチップの情報
interface TooltipInfo {
  x: number;
  y: number;
  fromWord: string;
  toWord: string;
  deprel: string;
  deprelJa: string;
  fromUpos: string;
  toUpos: string;
}

// Draw arrow helper function (module level to avoid hoisting issues)
function drawArrow(
  svg: SVGSVGElement,
  fromToken: HTMLElement,
  toToken: HTMLElement,
  container: HTMLElement,
  langCode: string,
  tokenById: Map<string, { form: string; upos: string }>,
  onTooltipShow: (info: TooltipInfo) => void,
  onTooltipHide: () => void,
) {
  const containerRect = container.getBoundingClientRect();
  const fromRect = fromToken.getBoundingClientRect();
  const toRect = toToken.getBoundingClientRect();

  const fromX =
    fromRect.left -
    containerRect.left +
    container.scrollLeft +
    fromRect.width / 2;
  const fromY = fromRect.top - containerRect.top + container.scrollTop;
  const toX =
    toRect.left - containerRect.left + container.scrollLeft + toRect.width / 2;
  const toY = toRect.top - containerRect.top + container.scrollTop;

  const distance = Math.abs(toX - fromX);
  const height = Math.min(60, 20 + distance * 0.08);

  const deprel = fromToken.dataset.deprel || "";
  const deprelBase = deprel.split(":")[0];
  const color = DEPREL_COLORS[deprelBase] || DEPREL_COLORS["default"];

  // パスを作成
  const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
  const topY = Math.min(fromY, toY) - height;
  const r = 5;

  let d = "";
  if (Math.abs(fromX - toX) < 2 * r) {
    d = `M ${fromX} ${fromY} L ${fromX} ${topY} L ${toX} ${topY} L ${toX} ${toY}`;
  } else {
    const dir = toX > fromX ? 1 : -1;
    d = `M ${fromX} ${fromY} L ${fromX} ${topY + r} Q ${fromX} ${topY} ${fromX + r * dir} ${topY} L ${toX - r * dir} ${topY} Q ${toX} ${topY} ${toX} ${topY + r} L ${toX} ${toY}`;
  }

  path.setAttribute("d", d);
  path.setAttribute("fill", "none");
  path.setAttribute("stroke", color);
  path.setAttribute("stroke-width", "1.5");
  path.setAttribute("marker-end", `url(#arrowhead-${langCode}-${deprelBase})`);
  path.setAttribute("data-from-id", fromToken.dataset.id || "");
  path.setAttribute("data-to-id", toToken.dataset.id || "");
  path.classList.add("dependency-arrow");

  // ホバー用の透明な太い線を追加（クリック/ホバー領域を広げる）
  const hitArea = document.createElementNS(
    "http://www.w3.org/2000/svg",
    "path",
  );
  hitArea.setAttribute("d", d);
  hitArea.setAttribute("fill", "none");
  hitArea.setAttribute("stroke", "transparent");
  hitArea.setAttribute("stroke-width", "12");
  hitArea.classList.add("dependency-hit-area");

  // ホバーイベント
  const fromTokenData = tokenById.get(fromToken.dataset.id || "");
  const toTokenData = tokenById.get(toToken.dataset.id || "");

  const handleMouseEnter = (e: MouseEvent) => {
    path.classList.add("arrow-highlight");
    if (fromTokenData && toTokenData) {
      onTooltipShow({
        x: e.clientX,
        y: e.clientY,
        fromWord: fromTokenData.form,
        toWord: toTokenData.form,
        deprel: deprel,
        deprelJa: DEPREL_JA_MAP[deprelBase] || deprel,
        fromUpos: fromTokenData.upos,
        toUpos: toTokenData.upos,
      });
    }
  };

  const handleMouseLeave = () => {
    path.classList.remove("arrow-highlight");
    onTooltipHide();
  };

  hitArea.addEventListener("mouseenter", handleMouseEnter);
  hitArea.addEventListener("mouseleave", handleMouseLeave);
  hitArea.addEventListener("mousemove", (e: MouseEvent) => {
    if (fromTokenData && toTokenData) {
      onTooltipShow({
        x: e.clientX,
        y: e.clientY,
        fromWord: fromTokenData.form,
        toWord: toTokenData.form,
        deprel: deprel,
        deprelJa: DEPREL_JA_MAP[deprelBase] || deprel,
        fromUpos: fromTokenData.upos,
        toUpos: toTokenData.upos,
      });
    }
  });

  svg.appendChild(path);
  svg.appendChild(hitArea);
}

interface LanguageBlockProps {
  sentence: Sentence;
  phraseSentence: PhraseSentence | null;
  languageName: string;
  langCode: string;
  showJapaneseTags: boolean;
  showDependencyGraph: boolean;
  zoom: number;
  onTooltipShow: (info: TooltipInfo) => void;
  onTooltipHide: () => void;
}

function LanguageBlock({
  sentence,
  phraseSentence,
  languageName,
  langCode,
  showJapaneseTags,
  showDependencyGraph,
  zoom,
  onTooltipShow,
  onTooltipHide,
}: LanguageBlockProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const tokens = useMemo(() => sentence.tokens || [], [sentence.tokens]);

  // Build token to phrase mapping
  const tokenToPhraseMap = useMemo(() => {
    const map = new Map<string, string>();
    if (phraseSentence?.phrases) {
      phraseSentence.phrases.forEach((phrase) => {
        phrase.tokens.forEach((t) => {
          map.set(t.id, phrase.head_id);
        });
      });
    }
    return map;
  }, [phraseSentence]);

  const phraseInfoMap = useMemo(() => {
    const map = new Map<string, { head_upos: string }>();
    if (phraseSentence?.phrases) {
      phraseSentence.phrases.forEach((phrase) => {
        map.set(phrase.head_id, { head_upos: phrase.head_upos });
      });
    }
    return map;
  }, [phraseSentence]);

  // トークンIDからトークン情報を取得するマップ
  const tokenById = useMemo(() => {
    const map = new Map<string, (typeof tokens)[0]>();
    tokens.forEach((t) => map.set(t.id, t));
    return map;
  }, [tokens]);

  // Draw dependency arrows
  useEffect(() => {
    if (!showDependencyGraph || !containerRef.current) return;

    const container = containerRef.current;

    // Remove existing SVG
    const existingSvg = container.querySelector(".dependency-layer");
    if (existingSvg) existingSvg.remove();

    // Create SVG
    const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    svg.classList.add("dependency-layer");
    svg.setAttribute("width", String(container.scrollWidth));
    svg.setAttribute("height", String(container.scrollHeight));

    // Create defs for markers
    const defs = document.createElementNS("http://www.w3.org/2000/svg", "defs");
    Object.entries(DEPREL_COLORS).forEach(([key, color]) => {
      const marker = document.createElementNS(
        "http://www.w3.org/2000/svg",
        "marker",
      );
      marker.setAttribute("id", `arrowhead-${langCode}-${key}`);
      marker.setAttribute("markerWidth", "10");
      marker.setAttribute("markerHeight", "7");
      marker.setAttribute("refX", "9");
      marker.setAttribute("refY", "3.5");
      marker.setAttribute("orient", "auto");

      const polygon = document.createElementNS(
        "http://www.w3.org/2000/svg",
        "polygon",
      );
      polygon.setAttribute("points", "0 0, 10 3.5, 0 7");
      polygon.setAttribute("fill", color);

      marker.appendChild(polygon);
      defs.appendChild(marker);
    });
    svg.appendChild(defs);

    container.appendChild(svg);

    const tokenElements = container.querySelectorAll(".token");
    const tokenMap = new Map<string, HTMLElement>();
    tokenElements.forEach((t) => {
      const el = t as HTMLElement;
      tokenMap.set(el.dataset.id || "", el);
    });

    tokenElements.forEach((tokenEl) => {
      const el = tokenEl as HTMLElement;
      const headId = el.dataset.headId;
      if (headId === "0" || !tokenMap.has(headId || "")) return;

      const headToken = tokenMap.get(headId || "");
      if (!headToken) return;

      drawArrow(
        svg,
        el,
        headToken,
        container,
        langCode,
        tokenById,
        onTooltipShow,
        onTooltipHide,
      );
    });
  }, [
    showDependencyGraph,
    tokens,
    zoom,
    langCode,
    tokenById,
    onTooltipShow,
    onTooltipHide,
  ]);

  return (
    <div className="language-block">
      <div className="language-header">
        {languageName}
        <span className="sent-id">{sentence.sent_id}</span>
      </div>
      <div className="sentence-text">{escapeHtml(sentence.text)}</div>
      <div className="tokens-display" ref={containerRef} data-lang={langCode}>
        {tokens.map((token, index) => {
          const phraseId = tokenToPhraseMap.get(token.id);
          const phrase = phraseInfoMap.get(phraseId || "");

          let phraseClass = "";
          let showPhraseLabel = false;

          if (phraseId) {
            const prevTokenId = tokens[index - 1]?.id;
            const nextTokenId = tokens[index + 1]?.id;
            const prevPhraseId = tokenToPhraseMap.get(prevTokenId || "");
            const nextPhraseId = tokenToPhraseMap.get(nextTokenId || "");

            const isStart = phraseId !== prevPhraseId;
            const isEnd = phraseId !== nextPhraseId;

            if (isStart && isEnd) {
              phraseClass = "phrase-single";
            } else if (isStart) {
              phraseClass = "phrase-start";
            } else if (isEnd) {
              phraseClass = "phrase-end";
            } else {
              phraseClass = "phrase-middle";
            }

            showPhraseLabel = isStart;
          }

          const uposLabel = showJapaneseTags
            ? UPOS_JA_MAP[token.upos] || token.upos
            : token.upos || "-";

          const deprelBase = (token.deprel || "").split(":")[0];
          const deprelLabel = showJapaneseTags
            ? DEPREL_JA_MAP[deprelBase] || token.deprel
            : token.deprel || "-";

          const tokenStyle = {
            fontSize: `${14 * zoom}px`,
            padding: `${8 * zoom}px ${12 * zoom}px`,
            minWidth: `${60 * zoom}px`,
            maxWidth: `${150 * zoom}px`,
          };

          const phraseMarkerStyle = {
            fontSize: `${12 * zoom}px`,
            height: `${24 * zoom}px`,
          };

          return (
            <div className="token-wrapper" key={token.id}>
              <div
                className="token"
                style={tokenStyle}
                data-token-id={index}
                data-id={token.id}
                data-head-id={token.head}
                data-lang={langCode}
                data-upos={token.upos}
                data-deprel={token.deprel}
                data-form={token.form}
              >
                <div className="token-form">{escapeHtml(token.form)}</div>
                <div className="token-tag upos-tag">{uposLabel}</div>
                <div className="token-tag deprel-tag">{deprelLabel}</div>
              </div>
              <div
                className={`phrase-marker ${phraseClass}`}
                style={phraseMarkerStyle}
                data-phrase-id={phraseId || ""}
              >
                {showPhraseLabel && phrase && (
                  <div className="phrase-label">
                    {showJapaneseTags
                      ? UPOS_JA_MAP[phrase.head_upos] || phrase.head_upos
                      : phrase.head_upos}
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

export function ComparisonArea({
  lang1Data,
  lang2Data,
  lang1Code,
  lang2Code,
  phraseData1,
  phraseData2,
  sentenceIndex,
  showJapaneseTags,
  showDependencyGraph,
  zoom,
  onZoomChange,
  onZoomReset,
}: Props) {
  const [tooltip, setTooltip] = useState<TooltipInfo | null>(null);

  const handleTooltipShow = (info: TooltipInfo) => {
    setTooltip(info);
  };

  const handleTooltipHide = () => {
    setTooltip(null);
  };

  if (!lang1Data || !lang2Data || sentenceIndex === null) {
    return (
      <div className="comparison-area">
        <div className="notice">上記から2つの言語を選択してください</div>
      </div>
    );
  }

  const sent1 = lang1Data.sentences[sentenceIndex];
  const sent2 = lang2Data.sentences[sentenceIndex];
  const phrases1 = phraseData1?.sentences[sentenceIndex] || null;
  const phrases2 = phraseData2?.sentences[sentenceIndex] || null;

  if (!sent1 || !sent2) {
    return (
      <div className="comparison-area">
        <div className="notice" style={{ color: "#ef4444" }}>
          ⚠️ 文が見つかりません
        </div>
      </div>
    );
  }

  return (
    <div className="comparison-area">
      <ZoomControls
        zoom={zoom}
        onZoomChange={onZoomChange}
        onZoomReset={onZoomReset}
      />
      <div className="sentence-comparison">
        <LanguageBlock
          sentence={sent1}
          phraseSentence={phrases1}
          languageName={lang1Data.language}
          langCode={lang1Code}
          showJapaneseTags={showJapaneseTags}
          showDependencyGraph={showDependencyGraph}
          zoom={zoom}
          onTooltipShow={handleTooltipShow}
          onTooltipHide={handleTooltipHide}
        />
        <LanguageBlock
          sentence={sent2}
          phraseSentence={phrases2}
          languageName={lang2Data.language}
          langCode={lang2Code}
          showJapaneseTags={showJapaneseTags}
          showDependencyGraph={showDependencyGraph}
          zoom={zoom}
          onTooltipShow={handleTooltipShow}
          onTooltipHide={handleTooltipHide}
        />
      </div>

      {/* 係り受けツールチップ */}
      {tooltip && (
        <div
          className="dependency-tooltip"
          style={{
            left: tooltip.x + 15,
            top: tooltip.y + 15,
          }}
        >
          <div className="tooltip-header">
            <span className="tooltip-from">{tooltip.toWord}</span>
            <span className="tooltip-arrow">←</span>
            <span className="tooltip-to">{tooltip.fromWord}</span>
          </div>
          <div className="tooltip-relation">
            <span className="relation-label">関係:</span>
            <span className="relation-value">{tooltip.deprel}</span>
            <span className="relation-ja">({tooltip.deprelJa})</span>
          </div>
          <div className="tooltip-upos">
            <span>Head: {tooltip.toUpos}</span>
            <span>Dep: {tooltip.fromUpos}</span>
          </div>
        </div>
      )}
    </div>
  );
}
