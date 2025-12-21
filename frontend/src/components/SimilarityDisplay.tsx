import './SimilarityDisplay.css';

interface Props {
    uposSimilarity: number | null;
    deprelSimilarity: number | null;
    phraseSimilarity: number | null;
    headDirectionRawSimilarity: number | null;
    headDirectionMergedSimilarity: number | null;
}

function formatScore(value: number | null, isDistance: boolean = false): string {
    if (value !== null && value !== undefined && !isNaN(value)) {
        if (isDistance) {
            // 距離の場合: 小さい方が類似
            return value.toFixed(4);
        }
        return value.toFixed(4);
    }
    return '—';
}

export function SimilarityDisplay({
    uposSimilarity,
    deprelSimilarity,
    phraseSimilarity,
    headDirectionRawSimilarity,
    headDirectionMergedSimilarity
}: Props) {
    return (
        <div className="similarity-display">
            <h3 className="similarity-title">言語間類似度</h3>
            <div className="similarity-grid">
                <div className="similarity-group">
                    <span className="group-label">n-gram類似度</span>
                    <div className="metric">
                        <span className="label">UPOS</span>
                        <span className="value">{formatScore(uposSimilarity)}</span>
                    </div>
                    <div className="metric">
                        <span className="label">DEPREL</span>
                        <span className="value">{formatScore(deprelSimilarity)}</span>
                    </div>
                    <div className="metric">
                        <span className="label">Phrase</span>
                        <span className="value">{formatScore(phraseSimilarity)}</span>
                    </div>
                </div>
                <div className="similarity-group">
                    <span className="group-label">Head Direction距離</span>
                    <div className="metric">
                        <span className="label">Raw</span>
                        <span className="value distance">{formatScore(headDirectionRawSimilarity, true)}</span>
                    </div>
                    <div className="metric">
                        <span className="label">Merged</span>
                        <span className="value distance">{formatScore(headDirectionMergedSimilarity, true)}</span>
                    </div>
                </div>
            </div>
        </div>
    );
}
