import { useMemo } from "react";
import { useNavigate } from "react-router-dom";
import {
  LANGUAGE_LOCATIONS,
  getLanguageByName,
} from "../../data/languageLocations";
import type { SimilarityMatrix } from "../../types";
import "./LanguageSimilarityPanel.css";

interface Props {
  selectedNodeCode: string;
  similarityData: SimilarityMatrix;
  onClose: () => void;
}

interface SimilarityItem {
  code: string;
  name: string;
  nameJa: string;
  country: string;
  similarity: number;
  distance: number;
}

export function LanguageSimilarityPanel({
  selectedNodeCode,
  similarityData,
  onClose,
}: Props) {
  const navigate = useNavigate();

  const selectedNode = LANGUAGE_LOCATIONS.find(
    (l) => l.code === selectedNodeCode,
  );

  const sortedSimilarities = useMemo(() => {
    if (!selectedNode) return [];

    // 選択されたノードのメイン言語名を取得
    const selectedLangName = selectedNode.isPrimary
      ? selectedNode.name
      : LANGUAGE_LOCATIONS.find((l) => l.code === selectedNode.primaryCode)
          ?.name;

    if (!selectedLangName || !similarityData[selectedLangName]) return [];

    const items: SimilarityItem[] = [];

    // すべてのノードに対して類似度を計算
    for (const node of LANGUAGE_LOCATIONS) {
      // 自分自身はスキップ
      if (node.code === selectedNodeCode) continue;

      // 同一言語のノードはスキップ（例：英語UK選択時に英語USはスキップ）
      if (node.name === selectedNode.name) continue;
      if (node.primaryCode === selectedNodeCode) continue;
      if (selectedNode.primaryCode && node.code === selectedNode.primaryCode)
        continue;
      if (
        selectedNode.primaryCode &&
        node.primaryCode === selectedNode.primaryCode
      )
        continue;

      const nodeLangName = node.isPrimary
        ? node.name
        : LANGUAGE_LOCATIONS.find((l) => l.code === node.primaryCode)?.name;

      if (!nodeLangName) continue;

      const distance = similarityData[selectedLangName]?.[nodeLangName];
      if (distance === undefined || distance === null) continue;

      const similarity = 1 - distance; // 類似度 = 距離

      items.push({
        code: node.code,
        name: node.name,
        nameJa: node.nameJa,
        country: node.country,
        similarity,
        distance,
      });
    }

    // 類似度の高い順（距離の小さい順）にソート
    return items.sort((a, b) => a.distance - b.distance);
  }, [selectedNode, selectedNodeCode, similarityData]);

  const handleItemClick = (item: SimilarityItem) => {
    const selectedNode = LANGUAGE_LOCATIONS.find(
      (l) => l.code === selectedNodeCode,
    );
    if (!selectedNode) return;

    const lang1 = getLanguageByName(
      selectedNode.isPrimary
        ? selectedNode.name
        : LANGUAGE_LOCATIONS.find((l) => l.code === selectedNode.primaryCode)
            ?.name || "",
    );
    const lang2 = getLanguageByName(item.name);

    if (lang1 && lang2) {
      navigate("/compare/" + lang1.code + "/" + lang2.code);
    }
  };

  const getDistanceColor = (distance: number): string => {
    if (distance < 0.05) return "#3b82f6"; // 青
    if (distance < 0.1) return "#22c55e"; // 緑
    if (distance < 0.3) return "#84cc16"; // 黄緑
    if (distance < 0.5) return "#facc15"; // 黄色
    if (distance < 0.7) return "#f97316"; // オレンジ
    return "#ef4444"; // 赤
  };

  return (
    <div className="similarity-panel">
      <div className="similarity-header">
        <div className="similarity-title-section">
          <h3 className="similarity-title">類似度ランキング</h3>
          <p className="similarity-subtitle">{selectedNode?.nameJa} との距離</p>
        </div>
        <button className="similarity-close" onClick={onClose}>
          ×
        </button>
      </div>

      <div className="similarity-list">
        {sortedSimilarities.map((item, index) => (
          <div
            key={item.code}
            className="similarity-item"
            onClick={() => handleItemClick(item)}
          >
            <div className="similarity-rank">#{index + 1}</div>
            <div className="similarity-info">
              <div className="similarity-lang-name">{item.nameJa}</div>
              <div className="similarity-country">{item.country}</div>
            </div>
            <div className="similarity-score">
              <div
                className="similarity-value"
                style={{ color: getDistanceColor(item.distance) }}
              >
                {item.distance.toFixed(4)}
              </div>
              <div className="similarity-bar-bg">
                <div
                  className="similarity-bar-fill"
                  style={{
                    width: `${Math.max(0, Math.min(100, (1 - item.distance) * 100))}%`,
                    backgroundColor: getDistanceColor(item.distance),
                  }}
                />
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="similarity-hint">💡 クリックして詳細比較</div>
    </div>
  );
}
