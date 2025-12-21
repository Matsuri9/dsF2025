"""
新しい言語のCoNLL-Uファイルを解析してJSON形式に変換するスクリプト
最大1000文までを処理する
"""

import json
import os
from pathlib import Path
from utils import parse_conllu_file


# 新しい言語のコードと言語名のマッピング
NEW_LANGUAGE_MAPPING = {
    "af": "Afrikaans",
    "fo": "Faroese",
    "he": "Hebrew",
    "ga": "Irish",
    "kpv": "Komi_Zyrian",
    "yrk": "Nenets",
    "nn": "Norwegian_Nynorsk",
    "sa": "Sanskrit",
    "tl": "Tagalog",
    "ta": "Tamil",
    "uz": "Uzbek",
    "vi": "Vietnamese",
    "sah": "Yakut"
}

MAX_SENTENCES = 1000


def parse_conllu_file_limited(file_path: str, language_name: str, max_sentences: int = MAX_SENTENCES):
    """
    CoNLL-Uファイルをパースして構造化データに変換（文数制限あり）
    
    Args:
        file_path: CoNLL-Uファイルのパス
        language_name: 言語名
        max_sentences: 最大文数（デフォルト1000）
    
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
            
            # 最大文数に達したら終了
            if len(sentences) >= max_sentences:
                break
            
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
            from utils import parse_token_line
            token = parse_token_line(line)
            if token is not None:
                current_tokens.append(token)
        
        # ファイル末尾の文を処理
        if current_sentence is not None and current_tokens and len(sentences) < max_sentences:
            current_sentence["tokens"] = current_tokens
            sentences.append(current_sentence)
    
    return {
        "language": language_name,
        "file_path": file_path,
        "sentence_count": len(sentences),
        "sentences": sentences
    }


def process_new_languages():
    """新しい言語のCoNLL-Uファイルを処理してJSONに変換"""
    
    # パスの設定
    project_root = Path(__file__).parent.parent
    raw_dir = project_root / "data" / "raw"
    processed_dir = project_root / "data" / "processed"
    
    # processed ディレクトリを作成
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    # 処理対象のディレクトリ名パターン
    target_patterns = [
        "UD_Afrikaans-AfriBooms",
        "UD_Faroese-OFT",
        "UD_Hebrew-IAHLTwiki",
        "UD_Irish-TwittIrish",
        "UD_Komi_Zyrian-Lattice",
        "UD_Nenets-Tundra",
        "UD_Norwegian-NynorskLIA",
        "UD_Sanskrit-UFAL",
        "UD_Tagalog-TRG",
        "UD_Tamil-TTB",
        "UD_Uzbek-UzUDT",
        "UD_Vietnamese-VTB",
        "UD_Yakut-YKTDT"
    ]
    
    processed_count = 0
    total_sentences = 0
    
    print("新言語のCoNLL-Uファイルの処理を開始します...")
    print(f"最大文数: {MAX_SENTENCES}")
    print("=" * 70)
    
    for pattern in target_patterns:
        # パターンに一致するディレクトリを検索
        matching_dirs = list(raw_dir.glob(f"{pattern}*"))
        
        if not matching_dirs:
            print(f"⚠ {pattern}: ディレクトリが見つかりません")
            continue
        
        for lang_dir in matching_dirs:
            if not lang_dir.is_dir():
                continue
            
            # CoNLL-Uファイルを検索
            conllu_files = list(lang_dir.glob("*.conllu"))
            
            if not conllu_files:
                print(f"⚠ {lang_dir.name}: CoNLL-Uファイルが見つかりません")
                continue
            
            for conllu_file in conllu_files:
                # 言語コードを抽出
                lang_code = conllu_file.stem.split("_")[0].split("-")[0]
                language_name = NEW_LANGUAGE_MAPPING.get(lang_code, lang_code.upper())
                
                print(f"\n処理中: {language_name} ({conllu_file.name})")
                
                try:
                    # CoNLL-Uファイルをパース（最大1000文）
                    data = parse_conllu_file_limited(str(conllu_file), language_name, MAX_SENTENCES)
                    
                    # 文数が制限に達した場合は警告を表示
                    if data["sentence_count"] >= MAX_SENTENCES:
                        print(f"  ⚠ 最大{MAX_SENTENCES}文に達したため、残りはスキップしました")
                    
                    # JSONファイルとして保存
                    output_file = processed_dir / f"{lang_code}.json"
                    with open(output_file, 'w', encoding='utf-8') as f:
                        json.dump(data, f, ensure_ascii=False, indent=2)
                    
                    processed_count += 1
                    total_sentences += data["sentence_count"]
                    
                    print(f"  ✓ 完了: {data['sentence_count']} 文を処理")
                    print(f"  出力: {output_file.name}")
                    
                except Exception as e:
                    print(f"  ✗ エラー: {conllu_file.name} - {e}")
                    import traceback
                    traceback.print_exc()
    
    print("\n" + "=" * 70)
    print(f"処理完了:")
    print(f"  - 処理した言語数: {processed_count}")
    print(f"  - 総文数: {total_sentences}")
    print(f"  - 出力ディレクトリ: {processed_dir}")


if __name__ == "__main__":
    process_new_languages()
