// ============================================
// 言語の地理座標データ
// ============================================
// 各言語の代表的な使用地域の座標

export interface LanguageLocation {
    code: string;           // 言語コード
    name: string;           // 英語名
    nameJa: string;         // 日本語名
    lat: number;
    lng: number;
    country: string;        // 国/地域名
    isPrimary: boolean;     // メインノードかどうか
    primaryCode?: string;   // サブノードの場合、紐づくメイン言語コード
    isNonPUD?: boolean;     // PUDデータでない言語（比較機能制限）
}

export const LANGUAGE_LOCATIONS: LanguageLocation[] = [
    // === メインノード（PUDデータあり） ===
    { code: 'ar', name: 'Arabic', nameJa: 'アラビア語', lat: 24.7136, lng: 46.6753, country: 'Saudi Arabia', isPrimary: true },
    { code: 'zh', name: 'Chinese', nameJa: '中国語', lat: 39.9042, lng: 116.4074, country: 'China', isPrimary: true },
    { code: 'cs', name: 'Czech', nameJa: 'チェコ語', lat: 50.0755, lng: 14.4378, country: 'Czech Republic', isPrimary: true },
    { code: 'en', name: 'English', nameJa: '英語', lat: 51.5074, lng: -0.1278, country: 'United Kingdom', isPrimary: true },
    { code: 'fi', name: 'Finnish', nameJa: 'フィンランド語', lat: 60.1699, lng: 24.9384, country: 'Finland', isPrimary: true },
    { code: 'fr', name: 'French', nameJa: 'フランス語', lat: 48.8566, lng: 2.3522, country: 'France', isPrimary: true },
    { code: 'gl', name: 'Galician', nameJa: 'ガリシア語', lat: 42.8782, lng: -8.5448, country: 'Spain (Galicia)', isPrimary: true },
    { code: 'de', name: 'German', nameJa: 'ドイツ語', lat: 52.5200, lng: 13.4050, country: 'Germany', isPrimary: true },
    { code: 'hi', name: 'Hindi', nameJa: 'ヒンディー語', lat: 28.6139, lng: 77.2090, country: 'India', isPrimary: true },
    { code: 'is', name: 'Icelandic', nameJa: 'アイスランド語', lat: 64.1466, lng: -21.9426, country: 'Iceland', isPrimary: true },
    { code: 'id', name: 'Indonesian', nameJa: 'インドネシア語', lat: -6.2088, lng: 106.8456, country: 'Indonesia', isPrimary: true },
    { code: 'it', name: 'Italian', nameJa: 'イタリア語', lat: 41.9028, lng: 12.4964, country: 'Italy', isPrimary: true },
    { code: 'ja', name: 'Japanese', nameJa: '日本語', lat: 35.6762, lng: 139.6503, country: 'Japan', isPrimary: true },
    { code: 'ko', name: 'Korean', nameJa: '韓国語', lat: 37.5665, lng: 126.9780, country: 'South Korea', isPrimary: true },
    { code: 'pt', name: 'Portuguese', nameJa: 'ポルトガル語', lat: 38.7223, lng: -9.1393, country: 'Portugal', isPrimary: true },
    { code: 'ru', name: 'Russian', nameJa: 'ロシア語', lat: 55.7558, lng: 37.6173, country: 'Russia', isPrimary: true },
    { code: 'es', name: 'Spanish', nameJa: 'スペイン語', lat: 40.4168, lng: -3.7038, country: 'Spain', isPrimary: true },
    { code: 'sv', name: 'Swedish', nameJa: 'スウェーデン語', lat: 59.3293, lng: 18.0686, country: 'Sweden', isPrimary: true },
    { code: 'th', name: 'Thai', nameJa: 'タイ語', lat: 13.7563, lng: 100.5018, country: 'Thailand', isPrimary: true },
    { code: 'tr', name: 'Turkish', nameJa: 'トルコ語', lat: 39.9334, lng: 32.8597, country: 'Turkey', isPrimary: true },

    // === 非PUD言語（新規追加） ===
    { code: 'af', name: 'Afrikaans', nameJa: 'アフリカーンス語', lat: -25.7479, lng: 28.2293, country: 'South Africa', isPrimary: true, isNonPUD: true },
    { code: 'fo', name: 'Faroese', nameJa: 'フェロー語', lat: 62.0107, lng: -6.7697, country: 'Faroe Islands', isPrimary: true, isNonPUD: true },
    { code: 'he', name: 'Hebrew', nameJa: 'ヘブライ語', lat: 31.7683, lng: 35.2137, country: 'Israel', isPrimary: true, isNonPUD: true },
    { code: 'ga', name: 'Irish', nameJa: 'アイルランド語', lat: 53.3498, lng: -6.2603, country: 'Ireland', isPrimary: true, isNonPUD: true },
    { code: 'kpv', name: 'Komi_Zyrian', nameJa: 'コミ・ジリェン語', lat: 61.6640, lng: 50.8283, country: 'Russia (Komi)', isPrimary: true, isNonPUD: true },
    { code: 'yrk', name: 'Nenets', nameJa: 'ネネツ語', lat: 66.6644, lng: 66.3858, country: 'Russia (Nenets)', isPrimary: true, isNonPUD: true },
    { code: 'no', name: 'NO', nameJa: 'ノルウェー語', lat: 60.3913, lng: 5.3221, country: 'Norway', isPrimary: true, isNonPUD: true },
    { code: 'sa', name: 'Sanskrit', nameJa: 'サンスクリット語', lat: 28.6139, lng: 77.2090, country: 'India', isPrimary: true, isNonPUD: true },
    { code: 'tl', name: 'Tagalog', nameJa: 'タガログ語', lat: 14.5995, lng: 120.9842, country: 'Philippines', isPrimary: true, isNonPUD: true },
    { code: 'ta', name: 'Tamil', nameJa: 'タミル語', lat: 13.0827, lng: 80.2707, country: 'India (Tamil Nadu)', isPrimary: true, isNonPUD: true },
    { code: 'uz', name: 'Uzbek', nameJa: 'ウズベク語', lat: 41.2995, lng: 69.2401, country: 'Uzbekistan', isPrimary: true, isNonPUD: true },
    { code: 'vi', name: 'Vietnamese', nameJa: 'ベトナム語', lat: 21.0285, lng: 105.8542, country: 'Vietnam', isPrimary: true, isNonPUD: true },
    { code: 'sah', name: 'Yakut', nameJa: 'ヤクート語', lat: 62.0397, lng: 129.7422, country: 'Russia (Sakha)', isPrimary: true, isNonPUD: true },

    // === サブノード（同一言語の別地域） ===
    { code: 'en-us', name: 'English', nameJa: '英語', lat: 38.9072, lng: -77.0369, country: 'United States', isPrimary: false, primaryCode: 'en' },
    { code: 'en-au', name: 'English', nameJa: '英語', lat: -33.8688, lng: 151.2093, country: 'Australia', isPrimary: false, primaryCode: 'en' },
    { code: 'pt-br', name: 'Portuguese', nameJa: 'ポルトガル語', lat: -23.5505, lng: -46.6333, country: 'Brazil', isPrimary: false, primaryCode: 'pt' },
    { code: 'es-mx', name: 'Spanish', nameJa: 'スペイン語', lat: 19.4326, lng: -99.1332, country: 'Mexico', isPrimary: false, primaryCode: 'es' },
    { code: 'es-ar', name: 'Spanish', nameJa: 'スペイン語', lat: -34.6037, lng: -58.3816, country: 'Argentina', isPrimary: false, primaryCode: 'es' },
    { code: 'fr-ca', name: 'French', nameJa: 'フランス語', lat: 45.5017, lng: -73.5673, country: 'Canada (Quebec)', isPrimary: false, primaryCode: 'fr' },
    { code: 'ar-eg', name: 'Arabic', nameJa: 'アラビア語', lat: 30.0444, lng: 31.2357, country: 'Egypt', isPrimary: false, primaryCode: 'ar' },
    { code: 'zh-tw', name: 'Chinese', nameJa: '中国語', lat: 25.0330, lng: 121.5654, country: 'Taiwan', isPrimary: false, primaryCode: 'zh' },
];

// 言語コードから言語情報を取得
export function getLanguageByCode(code: string): LanguageLocation | undefined {
    return LANGUAGE_LOCATIONS.find(lang => lang.code === code);
}

// 言語名から言語情報を取得（メインノードのみ）
export function getLanguageByName(name: string): LanguageLocation | undefined {
    return LANGUAGE_LOCATIONS.find(lang => lang.name === name && lang.isPrimary);
}

// メインノードのみ取得
export function getPrimaryLanguages(): LanguageLocation[] {
    return LANGUAGE_LOCATIONS.filter(lang => lang.isPrimary);
}

// サブノードのみ取得
export function getSecondaryLanguages(): LanguageLocation[] {
    return LANGUAGE_LOCATIONS.filter(lang => !lang.isPrimary);
}

// 同一言語のノードペアを取得（サブノード→メインノード）
export function getSameLanguagePairs(): { from: LanguageLocation; to: LanguageLocation }[] {
    const pairs: { from: LanguageLocation; to: LanguageLocation }[] = [];
    const secondaries = getSecondaryLanguages();

    for (const secondary of secondaries) {
        const primary = LANGUAGE_LOCATIONS.find(
            lang => lang.code === secondary.primaryCode && lang.isPrimary
        );
        if (primary) {
            pairs.push({ from: secondary, to: primary });
        }
    }

    return pairs;
}
