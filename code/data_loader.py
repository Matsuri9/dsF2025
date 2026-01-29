#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
データ読み込みモジュール

各種データファイル（processed JSON, phrases JSONなど）の読み込み機能を提供します。
"""

import json
from pathlib import Path
from typing import Dict, List, Any


# ============================================================
# 言語コードと言語名のマッピング
# ============================================================

# PUD (Parallel Universal Dependencies) 言語
PUD_LANGUAGE_MAPPING: Dict[str, str] = {
    "ar": "Arabic",
    "zh": "Chinese",
    "cs": "Czech",
    "en": "English",
    "fi": "Finnish",
    "fr": "French",
    "gl": "Galician",
    "de": "German",
    "hi": "Hindi",
    "is": "Icelandic",
    "id": "Indonesian",
    "it": "Italian",
    "ja": "Japanese",
    "ko": "Korean",
    "pt": "Portuguese",
    "ru": "Russian",
    "es": "Spanish",
    "sv": "Swedish",
    "th": "Thai",
    "tr": "Turkish",
}

# 追加言語
ADDITIONAL_LANGUAGE_MAPPING: Dict[str, str] = {
    "af": "Afrikaans",
    "fo": "Faroese",
    "he": "Hebrew",
    "ga": "Irish",
    "kpv": "Komi_Zyrian",
    "yrk": "Nenets",
    "nn": "Norwegian_Nynorsk",
    "no": "Norwegian",
    "sa": "Sanskrit",
    "tl": "Tagalog",
    "ta": "Tamil",
    "uz": "Uzbek",
    "vi": "Vietnamese",
    "sah": "Yakut",
}

# 全言語のマッピング
ALL_LANGUAGE_MAPPING: Dict[str, str] = {
    **PUD_LANGUAGE_MAPPING,
    **ADDITIONAL_LANGUAGE_MAPPING,
}


def get_language_name(lang_code: str) -> str:
    """
    言語コードから言語名を取得
    
    Args:
        lang_code: 言語コード（例: 'en', 'ja'）
    
    Returns:
        言語名（見つからない場合はコードを大文字にしたもの）
    """
    return ALL_LANGUAGE_MAPPING.get(lang_code, lang_code.upper())


# ============================================================
# データ読み込み関数
# ============================================================

def load_all_languages(processed_dir: Path) -> Dict[str, List[Dict]]:
    """
    全言語のパース済みデータを読み込む
    
    Args:
        processed_dir: パース済みJSONファイルが格納されたディレクトリ
    
    Returns:
        {言語名: [文データ, ...]} の辞書
        各文データには 'tokens' キーがあり、トークンのリストを含む
    
    Example:
        >>> data = load_all_languages(Path('data/processed'))
        >>> print(data.keys())
        dict_keys(['Arabic', 'Chinese', 'Czech', ...])
    """
    data = {}
    
    for json_file in sorted(processed_dir.glob("*.json")):
        with open(json_file, 'r', encoding='utf-8') as f:
            file_data = json.load(f)
        
        language = file_data["language"]
        data[language] = file_data["sentences"]
        
    return data


def load_sentences_upos(processed_dir: Path) -> Dict[str, List[List[str]]]:
    """
    各言語の文をUPOS列として読み込む
    
    Args:
        processed_dir: パース済みJSONファイルが格納されたディレクトリ
    
    Returns:
        {language: [[upos1, upos2, ...], [upos1, ...], ...]}
    """
    data = {}
    
    for json_file in sorted(processed_dir.glob("*.json")):
        with open(json_file, 'r', encoding='utf-8') as f:
            file_data = json.load(f)
        
        language = file_data["language"]
        sentences = []
        
        for sent in file_data["sentences"]:
            upos_seq = []
            for token in sent.get("tokens", []):
                upos = token.get("upos")
                if upos:
                    upos_seq.append(upos)
            if upos_seq:
                sentences.append(upos_seq)
        
        data[language] = sentences
    
    return data


def load_sentences_deprel(processed_dir: Path) -> Dict[str, List[List[str]]]:
    """
    各言語の文をDEPREL列として読み込む（ベースタグのみ）
    
    Args:
        processed_dir: パース済みJSONファイルが格納されたディレクトリ
    
    Returns:
        {language: [[deprel1, deprel2, ...], ...]}
    """
    data = {}
    
    for json_file in sorted(processed_dir.glob("*.json")):
        with open(json_file, 'r', encoding='utf-8') as f:
            file_data = json.load(f)
        
        language = file_data["language"]
        sentences = []
        
        for sent in file_data["sentences"]:
            deprel_seq = []
            for token in sent.get("tokens", []):
                deprel = token.get("deprel")
                if deprel:
                    # サブタイプを除去
                    base_deprel = deprel.split(':')[0]
                    deprel_seq.append(base_deprel)
            if deprel_seq:
                sentences.append(deprel_seq)
        
        data[language] = sentences
    
    return data


def load_sentences_phrase_heads(phrases_dir: Path) -> Dict[str, List[List[str]]]:
    """
    各言語の文を句の主辞UPOS列として読み込む
    
    Args:
        phrases_dir: phrasesディレクトリのパス
    
    Returns:
        {language: [[head_upos1, head_upos2, ...], ...]}
    """
    data = {}
    
    # PUD形式とその他の形式に対応
    for pattern in ["*_pud_phrases.json", "*_phrases.json"]:
        for json_file in sorted(phrases_dir.glob(pattern)):
            # 重複を避ける
            if json_file.stem.replace("_phrases", "") in [k.lower() for k in data.keys()]:
                continue
                
            with open(json_file, 'r', encoding='utf-8') as f:
                file_data = json.load(f)
            
            language = file_data["language"]
            
            # 既に読み込み済みならスキップ
            if language in data:
                continue
            
            sentences = []
            
            for sent in file_data["sentences"]:
                head_upos_seq = []
                for phrase in sent.get("phrases", []):
                    head_upos = phrase.get("head_upos")
                    if head_upos:
                        head_upos_seq.append(head_upos)
                if head_upos_seq:
                    sentences.append(head_upos_seq)
            
            if sentences:
                data[language] = sentences
    
    return data


def load_processed_file(file_path: Path) -> Dict[str, Any]:
    """
    単一のprocessed JSONファイルを読み込む
    
    Args:
        file_path: JSONファイルのパス
    
    Returns:
        パース済みデータの辞書
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_json(data: Dict[str, Any], output_path: Path, indent: int = 2) -> None:
    """
    データをJSONファイルとして保存
    
    Args:
        data: 保存するデータ
        output_path: 出力ファイルパス
        indent: インデント幅
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=indent)
