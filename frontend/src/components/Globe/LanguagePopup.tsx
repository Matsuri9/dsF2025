import type { HeadDirectionRates } from '../../types';
import { getLanguageByName, getPrimaryLanguages } from '../../data/languageLocations';
import './LanguagePopup.css';

interface Props {
    languageName: string;
    headDirectionRates: HeadDirectionRates;
    onClose: () => void;
}

// 言語の語順傾向を判定
function getWordOrderTendency(
    languageName: string,
    rates: HeadDirectionRates
): { tendency: string; tendencyEn: string; description: string; color: string } {
    const verbObjKey = 'VERBAL,NOMINAL,CORE_ARG';
    const rate = rates[verbObjKey]?.[languageName];

    if (rate === null || rate === undefined) {
        return {
            tendency: '不明',
            tendencyEn: 'Unknown',
            description: 'データが不足しています',
            color: '#64748b'
        };
    }

    if (rate > 0.7) {
        return {
            tendency: 'Head-Initial',
            tendencyEn: 'VO型',
            description: '動詞が目的語より前に来る傾向',
            color: '#22c55e'
        };
    } else if (rate < 0.3) {
        return {
            tendency: 'Head-Final',
            tendencyEn: 'OV型',
            description: '動詞が目的語より後に来る傾向',
            color: '#3b82f6'
        };
    } else {
        return {
            tendency: '混合型',
            tendencyEn: 'Mixed',
            description: '語順が比較的自由・文脈依存',
            color: '#a855f7'
        };
    }
}

// 主要なHead-Initial率を抽出
function getKeyRates(languageName: string, rates: HeadDirectionRates): {
    label: string;
    labelShort: string;
    rate: number | null;
    description: string;
}[] {
    const keyPairs = [
        {
            key: 'VERBAL,NOMINAL,CORE_ARG',
            label: '動詞 → 名詞',
            labelShort: 'V→N',
            description: '目的語の位置'
        },
        {
            key: 'NOMINAL,MODIFIER,MODIFIER',
            label: '名詞 → 修飾語',
            labelShort: 'N→Mod',
            description: '形容詞・関係節の位置'
        },
        {
            key: 'NOMINAL,FUNCTION,FUNCTION',
            label: '名詞 → 機能語',
            labelShort: 'N→Func',
            description: '前置詞・後置詞'
        },
    ];

    return keyPairs.map(({ key, label, labelShort, description }) => ({
        label,
        labelShort,
        rate: rates[key]?.[languageName] ?? null,
        description
    }));
}

// 類似言語を取得
function getSimilarLanguages(languageName: string, rates: HeadDirectionRates): string[] {
    const targetKey = 'VERBAL,NOMINAL,CORE_ARG';
    const targetRate = rates[targetKey]?.[languageName];

    if (targetRate === null || targetRate === undefined) return [];

    const primaryLangs = getPrimaryLanguages();
    const similar: { name: string; diff: number }[] = [];

    for (const lang of primaryLangs) {
        if (lang.name === languageName) continue;
        const rate = rates[targetKey]?.[lang.name];
        if (rate === null || rate === undefined) continue;

        const diff = Math.abs(rate - targetRate);
        if (diff < 0.15) {
            similar.push({ name: lang.nameJa, diff });
        }
    }

    return similar
        .sort((a, b) => a.diff - b.diff)
        .slice(0, 3)
        .map(s => s.name);
}

export function LanguagePopup({ languageName, headDirectionRates, onClose }: Props) {
    const langInfo = getLanguageByName(languageName);
    const tendency = getWordOrderTendency(languageName, headDirectionRates);
    const keyRates = getKeyRates(languageName, headDirectionRates);
    const similarLangs = getSimilarLanguages(languageName, headDirectionRates);

    if (!langInfo) {
        return null;
    }

    return (
        <div className="popup-overlay" onClick={onClose}>
            <div className="language-popup" onClick={(e) => e.stopPropagation()}>
                <button className="popup-close" onClick={onClose}>×</button>

                {/* ヘッダー */}
                <div className="popup-header">
                    <div className="header-main">
                        <h2 className="popup-title">{langInfo.nameJa}</h2>
                        <span className="popup-english">{langInfo.name}</span>
                    </div>
                    <div className="header-location">
                        <span className="location-icon">📍</span>
                        <span>{langInfo.country}</span>
                    </div>
                </div>

                {/* 語順傾向バッジ */}
                <div className="tendency-section">
                    <div
                        className="tendency-badge"
                        style={{
                            backgroundColor: `${tendency.color}20`,
                            borderColor: `${tendency.color}40`,
                            color: tendency.color
                        }}
                    >
                        <span className="tendency-main">{tendency.tendency}</span>
                        <span className="tendency-sub">{tendency.tendencyEn}</span>
                    </div>
                    <p className="tendency-description">{tendency.description}</p>
                </div>

                {/* Head-Initial率 */}
                <div className="rates-section">
                    <h4 className="section-title">Head-Initial率</h4>
                    <div className="rates-grid">
                        {keyRates.map(({ label, labelShort, rate, description }) => (
                            <div className="rate-card" key={label}>
                                <div className="rate-header">
                                    <span className="rate-label">{labelShort}</span>
                                    <span className="rate-value">
                                        {rate !== null ? `${(rate * 100).toFixed(0)}%` : '—'}
                                    </span>
                                </div>
                                {rate !== null && (
                                    <div className="rate-bar-container">
                                        <div
                                            className="rate-bar-fill"
                                            style={{
                                                width: `${rate * 100}%`,
                                                backgroundColor: rate > 0.5 ? '#22c55e' : '#3b82f6'
                                            }}
                                        />
                                    </div>
                                )}
                                <span className="rate-description">{description}</span>
                            </div>
                        ))}
                    </div>
                </div>

                {/* 類似言語 */}
                {similarLangs.length > 0 && (
                    <div className="similar-section">
                        <h4 className="section-title">類似した語順の言語</h4>
                        <div className="similar-tags">
                            {similarLangs.map(lang => (
                                <span className="similar-tag" key={lang}>{lang}</span>
                            ))}
                        </div>
                    </div>
                )}

                {/* フッター */}
                <div className="popup-footer">
                    <span className="footer-hint">💡 線をクリックして他の言語と比較</span>
                </div>
            </div>
        </div>
    );
}
