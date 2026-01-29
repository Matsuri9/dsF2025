#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CoNLL-Uファイルパーススクリプト

CoNLL-U形式のファイルを解析してJSON形式に変換します。
data/raw/ 内の全言語ディレクトリを処理し、data/processed/ に出力します。
"""

import json
from pathlib import Path
from typing import Optional, Tuple

from utils import parse_conllu_file
from data_loader import get_language_name


def process_conllu_files(
    raw_dir: Path,
    processed_dir: Path,
    max_sentences_non_pud: Optional[int] = 1000
) -> Tuple[int, int]:
    """
    CoNLL-Uファイルを処理してJSONに変換
    
    Args:
        raw_dir: 入力ディレクトリ（data/raw）
        processed_dir: 出力ディレクトリ（data/processed）
        max_sentences_non_pud: PUD以外の言語の最大文数（Noneなら全文）
    
    Returns:
        (処理したファイル数, 総文数)
    """
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    processed_count = 0
    total_sentences = 0
    
    for lang_dir in sorted(raw_dir.iterdir()):
        if not lang_dir.is_dir():
            continue
        
        conllu_files = list(lang_dir.glob("*.conllu"))
        
        if not conllu_files:
            print(f"⚠ {lang_dir.name}: CoNLL-Uファイルが見つかりません")
            continue
        
        for conllu_file in conllu_files:
            # 言語コードを抽出
            # 例: en_pud-ud-test.conllu -> en_pud
            # 例: af_afribooms-ud-test.conllu -> af
            filename_parts = conllu_file.stem.split("-")
            lang_part = filename_parts[0]  # en_pud や af_afribooms
            
            # 言語コードとサブセット名を分離
            lang_parts = lang_part.split("_")
            lang_code = lang_parts[0]  # en, af, ja など
            
            # PUDかどうかを判定
            is_pud = "pud" in lang_part.lower()
            
            # 出力ファイル名の決定
            # PUDの場合: en_pud.json、その他: af.json
            if is_pud:
                output_name = f"{lang_code}_pud"
                max_sentences = None  # PUDは制限なし
            else:
                output_name = lang_code
                max_sentences = max_sentences_non_pud  # 追加言語は制限あり
            
            language_name = get_language_name(lang_code)
            
            print(f"\n処理中: {language_name} ({conllu_file.name})")
            
            try:
                data = parse_conllu_file(str(conllu_file), language_name, max_sentences)
                
                if max_sentences and data["sentence_count"] >= max_sentences:
                    print(f"  ⚠ 最大{max_sentences}文に達したため、残りはスキップしました")
                
                output_file = processed_dir / f"{output_name}.json"
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
    
    return processed_count, total_sentences


def main():
    """メイン処理"""
    project_root = Path(__file__).resolve().parent.parent
    raw_dir = project_root / "data" / "raw"
    processed_dir = project_root / "data" / "processed"
    
    print("=" * 70)
    print("CoNLL-Uファイルの処理を開始します...")
    print("=" * 70)
    
    processed_count, total_sentences = process_conllu_files(
        raw_dir, processed_dir, max_sentences_non_pud=1000
    )
    
    print("\n" + "=" * 70)
    print(f"処理完了:")
    print(f"  - 処理した言語数: {processed_count}")
    print(f"  - 総文数: {total_sentences}")
    print(f"  - 出力ディレクトリ: {processed_dir}")
    print("=" * 70)


if __name__ == "__main__":
    main()
