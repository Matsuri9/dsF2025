"""
CoNLL-U形式のファイルをパースしてJSON形式に変換するユーティリティ
"""

from typing import Dict, List, Any, Optional


# ============================================================
# UPOS/DEPRELマージマッピング
# ============================================================
# 
# Head Direction分析において、次元削減とノイズ軽減のため、
# 意味的に近いタグをグループ化します。
#
# 参考: Universal Dependencies v2 タグセット
# https://universaldependencies.org/u/pos/
# https://universaldependencies.org/u/dep/
# ============================================================

# -----------------------------
# UPOS (品詞) マージマッピング
# -----------------------------
# Universal POSタグ17種類を、語順分析に関連する6カテゴリに統合
#
# NOMINAL: 名詞的要素（主語・目的語になりうる）
#   - NOUN: 普通名詞
#   - PROPN: 固有名詞
#   - PRON: 代名詞
#
# VERBAL: 動詞的要素
#   - VERB: 動詞
#   - AUX: 助動詞
#
# MODIFIER: 修飾語
#   - ADJ: 形容詞
#   - ADV: 副詞
#
# FUNCTION: 機能語（文法関係を示す語）
#   - ADP: 前置詞/後置詞
#   - DET: 限定詞（冠詞など）
#   - PART: 助詞
#   - SCONJ: 従属接続詞
#   - CCONJ: 等位接続詞
#
# OTHER: その他
#   - NUM: 数詞
#   - INTJ: 感動詞
#   - SYM: 記号
#   - X: その他
#
# PUNCT: 句読点（分析から除外する場合が多い）

UPOS_MERGE: Dict[str, str] = {
    # NOMINAL: 名詞的要素
    'NOUN': 'NOMINAL',
    'PROPN': 'NOMINAL',
    'PRON': 'NOMINAL',
    
    # VERBAL: 動詞的要素
    'VERB': 'VERBAL',
    'AUX': 'VERBAL',
    
    # MODIFIER: 修飾語
    'ADJ': 'MODIFIER',
    'ADV': 'MODIFIER',
    
    # FUNCTION: 機能語
    'ADP': 'FUNCTION',
    'DET': 'FUNCTION',
    'PART': 'FUNCTION',
    'SCONJ': 'FUNCTION',
    'CCONJ': 'FUNCTION',
    
    # OTHER: その他
    'NUM': 'OTHER',
    'INTJ': 'OTHER',
    'SYM': 'OTHER',
    'X': 'OTHER',
    
    # PUNCT: 句読点
    'PUNCT': 'PUNCT',
}

# -----------------------------
# DEPREL (係り受け関係) マージマッピング
# -----------------------------
# UDのDEPREL 37種類を、語順分析に関連する7カテゴリに統合
#
# CORE_ARG: コア項（主語・目的語など、動詞の必須項）
#   - nsubj: 名詞主語
#   - obj: 直接目的語
#   - iobj: 間接目的語
#   - csubj: 節主語
#   - ccomp: 補文節
#   - xcomp: open clausal complement
#
# OBLIQUE: 斜格・副詞節
#   - obl: 斜格（前置詞句など）
#   - advcl: 副詞節
#
# MODIFIER: 修飾語
#   - amod: 形容詞修飾語
#   - advmod: 副詞修飾語
#   - nummod: 数詞修飾語
#   - acl: 連体節（名詞を修飾する節）
#
# FUNCTION: 機能語関係
#   - case: 格標識（前置詞・後置詞）
#   - det: 限定詞
#   - mark: 接続標識
#   - cop: コピュラ
#   - aux: 助動詞
#
# NOMINAL_MOD: 名詞修飾語
#   - nmod: 名詞修飾語（所有格など）
#   - appos: 同格
#
# COMPOUND: 複合語
#   - compound: 複合語
#   - flat: フラット構造（固有名詞など）
#   - fixed: 固定表現
#
# COORD: 並列構造
#   - conj: 並列要素
#   - cc: 並列接続詞
#
# その他のタグはすべて 'OTHER' にマッピング

DEPREL_MERGE: Dict[str, str] = {
    # CORE_ARG: コア項
    'nsubj': 'CORE_ARG',
    'obj': 'CORE_ARG',
    'iobj': 'CORE_ARG',
    'csubj': 'CORE_ARG',
    'ccomp': 'CORE_ARG',
    'xcomp': 'CORE_ARG',
    
    # OBLIQUE: 斜格・副詞節
    'obl': 'OBLIQUE',
    'advcl': 'OBLIQUE',
    
    # MODIFIER: 修飾語
    'amod': 'MODIFIER',
    'advmod': 'MODIFIER',
    'nummod': 'MODIFIER',
    'acl': 'MODIFIER',
    
    # FUNCTION: 機能語関係
    'case': 'FUNCTION',
    'det': 'FUNCTION',
    'mark': 'FUNCTION',
    'cop': 'FUNCTION',
    'aux': 'FUNCTION',
    
    # NOMINAL_MOD: 名詞修飾語
    'nmod': 'NOMINAL_MOD',
    'appos': 'NOMINAL_MOD',
    
    # COMPOUND: 複合語
    'compound': 'COMPOUND',
    'flat': 'COMPOUND',
    'fixed': 'COMPOUND',
    
    # COORD: 並列構造
    'conj': 'COORD',
    'cc': 'COORD',
}

# デフォルトのマージ先（マッピングに存在しないタグ用）
UPOS_MERGE_DEFAULT = 'OTHER'
DEPREL_MERGE_DEFAULT = 'OTHER'


def merge_upos(upos: str) -> str:
    """
    UPOSタグをマージ後のカテゴリに変換
    
    Args:
        upos: 元のUPOSタグ（例: 'NOUN', 'VERB'）
    
    Returns:
        マージ後のカテゴリ（例: 'NOMINAL', 'VERBAL'）
    
    Example:
        >>> merge_upos('NOUN')
        'NOMINAL'
        >>> merge_upos('PROPN')
        'NOMINAL'
        >>> merge_upos('VERB')
        'VERBAL'
    """
    return UPOS_MERGE.get(upos, UPOS_MERGE_DEFAULT)


def merge_deprel(deprel: str) -> str:
    """
    DEPRELタグをマージ後のカテゴリに変換
    
    サブタイプ（例: nsubj:pass）がある場合は、
    ベースタイプ（nsubj）のみを使用してマッピングします。
    
    Args:
        deprel: 元のDEPRELタグ（例: 'nsubj', 'nsubj:pass'）
    
    Returns:
        マージ後のカテゴリ（例: 'CORE_ARG'）
    
    Example:
        >>> merge_deprel('nsubj')
        'CORE_ARG'
        >>> merge_deprel('nsubj:pass')
        'CORE_ARG'
        >>> merge_deprel('case')
        'FUNCTION'
    """
    # サブタイプを除去（例: nsubj:pass -> nsubj）
    base_deprel = deprel.split(':')[0] if deprel else ''
    return DEPREL_MERGE.get(base_deprel, DEPREL_MERGE_DEFAULT)


def parse_feats(feats_str: str) -> Dict[str, str]:
    """
    FEATSフィールドをパースして辞書に変換
    例: "Mood=Ind|Number=Sing|Person=3" -> {"Mood": "Ind", "Number": "Sing", "Person": "3"}
    """
    if feats_str == "_" or not feats_str:
        return {}
    
    feats = {}
    for feat in feats_str.split("|"):
        if "=" in feat:
            key, value = feat.split("=", 1)
            feats[key] = value
    return feats


def parse_misc(misc_str: str) -> Dict[str, str]:
    """
    MISCフィールドをパースして辞書に変換
    例: "SpaceAfter=No|TemporalNPAdjunct=Yes" -> {"SpaceAfter": "No", "TemporalNPAdjunct": "Yes"}
    """
    if misc_str == "_" or not misc_str:
        return {}
    
    misc = {}
    for item in misc_str.split("|"):
        if "=" in item:
            key, value = item.split("=", 1)
            misc[key] = value
        else:
            # キーのみの場合
            misc[item] = "Yes"
    return misc


def parse_token_line(line: str) -> Optional[Dict[str, Any]]:
    """
    CoNLL-Uのトークン行をパースして辞書に変換
    
    CoNLL-Uの形式:
    ID FORM LEMMA UPOS XPOS FEATS HEAD DEPREL DEPS MISC
    """
    fields = line.split("\t")
    
    if len(fields) != 10:
        return None
    
    # マルチワードトークン(1-2のような形式)やempty nodeは無視
    token_id = fields[0]
    if "-" in token_id or "." in token_id:
        return None
    
    try:
        return {
            "id": int(fields[0]),
            "form": fields[1],
            "lemma": fields[2],
            "upos": fields[3],
            "xpos": fields[4] if fields[4] != "_" else None,
            "feats": parse_feats(fields[5]),
            "head": int(fields[6]) if fields[6] != "_" else 0,
            "deprel": fields[7] if fields[7] != "_" else None,
            "deps": fields[8] if fields[8] != "_" else None,
            "misc": parse_misc(fields[9])
        }
    except (ValueError, IndexError) as e:
        print(f"Warning: トークン行のパースエラー: {line[:50]}... - {e}")
        return None


def parse_conllu_file(file_path: str, language_name: str) -> Dict[str, Any]:
    """
    CoNLL-Uファイルをパースして構造化データに変換
    
    Args:
        file_path: CoNLL-Uファイルのパス
        language_name: 言語名
    
    Returns:
        パース結果の辞書
    """
    sentences = []
    current_sentence = None
    current_tokens = []
    current_metadata = {}
    
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.rstrip('\n')
            
            # 空行は文の区切り
            if not line.strip():
                if current_sentence is not None and current_tokens:
                    current_sentence["tokens"] = current_tokens
                    sentences.append(current_sentence)
                    current_sentence = None
                    current_tokens = []
                    current_metadata = {}
                continue
            
            # コメント行(メタデータ)
            if line.startswith("#"):
                # メタデータをパース
                if "=" in line:
                    key, value = line[1:].split("=", 1)
                    key = key.strip()
                    value = value.strip()
                    current_metadata[key] = value
                    
                    # 新しい文の開始
                    if key == "sent_id":
                        if current_sentence is not None and current_tokens:
                            current_sentence["tokens"] = current_tokens
                            sentences.append(current_sentence)
                        
                        current_sentence = {
                            "sent_id": value,
                            "text": "",
                            "metadata": {}
                        }
                        current_tokens = []
                    elif key == "text" and current_sentence is not None:
                        current_sentence["text"] = value
                    elif current_sentence is not None:
                        current_sentence["metadata"][key] = value
                continue
            
            # トークン行
            token = parse_token_line(line)
            if token is not None:
                current_tokens.append(token)
        
        # ファイル末尾の文を処理
        if current_sentence is not None and current_tokens:
            current_sentence["tokens"] = current_tokens
            sentences.append(current_sentence)
    
    return {
        "language": language_name,
        "file_path": file_path,
        "sentence_count": len(sentences),
        "sentences": sentences
    }
