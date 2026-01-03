import { useMemo } from 'react';
import type { HeadDirectionRates } from '../types';
import { InfoTooltip } from './InfoTooltip';
import './HeadDirectionPanel.css';

interface Props {
    lang1Name: string;
    lang2Name: string;
    headDirectionRates: HeadDirectionRates;
}

// マージ後のカテゴリの日本語名
const MERGED_UPOS_NAMES: { [key: string]: string } = {
    'NOMINAL': '名詞類',
    'VERBAL': '動詞類',
    'MODIFIER': '修飾語',
    'FUNCTION': '機能語',
    'OTHER': 'その他',
    'PUNCT': '句読点'
};

const MERGED_DEPREL_NAMES: { [key: string]: string } = {
    'CORE_ARG': 'コア項',
    'OBLIQUE': '斜格',
    'MODIFIER': '修飾語',
    'FUNCTION': '機能語',
    'NOMINAL_MOD': '名詞修飾',
    'COMPOUND': '複合語',
    'COORD': '並列',
    'OTHER': 'その他'
};

interface ParsedPair {
    headUpos: string;
    depUpos: string;
    deprel: string;
    key: string;
    lang1Rate: number | null;
    lang2Rate: number | null;
    diff: number | null;
}

export function HeadDirectionPanel({ lang1Name, lang2Name, headDirectionRates }: Props) {
    const pairs = useMemo(() => {
        const result: ParsedPair[] = [];

        for (const [key, rates] of Object.entries(headDirectionRates)) {
            const parts = key.split(',');
            if (parts.length !== 3) continue;

            const [headUpos, depUpos, deprel] = parts;
            const lang1Rate = rates[lang1Name] ?? null;
            const lang2Rate = rates[lang2Name] ?? null;

            // 両言語にデータがあるペアのみ
            if (lang1Rate === null && lang2Rate === null) continue;

            const diff = (lang1Rate !== null && lang2Rate !== null)
                ? lang1Rate - lang2Rate
                : null;

            result.push({
                headUpos,
                depUpos,
                deprel,
                key,
                lang1Rate,
                lang2Rate,
                diff
            });
        }

        // 差分の絶対値でソート（大きい差分を上位に）
        result.sort((a, b) => {
            const absA = a.diff !== null ? Math.abs(a.diff) : 0;
            const absB = b.diff !== null ? Math.abs(b.diff) : 0;
            return absB - absA;
        });

        return result.slice(0, 15); // 上位15件
    }, [headDirectionRates, lang1Name, lang2Name]);

    if (!lang1Name || !lang2Name) {
        return null;
    }

    if (pairs.length === 0) {
        return (
            <div className="head-direction-panel">
                <h3 className="panel-title">Head Direction 比較</h3>
                <p className="no-data">データがありません</p>
            </div>
        );
    }

    return (
        <div className="head-direction-panel">
            <h3 className="panel-title">Head Direction 比較</h3>
            <p className="panel-description">
                Head-Initial率: 1.0に近いほどHeadが前（例: 英語）、0.0に近いほどHeadが後（例: 日本語）
            </p>
            <div className="rates-table">
                <div className="table-header">
                    <span className="col-pair">ペア (Head → Dep, 関係)</span>
                    <span className="col-rate">{lang1Name}</span>
                    <span className="col-rate">{lang2Name}</span>
                    <span className="col-diff">差分</span>
                </div>
                {pairs.map((pair) => {
                    const headLabel = MERGED_UPOS_NAMES[pair.headUpos] || pair.headUpos;
                    const depLabel = MERGED_UPOS_NAMES[pair.depUpos] || pair.depUpos;
                    const deprelLabel = MERGED_DEPREL_NAMES[pair.deprel] || pair.deprel;

                    return (
                        <div className="table-row" key={pair.key}>
                            <span className="col-pair">
                                <span className="pair-main">{headLabel} → {depLabel}</span>
                                <span className="pair-deprel">{deprelLabel}</span>
                            </span>
                            <span className="col-rate">
                                {pair.lang1Rate !== null ? pair.lang1Rate.toFixed(2) : '—'}
                            </span>
                            <span className="col-rate">
                                {pair.lang2Rate !== null ? pair.lang2Rate.toFixed(2) : '—'}
                            </span>
                            <span className={`col-diff ${getDiffClass(pair.diff)}`}>
                                {pair.diff !== null ? (
                                    <>
                                        {pair.diff >= 0 ? '+' : ''}{pair.diff.toFixed(2)}
                                        {getDiffIndicator(pair.diff)}
                                    </>
                                ) : '—'}
                            </span>
                        </div>
                    );
                })}
            </div>
        </div>
    );
}

function getDiffClass(diff: number | null): string {
    if (diff === null) return '';
    const abs = Math.abs(diff);
    if (abs > 0.5) return 'diff-large';
    if (abs > 0.2) return 'diff-medium';
    return 'diff-small';
}

function getDiffIndicator(diff: number): string {
    const abs = Math.abs(diff);
    if (abs > 0.5) return ' ◆';
    if (abs > 0.2) return ' ◇';
    return '';
}
