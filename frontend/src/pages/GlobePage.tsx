import { useState } from "react";
import { GlobeVisualization } from "../components/Globe/Globe";
import { LanguagePopup } from "../components/Globe/LanguagePopup";
import { LanguageSimilarityPanel } from "../components/Globe/LanguageSimilarityPanel";
import {
  useSimilarityData,
  useHeadDirectionRates,
} from "../hooks/useLanguageData";
import { LANGUAGE_LOCATIONS } from "../data/languageLocations";
import "./GlobePage.css";

interface DistanceFilter {
  veryClose: boolean;
  close: boolean;
  slightlyClose: boolean;
  slightlyFar: boolean;
  far: boolean;
  veryFar: boolean;
}

export function GlobePage() {
  const { similarityData } = useSimilarityData();
  const { rates: headDirectionRates } = useHeadDirectionRates();
  const [popupLanguage, setPopupLanguage] = useState<string | null>(null);
  const [selectedNodeCode, setSelectedNodeCode] = useState<string | null>(null);
  const [distanceFilter, setDistanceFilter] = useState<DistanceFilter>({
    veryClose: true,
    close: true,
    slightlyClose: true,
    slightlyFar: false,
    far: false,
    veryFar: false,
  });

  const handleLanguageClick = (_langName: string, nodeCode: string) => {
    // ノードを選択（同じノードをクリックしたら選択解除）
    if (selectedNodeCode === nodeCode) {
      setSelectedNodeCode(null);
    } else {
      setSelectedNodeCode(nodeCode);
    }
  };

  const handleShowPopup = () => {
    if (selectedNodeCode) {
      const node = LANGUAGE_LOCATIONS.find((l) => l.code === selectedNodeCode);
      if (node) {
        setPopupLanguage(node.name);
      }
    }
  };

  const handleClosePopup = () => {
    setPopupLanguage(null);
  };

  const handleClearSelection = () => {
    setSelectedNodeCode(null);
  };

  const handleFilterChange = (key: keyof DistanceFilter) => {
    setDistanceFilter((prev) => ({
      ...prev,
      [key]: !prev[key],
    }));
  };

  const selectedNode = selectedNodeCode
    ? LANGUAGE_LOCATIONS.find((l) => l.code === selectedNodeCode)
    : null;

  return (
    <div className="globe-page">
      <div className="globe-fullscreen">
        <GlobeVisualization
          similarityData={similarityData.headDirectionMerged}
          onLanguageClick={handleLanguageClick}
          distanceFilter={distanceFilter}
          selectedNodeCode={selectedNodeCode}
        />
      </div>

      {/* ヘッダー */}
      <div className="overlay-header">
        <h1 className="site-title">
          <span className="title-icon">🌐</span>
          Grammatical Cosmos
        </h1>
        <p className="site-subtitle">言語の文法構造を宇宙から眺める</p>
      </div>

      {/* 選択中のノード表示（右上） */}
      {selectedNode && (
        <div className="selected-node-panel">
          <div className="selected-node-header">
            <span className="selected-label">選択中</span>
            <button className="clear-btn" onClick={handleClearSelection}>
              ×
            </button>
          </div>
          <div className="selected-node-info">
            <span className="selected-name">{selectedNode.nameJa}</span>
            <span className="selected-country">{selectedNode.country}</span>
          </div>
          <button className="details-btn" onClick={handleShowPopup}>
            詳細を見る →
          </button>
        </div>
      )}

      {/* 凡例（選択中のノードがない場合のみ表示） */}
      {!selectedNodeCode && (
        <div className="overlay-legend">
          <div className="legend-content">
            <h4 className="legend-title">表示する距離</h4>
            <div className="legend-filters">
              <label className="filter-item">
                <input
                  type="checkbox"
                  checked={distanceFilter.veryClose}
                  onChange={() => handleFilterChange("veryClose")}
                />
                <span
                  className="color-sample"
                  style={{ background: "#3b82f6" }}
                ></span>
                <span>非常に近い (&lt;0.05)</span>
              </label>
              <label className="filter-item">
                <input
                  type="checkbox"
                  checked={distanceFilter.close}
                  onChange={() => handleFilterChange("close")}
                />
                <span
                  className="color-sample"
                  style={{ background: "#22c55e" }}
                ></span>
                <span>近い (&lt;0.1)</span>
              </label>
              <label className="filter-item">
                <input
                  type="checkbox"
                  checked={distanceFilter.slightlyClose}
                  onChange={() => handleFilterChange("slightlyClose")}
                />
                <span
                  className="color-sample"
                  style={{ background: "#84cc16" }}
                ></span>
                <span>やや近い (&lt;0.3)</span>
              </label>
              <label className="filter-item">
                <input
                  type="checkbox"
                  checked={distanceFilter.slightlyFar}
                  onChange={() => handleFilterChange("slightlyFar")}
                />
                <span
                  className="color-sample"
                  style={{ background: "#facc15" }}
                ></span>
                <span>やや遠い (&lt;0.5)</span>
              </label>
              <label className="filter-item">
                <input
                  type="checkbox"
                  checked={distanceFilter.far}
                  onChange={() => handleFilterChange("far")}
                />
                <span
                  className="color-sample"
                  style={{ background: "#f97316" }}
                ></span>
                <span>遠い (&lt;0.7)</span>
              </label>
              <label className="filter-item">
                <input
                  type="checkbox"
                  checked={distanceFilter.veryFar}
                  onChange={() => handleFilterChange("veryFar")}
                />
                <span
                  className="color-sample"
                  style={{ background: "#ef4444" }}
                ></span>
                <span>非常に遠い (≥0.7)</span>
              </label>
            </div>
            <p className="legend-hint">※ ノードをクリックで詳細表示</p>
          </div>
        </div>
      )}

      <div className="overlay-instructions">
        <div className="instruction-item">◉ 国クリック → 選択</div>
        <div className="instruction-item">━ 線クリック → 比較ページ</div>
      </div>

      <div className="overlay-footer">
        Grammatical Cosmos | Universal Dependencies v2.16
      </div>

      {popupLanguage && (
        <LanguagePopup
          languageName={popupLanguage}
          headDirectionRates={headDirectionRates}
          onClose={handleClosePopup}
        />
      )}

      {/* 言語類似度パネル（ノード選択時） */}
      {selectedNodeCode && !popupLanguage && (
        <LanguageSimilarityPanel
          selectedNodeCode={selectedNodeCode}
          similarityData={similarityData.headDirectionMerged}
          onClose={handleClearSelection}
        />
      )}
    </div>
  );
}
