// ============================================
// Language Mappings
// ============================================

export const LANGUAGE_NAMES: { [key: string]: string } = {
    'ar': 'Arabic (アラビア語)',
    'zh': 'Chinese (中国語)',
    'cs': 'Czech (チェコ語)',
    'en': 'English (英語)',
    'fi': 'Finnish (フィンランド語)',
    'fr': 'French (フランス語)',
    'gl': 'Galician (ガリシア語)',
    'de': 'German (ドイツ語)',
    'hi': 'Hindi (ヒンディー語)',
    'is': 'Icelandic (アイスランド語)',
    'id': 'Indonesian (インドネシア語)',
    'it': 'Italian (イタリア語)',
    'ja': 'Japanese (日本語)',
    'ko': 'Korean (韓国語)',
    'pt': 'Portuguese (ポルトガル語)',
    'ru': 'Russian (ロシア語)',
    'es': 'Spanish (スペイン語)',
    'sv': 'Swedish (スウェーデン語)',
    'th': 'Thai (タイ語)',
    'tr': 'Turkish (トルコ語)',
    // 新規追加言語
    'af': 'Afrikaans (アフリカーンス語)',
    'fo': 'Faroese (フェロー語)',
    'he': 'Hebrew (ヘブライ語)',
    'ga': 'Irish (アイルランド語)',
    'kpv': 'Komi Zyrian (コミ・ジリェン語)',
    'yrk': 'Nenets (ネネツ語)',
    'no': 'Norwegian Nynorsk (ノルウェー語・ニーノシュク)',
    'sa': 'Sanskrit (サンスクリット語)',
    'tl': 'Tagalog (タガログ語)',
    'ta': 'Tamil (タミル語)',
    'uz': 'Uzbek (ウズベク語)',
    'vi': 'Vietnamese (ベトナム語)',
    'sah': 'Yakut (ヤクート語)'
};

// ============================================
// UPOS Tag Japanese Mapping
// ============================================

export const UPOS_JA_MAP: { [key: string]: string } = {
    'ADJ': '形容詞',
    'ADP': '助詞/前置詞',
    'ADV': '副詞',
    'AUX': '助動詞',
    'CCONJ': '等位接続詞',
    'DET': '限定詞',
    'INTJ': '間投詞',
    'NOUN': '名詞',
    'NUM': '数詞',
    'PART': '小詞/粒子',
    'PRON': '代名詞',
    'PROPN': '固有名詞',
    'PUNCT': '句読点',
    'SCONJ': '従属接続詞',
    'SYM': '記号',
    'VERB': '動詞',
    'X': 'その他'
};

// ============================================
// DEPREL Tag Japanese Mapping
// ============================================

export const DEPREL_JA_MAP: { [key: string]: string } = {
    'acl': '名詞節修飾',
    'advcl': '副詞節修飾',
    'advmod': '副詞修飾',
    'amod': '形容詞修飾',
    'appos': '同格',
    'aux': '助動詞',
    'case': '格表示',
    'cc': '等位接続',
    'ccomp': '補文',
    'clf': '類別詞',
    'compound': '複合名詞',
    'conj': '結合詞',
    'cop': '連結詞',
    'csubj': '主部',
    'dep': '不明',
    'det': '限定詞',
    'discourse': '談話',
    'dislocated': '転置',
    'expl': '虚辞',
    'fixed': '固定表現',
    'flat': '同格表現',
    'goeswith': '分割表現',
    'iobj': '間接目的',
    'list': 'リスト',
    'mark': '接続詞',
    'nmod': '名詞修飾',
    'nsubj': '主語',
    'nummod': '数詞修飾',
    'obj': '目的語',
    'obl': '斜格名詞',
    'orphan': '独立関係',
    'parataxis': '並列',
    'punct': '句読点',
    'reparandum': '言い直し',
    'root': '根',
    'vocative': '呼びかけ',
    'xcomp': '補体'
};

// ============================================
// Dependency Relation Colors
// ============================================

export const DEPREL_COLORS: { [key: string]: string } = {
    'root': '#333333',
    'nsubj': '#e53935',
    'csubj': '#e53935',
    'obj': '#1e88e5',
    'iobj': '#1e88e5',
    'nmod': '#43a047',
    'amod': '#43a047',
    'advmod': '#fb8c00',
    'cc': '#8e24aa',
    'conj': '#8e24aa',
    'case': '#757575',
    'mark': '#757575',
    'det': '#757575',
    'punct': '#bdbdbd',
    'default': '#9e9e9e'
};

// ============================================
// Data Paths
// ============================================

// Use Vite's base URL for dynamic path resolution
const BASE_URL = import.meta.env.BASE_URL || '/';
export const DATA_BASE_PATH = `${BASE_URL}data`.replace(/\/\//g, '/');
export const PROCESSED_PATH = `${DATA_BASE_PATH}/processed`;
export const PHRASES_PATH = `${DATA_BASE_PATH}/phrases`;
export const RESULTS_PATH = `${DATA_BASE_PATH}/results`;
