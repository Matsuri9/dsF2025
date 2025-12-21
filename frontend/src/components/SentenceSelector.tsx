import type { Sentence } from '../types';
import './SentenceSelector.css';

interface Props {
    sentences: Sentence[];
    selectedIndex: number | null;
    disabled: boolean;
    showJapaneseTags: boolean;
    showDependencyGraph: boolean;
    onSentenceChange: (index: number) => void;
    onRandomSelect: () => void;
    onShowJapaneseTagsChange: (checked: boolean) => void;
    onShowDependencyGraphChange: (checked: boolean) => void;
}

export function SentenceSelector({
    sentences,
    selectedIndex,
    disabled,
    showJapaneseTags,
    showDependencyGraph,
    onSentenceChange,
    onRandomSelect,
    onShowJapaneseTagsChange,
    onShowDependencyGraphChange
}: Props) {
    return (
        <div className="sentence-selector">
            <label htmlFor="sentenceSelect">文を選択:</label>
            <select
                id="sentenceSelect"
                className="sentence-select"
                disabled={disabled}
                value={selectedIndex !== null ? selectedIndex : ''}
                onChange={(e) => onSentenceChange(parseInt(e.target.value))}
            >
                <option value="">
                    {disabled ? 'まず言語を選択してください' : '文を選択してください'}
                </option>
                {sentences.map((sent, index) => (
                    <option key={sent.sent_id} value={index}>
                        {index + 1}. {sent.sent_id} - {sent.text.substring(0, 50)}...
                    </option>
                ))}
            </select>
            <button
                className="btn btn-secondary"
                disabled={disabled}
                onClick={onRandomSelect}
            >
                ランダム選択
            </button>
            <div className="display-options">
                <label className="checkbox-label">
                    <input
                        type="checkbox"
                        checked={showJapaneseTags}
                        onChange={(e) => onShowJapaneseTagsChange(e.target.checked)}
                    />
                    タグを日本語で表示
                </label>
                <label className="checkbox-label" style={{ marginLeft: '15px' }}>
                    <input
                        type="checkbox"
                        checked={showDependencyGraph}
                        onChange={(e) => onShowDependencyGraphChange(e.target.checked)}
                    />
                    係り受けグラフを表示
                </label>
            </div>
        </div>
    );
}
