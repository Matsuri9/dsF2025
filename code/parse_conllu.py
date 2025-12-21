"""
CoNLL-Uファイルを解析してJSON形式に変換するスクリプト
全ての言語のCoNLL-Uファイルを処理し、data/processed/にJSON出力する
"""

import json
import os
from pathlib import Path
from utils import parse_conllu_file


# 言語コードと言語名のマッピング
LANGUAGE_MAPPING = {
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
    "tr": "Turkish"
}


def process_all_conllu_files():
    """全てのCoNLL-Uファイルを処理してJSONに変換"""
    
    # パスの設定
    project_root = Path(__file__).parent.parent
    raw_dir = project_root / "data" / "raw"
    processed_dir = project_root / "data" / "processed"
    
    # processed ディレクトリを作成
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    # 各言語ディレクトリを処理
    processed_count = 0
    total_sentences = 0
    
    print("CoNLL-Uファイルの処理を開始します...")
    print("=" * 70)
    
    for lang_dir in sorted(raw_dir.iterdir()):
        if not lang_dir.is_dir():
            continue
        
        # CoNLL-Uファイルを検索
        conllu_files = list(lang_dir.glob("*.conllu"))
        
        if not conllu_files:
            print(f"⚠ {lang_dir.name}: CoNLL-Uファイルが見つかりません")
            continue
        
        for conllu_file in conllu_files:
            # 言語コードを抽出 (例: en_pud-ud-test.conllu -> en)
            lang_code = conllu_file.stem.split("_")[0]
            language_name = LANGUAGE_MAPPING.get(lang_code, lang_code.upper())
            
            print(f"\n処理中: {language_name} ({conllu_file.name})")
            
            try:
                # CoNLL-Uファイルをパース
                data = parse_conllu_file(str(conllu_file), language_name)
                
                # JSONファイルとして保存
                output_file = processed_dir / f"{lang_code}_pud.json"
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
    process_all_conllu_files()
