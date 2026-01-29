"""
Zipファイルの展開スクリプト
data/zip/ 内の全てのzipファイルを data/raw/ に展開する
"""

import os
import zipfile
from pathlib import Path


def extract_all_zips():
    """全てのzipファイルを展開する"""
    
    # パスの設定
    project_root = Path(__file__).resolve().parent.parent
    zip_dir = project_root / "data" / "zip"
    raw_dir = project_root / "data" / "raw"
    
    # raw ディレクトリが存在することを確認
    raw_dir.mkdir(parents=True, exist_ok=True)
    
    # zip ファイルのリストを取得 (Zone.Identifier を除外)
    zip_files = [f for f in zip_dir.glob("*.zip") if not f.name.endswith(".zip:Zone.Identifier")]
    
    print(f"見つかったzipファイル数: {len(zip_files)}")
    print("-" * 60)
    
    # 各zipファイルを展開
    extracted_count = 0
    for zip_path in sorted(zip_files):
        print(f"展開中: {zip_path.name}")
        
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                # 展開先ディレクトリ名を取得
                extract_to = raw_dir
                
                # 展開
                zip_ref.extractall(extract_to)
                extracted_count += 1
                print(f"  ✓ 完了: {zip_path.name}")
                
        except Exception as e:
            print(f"  ✗ エラー: {zip_path.name} - {e}")
    
    print("-" * 60)
    print(f"展開完了: {extracted_count}/{len(zip_files)} ファイル")
    
    # 展開後のディレクトリを確認
    print("\n展開されたディレクトリ:")
    for item in sorted(raw_dir.iterdir()):
        if item.is_dir():
            print(f"  - {item.name}")


if __name__ == "__main__":
    extract_all_zips()
