import { InfoTooltip } from "./InfoTooltip";
import "./SimilarityDisplay.css";

interface Props {
  uposSimilarity: number | null;
  deprelSimilarity: number | null;
  phraseSimilarity: number | null;
  headDirectionRawSimilarity: number | null;
  headDirectionMergedSimilarity: number | null;
}

function formatScore(
  value: number | null,
  isDistance: boolean = false,
): string {
  if (value !== null && value !== undefined && !isNaN(value)) {
    if (isDistance) {
      // 距離の場合: 小さい方が類似
      return value.toFixed(4);
    }
    return value.toFixed(4);
  }
  return "—";
}

export function SimilarityDisplay({
  uposSimilarity,
  deprelSimilarity,
  phraseSimilarity,
  headDirectionRawSimilarity,
  headDirectionMergedSimilarity,
}: Props) {
  return (
    <div className="similarity-display">
      <h3 className="similarity-title">言語間類似度</h3>
      <div className="similarity-grid">
        <div className="similarity-group">
          <span className="group-label">
            <InfoTooltip
              term="n-gram類似度"
              description="連続する単語・品詞の並びパターンの類似度。値が大きいほど類似。"
            />
          </span>
          <div className="metric">
            <span className="label">
              <InfoTooltip
                term="UPOS"
                description="Universal Part-of-Speech: 言語横断的な品詞タグ体系（名詞、動詞など17種類）"
              />
            </span>
            <span className="value">{formatScore(uposSimilarity)}</span>
          </div>
          <div className="metric">
            <span className="label">
              <InfoTooltip
                term="DEPREL"
                description="Dependency Relation: 係り受け関係のタイプ（主語、目的語など37種類）"
              />
            </span>
            <span className="value">{formatScore(deprelSimilarity)}</span>
          </div>
          <div className="metric">
            <span className="label">Phrase</span>
            <span className="value">{formatScore(phraseSimilarity)}</span>
          </div>
        </div>
        <div className="similarity-group">
          <span className="group-label">
            <InfoTooltip
              term="Head Direction距離"
              description="主要部（Head）が前に来るか後ろに来るかの傾向の違い。値が小さいほど類似。"
            />
          </span>
          <div className="metric">
            <span className="label">Raw</span>
            <span className="value distance">
              {formatScore(headDirectionRawSimilarity, true)}
            </span>
          </div>
          <div className="metric">
            <span className="label">Merged</span>
            <span className="value distance">
              {formatScore(headDirectionMergedSimilarity, true)}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
