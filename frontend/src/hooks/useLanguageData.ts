import { useState, useEffect, useCallback } from "react";
import type {
  LanguageData,
  PhraseData,
  SimilarityData,
  SimilarityMatrix,
  HeadDirectionRates,
} from "../types";
import {
  LANGUAGE_NAMES,
  PROCESSED_PATH,
  PHRASES_PATH,
  RESULTS_PATH,
} from "../constants";

// ============================================
// CSV Parser
// ============================================

function parseCSV(csvText: string): SimilarityMatrix {
  const lines = csvText.trim().split("\n");
  const headers = lines[0].split(",").slice(1);
  const matrix: SimilarityMatrix = {};

  for (let i = 1; i < lines.length; i++) {
    const values = lines[i].split(",");
    const rowLang = values[0];
    matrix[rowLang] = {};

    for (let j = 1; j < values.length; j++) {
      const colLang = headers[j - 1];
      matrix[rowLang][colLang] = parseFloat(values[j]);
    }
  }

  return matrix;
}

function parseHeadDirectionRatesCSV(csvText: string): HeadDirectionRates {
  const lines = csvText.trim().split("\n");
  if (lines.length < 2) return {};

  const headers = lines[0].split(",");
  const languageHeaders = headers.slice(3);

  const rates: HeadDirectionRates = {};

  for (let i = 1; i < lines.length; i++) {
    const values = lines[i].split(",");
    if (values.length < 4) continue;

    const headUpos = values[0];
    const depUpos = values[1];
    const deprel = values[2];
    const key = `${headUpos},${depUpos},${deprel}`;

    rates[key] = {};

    for (let j = 0; j < languageHeaders.length; j++) {
      const lang = languageHeaders[j];
      const value = values[3 + j];
      rates[key][lang] =
        value && value.trim() !== "" ? parseFloat(value) : null;
    }
  }

  return rates;
}

// ============================================
// 遅延読み込み用キャッシュ
// ============================================

// グローバルキャッシュ（コンポーネント間で共有）
const languageDataCache: { [key: string]: LanguageData } = {};
const phraseDataCache: { [key: string]: PhraseData } = {};
const failedLanguagesCache: Set<string> = new Set();

// ============================================
// useLazyLanguageData Hook（遅延読み込み版）
// ============================================

export function useLazyLanguageData() {
  const [languageData, setLanguageData] = useState<{
    [key: string]: LanguageData;
  }>(languageDataCache);
  const [phraseData, setPhraseData] = useState<{ [key: string]: PhraseData }>(
    phraseDataCache,
  );
  const [loadingLanguages, setLoadingLanguages] = useState<Set<string>>(
    new Set(),
  );
  const [error, setError] = useState<string | null>(null);

  // 言語データを読み込む（キャッシュがあればスキップ）
  const loadLanguage = useCallback(
    async (code: string): Promise<boolean> => {
      // 既にキャッシュにある場合はスキップ
      if (languageDataCache[code]) {
        return true;
      }

      // 既に失敗した言語はスキップ（無限ループ防止）
      if (failedLanguagesCache.has(code)) {
        return false;
      }

      // 既に読み込み中の場合はスキップ
      if (loadingLanguages.has(code)) {
        return false;
      }

      setLoadingLanguages((prev) => new Set(prev).add(code));

      try {
        // まずPUD形式を試行
        let langResponse = await fetch(`${PROCESSED_PATH}/${code}_pud.json`);
        let phraseResponse = await fetch(
          `${PHRASES_PATH}/${code}_pud_phrases.json`,
        );

        // PUD形式で失敗した場合、非PUD形式を試行
        if (!langResponse.ok) {
          langResponse = await fetch(`${PROCESSED_PATH}/${code}.json`);
          phraseResponse = await fetch(`${PHRASES_PATH}/${code}_phrases.json`);
        }

        if (langResponse.ok) {
          const data = await langResponse.json();
          languageDataCache[code] = data;
          setLanguageData((prev) => ({ ...prev, [code]: data }));
        }

        if (phraseResponse.ok) {
          const data = await phraseResponse.json();
          phraseDataCache[code] = data;
          setPhraseData((prev) => ({ ...prev, [code]: data }));
        }

        setLoadingLanguages((prev) => {
          const next = new Set(prev);
          next.delete(code);
          return next;
        });

        return langResponse.ok;
      } catch (e) {
        console.warn(`Failed to load ${code}:`, e);
        failedLanguagesCache.add(code);
        setError(`Failed to load ${code}`);
        setLoadingLanguages((prev) => {
          const next = new Set(prev);
          next.delete(code);
          return next;
        });
        return false;
      }
    },
    [loadingLanguages],
  );

  // 言語がロード済みかどうかを確認
  const isLanguageLoaded = useCallback((code: string): boolean => {
    return !!languageDataCache[code];
  }, []);

  // 言語が読み込み中かどうかを確認
  const isLanguageLoading = useCallback(
    (code: string): boolean => {
      return loadingLanguages.has(code);
    },
    [loadingLanguages],
  );

  // 利用可能な言語コード一覧
  const availableLanguages = Object.keys(LANGUAGE_NAMES);

  return {
    languageData,
    phraseData,
    loadLanguage,
    isLanguageLoaded,
    isLanguageLoading,
    availableLanguages,
    error,
  };
}

// ============================================
// useLanguageData Hook（後方互換用：全データ一括読み込み）
// ============================================

export function useLanguageData() {
  const [languageData, setLanguageData] = useState<{
    [key: string]: LanguageData;
  }>({});
  const [phraseData, setPhraseData] = useState<{ [key: string]: PhraseData }>(
    {},
  );
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadData() {
      const langData: { [key: string]: LanguageData } = {};
      const phData: { [key: string]: PhraseData } = {};
      const languageCodes = Object.keys(LANGUAGE_NAMES);

      try {
        for (const code of languageCodes) {
          try {
            const response = await fetch(`${PROCESSED_PATH}/${code}_pud.json`);
            if (response.ok) {
              const data = await response.json();
              langData[code] = data;
            }
          } catch (e) {
            console.warn(`Failed to load ${code}_pud.json:`, e);
          }
        }

        for (const code of languageCodes) {
          try {
            const response = await fetch(
              `${PHRASES_PATH}/${code}_pud_phrases.json`,
            );
            if (response.ok) {
              const data = await response.json();
              phData[code] = data;
            }
          } catch (e) {
            console.warn(`Failed to load ${code}_pud_phrases.json:`, e);
          }
        }

        setLanguageData(langData);
        setPhraseData(phData);
        setLoading(false);
      } catch {
        setError("Failed to load language data");
        setLoading(false);
      }
    }

    loadData();
  }, []);

  return { languageData, phraseData, loading, error };
}

// ============================================
// useSimilarityData Hook
// ============================================

export function useSimilarityData() {
  const [similarityData, setSimilarityData] = useState<SimilarityData>({
    upos: {},
    deprel: {},
    phrase: {},
    headDirectionRaw: {},
    headDirectionMerged: {},
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      const data: SimilarityData = {
        upos: {},
        deprel: {},
        phrase: {},
        headDirectionRaw: {},
        headDirectionMerged: {},
      };

      try {
        const [
          uposResponse,
          deprelResponse,
          phraseResponse,
          headDirRawResponse,
          headDirMergedResponse,
        ] = await Promise.all([
          fetch(`${RESULTS_PATH}/upos_similarity_cosine.csv`),
          fetch(`${RESULTS_PATH}/deprel_similarity_cosine.csv`),
          fetch(`${RESULTS_PATH}/phrase_similarity_cosine.csv`),
          fetch(`${RESULTS_PATH}/head_direction_distance_cosine_raw.csv`),
          fetch(`${RESULTS_PATH}/head_direction_distance_cosine_merged.csv`),
        ]);

        if (uposResponse.ok) {
          data.upos = parseCSV(await uposResponse.text());
        }
        if (deprelResponse.ok) {
          data.deprel = parseCSV(await deprelResponse.text());
        }
        if (phraseResponse.ok) {
          data.phrase = parseCSV(await phraseResponse.text());
        }
        if (headDirRawResponse.ok) {
          data.headDirectionRaw = parseCSV(await headDirRawResponse.text());
        }
        if (headDirMergedResponse.ok) {
          data.headDirectionMerged = parseCSV(
            await headDirMergedResponse.text(),
          );
        }

        setSimilarityData(data);
      } catch (e) {
        console.warn("Failed to load similarity data:", e);
      }

      setLoading(false);
    }

    loadData();
  }, []);

  return { similarityData, loading };
}

// ============================================
// useHeadDirectionRates Hook
// ============================================

export function useHeadDirectionRates() {
  const [rates, setRates] = useState<HeadDirectionRates>({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      try {
        const response = await fetch(
          `${RESULTS_PATH}/head_direction_rates_merged.csv`,
        );
        if (response.ok) {
          const csvText = await response.text();
          setRates(parseHeadDirectionRatesCSV(csvText));
        }
      } catch (e) {
        console.warn("Failed to load head direction rates:", e);
      }
      setLoading(false);
    }

    loadData();
  }, []);

  return { rates, loading };
}
