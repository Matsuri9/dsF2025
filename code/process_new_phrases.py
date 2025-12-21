"""
新しい言語のphraseファイルを生成するスクリプト
"""

import json
import sys
from pathlib import Path

# プロジェクトルートのcodeディレクトリをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "code"))

from utils import merge_upos, merge_deprel

# 新しい言語のコードリスト
NEW_LANGS = ['af', 'fo', 'he', 'ga', 'kpv', 'yrk', 'nn', 'sa', 'tl', 'ta', 'uz', 'vi', 'sah']

def process_new_language_phrases():
    """新しい言語のphraseファイルを生成"""
    
    processed_dir = project_root / 'data' / 'processed'
    phrases_dir = project_root / 'data' / 'phrases'
    phrases_dir.mkdir(parents=True, exist_ok=True)
    
    print("新言語のphrase生成を開始します...")
    print("=" * 60)
    
    for lang_code in NEW_LANGS:
        input_file = processed_dir / f'{lang_code}.json'
        if not input_file.exists():
            print(f'⚠ {lang_code}: ファイルが見つかりません')
            continue
        
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f'処理中: {lang_code} ({data["language"]})')
        
        # 全phraseを集計
        all_phrases = []
        for sentence in data['sentences']:
            for token in sentence['tokens']:
                if token['head'] != 0:
                    # headトークンを探す
                    head_token = next((t for t in sentence['tokens'] if t['id'] == token['head']), None)
                    if head_token:
                        all_phrases.append({
                            'head_id': str(token['head']),
                            'head_upos': merge_upos(head_token['upos']),
                            'dep_id': str(token['id']),
                            'dep_upos': merge_upos(token['upos']),
                            'deprel': merge_deprel(token['deprel'])
                        })
        
        output = {
            'language': data['language'],
            'total_phrases': len(all_phrases),
            'sentences': [{'sent_id': s['sent_id'], 'phrases': []} for s in data['sentences']]
        }
        
        output_file = phrases_dir / f'{lang_code}_phrases.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        
        print(f'  ✓ 完了: {len(all_phrases)}句 -> {output_file.name}')
    
    print("=" * 60)
    print("処理完了!")


if __name__ == "__main__":
    process_new_language_phrases()
