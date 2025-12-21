// ============================================
// Data Types
// ============================================

export interface Token {
    id: string;
    form: string;
    upos: string;
    deprel: string;
    head: string;
}

export interface Sentence {
    sent_id: string;
    text: string;
    tokens: Token[];
}

export interface LanguageData {
    language: string;
    sentences: Sentence[];
}

export interface PhraseToken {
    id: string;
    form: string;
}

export interface Phrase {
    head_id: string;
    head_upos: string;
    tokens: PhraseToken[];
}

export interface PhraseSentence {
    sent_id: string;
    phrases: Phrase[];
}

export interface PhraseData {
    language: string;
    total_phrases: number;
    sentences: PhraseSentence[];
}

export interface SimilarityMatrix {
    [lang1: string]: { [lang2: string]: number };
}

export interface SimilarityData {
    upos: SimilarityMatrix;
    deprel: SimilarityMatrix;
    phrase: SimilarityMatrix;
    headDirectionRaw: SimilarityMatrix;
    headDirectionMerged: SimilarityMatrix;
}

// Head Direction Rates: { "VERBAL,NOMINAL,CORE_ARG": { "Japanese": 0.02, "English": 0.95 } }
export interface HeadDirectionRates {
    [pairKey: string]: { [lang: string]: number | null };
}

// Parsed head direction pair
export interface HeadDirectionPair {
    headUpos: string;
    depUpos: string;
    deprel: string;
    key: string;
}

// ============================================
// Props Types
// ============================================

export interface LanguageSelectorProps {
    selectedLang1: string;
    selectedLang2: string;
    availableLanguages: string[];
    onLang1Change: (lang: string) => void;
    onLang2Change: (lang: string) => void;
}

export interface SimilarityDisplayProps {
    uposSimilarity: number | null;
    deprelSimilarity: number | null;
    phraseSimilarity: number | null;
    headDirectionRawSimilarity: number | null;
    headDirectionMergedSimilarity: number | null;
}

export interface SentenceSelectorProps {
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

export interface ComparisonAreaProps {
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

export interface HeadDirectionPanelProps {
    lang1Name: string;
    lang2Name: string;
    headDirectionRates: HeadDirectionRates;
}
