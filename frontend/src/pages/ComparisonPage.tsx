import { useState, useCallback, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { LanguageSelector } from '../components/LanguageSelector';
import { SimilarityDisplay } from '../components/SimilarityDisplay';
import { SentenceSelector } from '../components/SentenceSelector';
import { ComparisonArea } from '../components/ComparisonArea';
import { HeadDirectionPanel } from '../components/HeadDirectionPanel';
import { useLazyLanguageData, useSimilarityData, useHeadDirectionRates } from '../hooks/useLanguageData';
import { LANGUAGE_LOCATIONS } from '../data/languageLocations';
import './ComparisonPage.css';

export function ComparisonPage() {
    const { lang1: urlLang1, lang2: urlLang2 } = useParams<{ lang1?: string; lang2?: string }>();
    const navigate = useNavigate();

    const {
        languageData,
        phraseData,
        loadLanguage,
        isLanguageLoaded,
        isLanguageLoading,
        availableLanguages
    } = useLazyLanguageData();
    const { similarityData } = useSimilarityData();
    const { rates: headDirectionRates } = useHeadDirectionRates();

    const [selectedLang1, setSelectedLang1] = useState(urlLang1 || '');
    const [selectedLang2, setSelectedLang2] = useState(urlLang2 || '');
    const [selectedSentence, setSelectedSentence] = useState<number | null>(null);
    const [showJapaneseTags, setShowJapaneseTags] = useState(false);
    const [showDependencyGraph, setShowDependencyGraph] = useState(true);
    const [zoom, setZoom] = useState(1.0);
    const [loadingMessage, setLoadingMessage] = useState<string | null>(null);

    // selectedLang1/2 is initialized from URL params directly
    // Sync from URL to state only when URL changes AND differs from current state
    useEffect(() => {
        if (urlLang1 && urlLang1 !== selectedLang1) {
            setSelectedLang1(urlLang1);
        }
        if (urlLang2 && urlLang2 !== selectedLang2) {
            setSelectedLang2(urlLang2);
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [urlLang1, urlLang2]);

    // 言語が変更されたら読み込み開始
    useEffect(() => {
        const loadLanguages = async () => {
            const toLoad: string[] = [];

            if (selectedLang1 && !isLanguageLoaded(selectedLang1)) {
                toLoad.push(selectedLang1);
            }
            if (selectedLang2 && !isLanguageLoaded(selectedLang2)) {
                toLoad.push(selectedLang2);
            }

            if (toLoad.length > 0) {
                setLoadingMessage(`${toLoad.join(', ')} を読み込み中...`);
                await Promise.all(toLoad.map(code => loadLanguage(code)));
                setLoadingMessage(null);
            }
        };

        loadLanguages();
    }, [selectedLang1, selectedLang2, isLanguageLoaded, loadLanguage]);

    // 言語が変更されたらURLを更新
    useEffect(() => {
        if (selectedLang1 && selectedLang2) {
            navigate(`/compare/${selectedLang1}/${selectedLang2}`, { replace: true });
        }
    }, [selectedLang1, selectedLang2, navigate]);

    const lang1Data = languageData[selectedLang1] || null;
    const lang2Data = languageData[selectedLang2] || null;
    const phraseData1 = phraseData[selectedLang1] || null;
    const phraseData2 = phraseData[selectedLang2] || null;

    // Check if selected languages are non-PUD
    const lang1Location = LANGUAGE_LOCATIONS.find(l => l.code === selectedLang1);
    const lang2Location = LANGUAGE_LOCATIONS.find(l => l.code === selectedLang2);
    const isLang1NonPUD = lang1Location?.isNonPUD || false;
    const isLang2NonPUD = lang2Location?.isNonPUD || false;
    const hasNonPUD = isLang1NonPUD || isLang2NonPUD;

    // Get similarity scores
    const lang1Full = lang1Data?.language || selectedLang1;
    const lang2Full = lang2Data?.language || selectedLang2;
    const uposSimilarity = similarityData.upos[lang1Full]?.[lang2Full] ?? null;
    const deprelSimilarity = similarityData.deprel[lang1Full]?.[lang2Full] ?? null;
    const phraseSimilarity = similarityData.phrase[lang1Full]?.[lang2Full] ?? null;
    const headDirectionRawSimilarity = similarityData.headDirectionRaw[lang1Full]?.[lang2Full] ?? null;
    const headDirectionMergedSimilarity = similarityData.headDirectionMerged[lang1Full]?.[lang2Full] ?? null;

    // Get sentences for selector
    const sentences = lang1Data && lang2Data
        ? lang1Data.sentences.slice(0, Math.min(lang1Data.sentences.length, lang2Data.sentences.length))
        : [];

    // Auto-select first sentence when both languages are loaded
    // This is a valid use case: syncing component state with async data availability
    useEffect(() => {
        if (lang1Data && lang2Data) {
            setSelectedSentence(0);
        } else {
            setSelectedSentence(null);
        }
    }, [lang1Data, lang2Data]);

    const handleRandomSelect = useCallback(() => {
        if (sentences.length > 0) {
            const randomIndex = Math.floor(Math.random() * sentences.length);
            setSelectedSentence(randomIndex);
        }
    }, [sentences.length]);

    const handleZoomChange = useCallback((delta: number) => {
        setZoom(prev => Math.max(0.5, Math.min(2.0, prev + delta)));
    }, []);

    const handleZoomReset = useCallback(() => {
        setZoom(1.0);
    }, []);

    // ローディング中の表示
    const isLoading = (selectedLang1 && isLanguageLoading(selectedLang1)) ||
        (selectedLang2 && isLanguageLoading(selectedLang2));

    return (
        <div className="comparison-page">
            <header className="comparison-header">
                <Link to="/" className="back-link">
                    <span className="back-icon">←</span>
                    <span>地球へ戻る</span>
                </Link>
                <h1 className="page-title">言語間比較</h1>
                {loadingMessage && (
                    <span className="loading-indicator">{loadingMessage}</span>
                )}
            </header>

            <div className="comparison-content">
                <div className="controls">
                    <div className="control-panel">
                        <LanguageSelector
                            selectedLang1={selectedLang1}
                            selectedLang2={selectedLang2}
                            availableLanguages={availableLanguages}
                            onLang1Change={setSelectedLang1}
                            onLang2Change={setSelectedLang2}
                        />
                        <SimilarityDisplay
                            uposSimilarity={uposSimilarity}
                            deprelSimilarity={deprelSimilarity}
                            phraseSimilarity={phraseSimilarity}
                            headDirectionRawSimilarity={headDirectionRawSimilarity}
                            headDirectionMergedSimilarity={headDirectionMergedSimilarity}
                        />
                    </div>

                    <SentenceSelector
                        sentences={sentences}
                        selectedIndex={selectedSentence}
                        disabled={!selectedLang1 || !selectedLang2 || !!isLoading}
                        showJapaneseTags={showJapaneseTags}
                        showDependencyGraph={showDependencyGraph}
                        onSentenceChange={setSelectedSentence}
                        onRandomSelect={handleRandomSelect}
                        onShowJapaneseTagsChange={setShowJapaneseTags}
                        onShowDependencyGraphChange={setShowDependencyGraph}
                    />
                </div>

                {hasNonPUD && selectedLang1 && selectedLang2 && (
                    <div className="non-pud-warning">
                        <div className="warning-icon">📊</div>
                        <div className="warning-content">
                            <h3>一部の比較機能が制限されています</h3>
                            <p>
                                選択された言語の一方または両方について、文レベルの比較データ（品詞・依存関係）がありません。
                                語順傾向（Head Direction）のみ比較できます。
                            </p>
                        </div>
                    </div>
                )}

                {isLoading ? (
                    <div className="loading-container">
                        <div className="loading-spinner"></div>
                        <p>言語データを読み込んでいます...</p>
                    </div>
                ) : (
                    <ComparisonArea
                        lang1Data={lang1Data}
                        lang2Data={lang2Data}
                        lang1Code={selectedLang1}
                        lang2Code={selectedLang2}
                        phraseData1={phraseData1}
                        phraseData2={phraseData2}
                        sentenceIndex={selectedSentence}
                        showJapaneseTags={showJapaneseTags}
                        showDependencyGraph={showDependencyGraph}
                        zoom={zoom}
                        onZoomChange={handleZoomChange}
                        onZoomReset={handleZoomReset}
                    />
                )}

                <HeadDirectionPanel
                    lang1Name={lang1Full}
                    lang2Name={lang2Full}
                    headDirectionRates={headDirectionRates}
                />
            </div>

            <footer className="comparison-footer">
                <p>Grammatical Cosmos | Data: Universal Dependencies v2.16</p>
            </footer>
        </div>
    );
}
