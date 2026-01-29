#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
句へのマージ機能
依存関係を利用して、トークンを句単位でグループ化します。
"""

import json
import os
from collections import defaultdict

# 句の核となりうる品詞（主要語）
HEAD_POS = {'NOUN', 'VERB', 'ADJ', 'ADV', 'PROPN', 'PRON', 'NUM', 'DET', 'INTJ', 'X', 'SYM'}

# 句から除外する依存関係ラベル（これら以外は基本的にマージする）
# サブタイプ（:以降）は無視して判定します
EXCLUDE_DEPRELS = {
    'root',         # 根
    'punct',        # 句読点（分離してもしなくても良いが、分離が一般的）
    
    # --- 節・項構造の境界（これらは分離する） ---
    'nsubj', 'csubj',       # 主語
    'obj', 'iobj',          # 目的語
    'ccomp', 'xcomp',       # 補文
    'advcl',                # 副詞節
    'acl',                  # 名詞修飾節（関係代名詞など "which..." は長いので分離）
    
    'nmod',                 # 名詞修飾（前置詞句 "of X"）。日本語では「Xの」は独立した文節になるため分離推奨。
    'obl',                  # 斜格（前置詞句による動詞修飾 "on the table"）
    'conj',                 # 並列（A and B の B）
    
    # --- その他 ---
    'vocative', 'dislocated', 'orphan', 'reparandum'
}

def build_dependency_tree(tokens):
    """
    依存関係ツリーを構築
    
    Args:
        tokens: トークンのリスト
    
    Returns:
        dict: {parent_id: [child_ids]}
    """
    tree = defaultdict(list)
    
    for token in tokens:
        head = token.get('head', 0)
        token_id = token.get('id', 0)
        
        if head != 0:  # rootでない場合
            tree[head].append(token_id)
    
    return tree


def get_phrase_members(token_id, tokens, tree, included):
    """
    トークンを核とする句のメンバーを再帰的に取得
    
    Args:
        token_id: 核となるトークンのID
        tokens: 全トークンのリスト
        tree: 依存関係ツリー
        included: 既に句に含まれたトークンIDのセット
    
    Returns:
        list: 句に含まれるトークンIDのリスト
    """
    members = [token_id]
    included.add(token_id)
    
    # 子トークンをチェック
    for child_id in tree.get(token_id, []):
        if child_id in included:
            continue
            
        # トークンを取得
        child_token = next((t for t in tokens if t.get('id') == child_id), None)
        if not child_token:
            continue
        
        deprel = child_token.get('deprel', '')
        # サブタイプ（:以降）を除去してベースタグを取得
        deprel_base = deprel.split(':')[0] if deprel else ''
        
        # 句に含める条件をチェック
        # nmod:poss（所有格）は親にマージすべきなので例外扱い
        if deprel_base not in EXCLUDE_DEPRELS or deprel == 'nmod:poss':
            # 再帰的に子トークンの句メンバーも取得
            child_members = get_phrase_members(child_id, tokens, tree, included)
            members.extend(child_members)
    
    return members


def merge_to_phrases(sentence):
    """
    文を句単位にマージ
    
    Args:
        sentence: 文のデータ（tokensを含む）
    
    Returns:
        list: 句のリスト
    """
    tokens = sentence.get('tokens', [])
    if not tokens:
        return []
    
    # 依存関係ツリーを構築
    tree = build_dependency_tree(tokens)
    
    phrases = []
    included = set()
    
    # 句作成のヘルパー関数
    def create_phrase(token_id, upos, token):
        # 依存関係に基づいてメンバー候補を取得（再帰的）
        temp_included = included.copy()
        members = get_phrase_members(token_id, tokens, tree, temp_included)
        
        # メンバートークンをIDでソート
        members.sort()
        
        # 連結性チェック: メンバーが連続しているか確認
        # Headを含む最大の連続領域を特定する
        
        # Headのインデックスを探す
        try:
            head_idx = members.index(token_id)
        except ValueError:
            head_idx = 0
        
        # 左側に連続している範囲を探索
        start_idx = head_idx
        while start_idx > 0:
            if members[start_idx] - members[start_idx - 1] == 1:
                start_idx -= 1
            else:
                break
        
        # 右側に連続している範囲を探索
        end_idx = head_idx
        while end_idx < len(members) - 1:
            if members[end_idx + 1] - members[end_idx] == 1:
                end_idx += 1
            else:
                break
        
        # 連続領域のみを正式なメンバーとして採用
        final_members = members[start_idx : end_idx + 1]
        
        # 採用されたメンバーを included に追加
        for m_id in final_members:
            included.add(m_id)
        
        # 句を構築
        phrase_tokens = [t for t in tokens if t.get('id') in final_members]
        phrase_tokens.sort(key=lambda t: t.get('id', 0))
        
        return {
            'head_id': token_id,
            'head_form': token.get('form', ''),
            'head_upos': upos,
            'head_deprel': token.get('deprel', ''),
            'tokens': phrase_tokens,
            'forms': [t.get('form', '') for t in phrase_tokens],
            'upos_tags': [t.get('upos', '') for t in phrase_tokens],
            'deprel_tags': [t.get('deprel', '') for t in phrase_tokens],
            'text': ' '.join([t.get('form', '') for t in phrase_tokens])
        }

    # パス1: 独立した主要語（root, nsubj, objなど）を中心に句を作成
    # これにより、compoundなどの従属要素が先に独立して句になるのを防ぐ
    for token in tokens:
        token_id = token.get('id', 0)
        if token_id in included:
            continue
        
        upos = token.get('upos', '')
        deprel = token.get('deprel', '')
        deprel_base = deprel.split(':')[0] if deprel else ''
        
        # 独立性の判定: EXCLUDE_DEPRELSに含まれるか、rootである場合
        # ただしnmod:poss（所有格）は独立させず親にマージされるべき
        is_independent = ((deprel_base in EXCLUDE_DEPRELS) and deprel != 'nmod:poss') or (token.get('head') == 0)
        
        if upos in HEAD_POS and is_independent:
            phrase = create_phrase(token_id, upos, token)
            phrases.append(phrase)
            
    # パス2: 残りのトークンを処理
    # パス1で取り込まれなかった従属要素（連結性チェックで弾かれたものなど）や、
    # そもそも独立していなかったが親に取り込まれなかったものを句にする
    for token in tokens:
        token_id = token.get('id', 0)
        if token_id in included:
            continue
            
        upos = token.get('upos', '')
        
        if upos in HEAD_POS:
            phrase = create_phrase(token_id, upos, token)
            phrases.append(phrase)
        else:
            # 主要語でない場合は単独の句として扱う
            included.add(token_id)
            phrase = {
                'head_id': token_id,
                'head_form': token.get('form', ''),
                'head_upos': upos,
                'head_deprel': token.get('deprel', ''),
                'tokens': [token],
                'forms': [token.get('form', '')],
                'upos_tags': [upos],
                'deprel_tags': [token.get('deprel', '')],
                'text': token.get('form', '')
            }
            phrases.append(phrase)
    
    # 句をID順（出現順）にソート
    phrases.sort(key=lambda p: p['tokens'][0]['id'] if p['tokens'] else 0)
    
    return phrases


def process_language_file(input_path, output_path):
    """
    言語ファイルを処理して句データを生成
    
    Args:
        input_path: 入力JSONファイルのパス
        output_path: 出力JSONファイルのパス
    """
    print(f"処理中: {input_path}")
    
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    language = data.get('language', 'Unknown')
    sentences = data.get('sentences', [])
    
    # 各文を句に変換
    phrase_sentences = []
    total_phrases = 0
    
    for sent in sentences:
        phrases = merge_to_phrases(sent)
        
        phrase_sent = {
            'sent_id': sent.get('sent_id', ''),
            'text': sent.get('text', ''),
            'original_tokens': sent.get('tokens', []),
            'phrases': phrases,
            'phrase_count': len(phrases),
            'token_count': len(sent.get('tokens', []))
        }
        
        phrase_sentences.append(phrase_sent)
        total_phrases += len(phrases)
    
    # 出力データを構築
    output_data = {
        'language': language,
        'sentence_count': len(phrase_sentences),
        'total_phrases': total_phrases,
        'total_tokens': sum(s['token_count'] for s in phrase_sentences),
        'sentences': phrase_sentences
    }
    
    # ファイルに保存
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    
    print(f"  → {len(phrase_sentences)}文、{total_phrases}句を生成")
    print(f"  → 保存先: {output_path}")


def main():
    """メイン処理"""
    # ディレクトリパス
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    processed_dir = os.path.join(project_root, 'data', 'processed')
    phrases_dir = os.path.join(project_root, 'data', 'phrases')
    
    # 出力ディレクトリを作成
    os.makedirs(phrases_dir, exist_ok=True)
    
    print("=" * 60)
    print("句へのマージ処理を開始します")
    print("=" * 60)
    
    # processedディレクトリ内の全JSONファイルを処理
    processed_files = sorted([f for f in os.listdir(processed_dir) if f.endswith('.json')])
    
    if not processed_files:
        print("警告: 処理対象のファイルが見つかりません")
        return
    
    for filename in processed_files:
        input_file = os.path.join(processed_dir, filename)
        
        # 出力ファイル名を決定（例: en_pud.json -> en_pud_phrases.json）
        base_name = os.path.splitext(filename)[0]
        output_file = os.path.join(phrases_dir, f'{base_name}_phrases.json')
        
        process_language_file(input_file, output_file)
    
    print("=" * 60)
    print("処理完了!")
    print("=" * 60)


if __name__ == '__main__':
    main()
