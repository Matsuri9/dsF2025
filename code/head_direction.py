#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Head Direction分析モジュール

Universal Dependencies (UD) の係り受け構造を用い、言語ごとに
「統語的な親（Head）と子（Dependent）の相対的な位置関係」を
統計的にスコア化し、特徴ベクトルとして比較する。

【手法の概要】
1. UDコーパス内の全データに対し、Head-Dependentペアを抽出
2. 各ペアについて、HeadがDependentより「前にある」か「後ろにある」かを判定
3. 各文法関係パターンについて、Head-Initial率（0.0～1.0）を算出
4. 言語間のベクトル類似度（コサイン類似度・ユークリッド距離）を計算
"""

import csv
import numpy as np
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Tuple, Set

from scipy.spatial.distance import squareform, pdist
from sklearn.metrics.pairwise import cosine_similarity

from utils import merge_upos, merge_deprel


# ============================================================
# 型エイリアス
# ============================================================
# Head-Dependentペアを表すタプル: (HeadのUPOS, DependentのUPOS, DEPREL)
PairKey = Tuple[str, str, str]

# 言語ごとのHead-Initial率: {言語名: {ペアキー: (head_initial_count, total_count)}}
LanguagePairCounts = Dict[str, Dict[PairKey, Tuple[int, int]]]


# ============================================================
# Head-Dependentペアの抽出とカウント
# ============================================================

def extract_head_dependent_pairs(
    sentences: List[Dict],
    use_merged: bool = False,
    exclude_punct: bool = True
) -> Dict[PairKey, Tuple[int, int]]:
    """
    文のリストから全てのHead-Dependentペアを抽出し、
    Head-Initial（Headが前にある）かどうかをカウントする
    
    Args:
        sentences: 文のリスト（各文は 'tokens' キーを持つ辞書）
        use_merged: True の場合、マージ後のカテゴリを使用
        exclude_punct: True の場合、PUNCTを除外
    
    Returns:
        {(HeadUPOS, DepUPOS, DEPREL): (head_initial_count, total_count)}
        
        - head_initial_count: HeadがDependentより前にある（ID < Dep ID）回数
        - total_count: 該当ペアの総出現回数
    
    【Head-Initial率の解釈】
    - 1.0 に近い: Head が Dependent より前に来る（例: 英語の動詞-目的語）
    - 0.0 に近い: Head が Dependent より後に来る（例: 日本語の動詞-目的語）
    - 0.5 付近: 順序が一定しない、または言語内で変動がある
    """
    pair_counts: Dict[PairKey, List[int]] = defaultdict(lambda: [0, 0])
    
    for sentence in sentences:
        tokens = sentence.get("tokens", [])
        token_map = {token["id"]: token for token in tokens}
        
        for token in tokens:
            head_id = token.get("head", 0)
            
            # ROOTは係り受け分析から除外
            if head_id == 0:
                continue
            
            head_token = token_map.get(head_id)
            if head_token is None:
                continue
            
            dep_upos = token.get("upos", "")
            head_upos = head_token.get("upos", "")
            deprel = token.get("deprel", "")
            
            if not dep_upos or not head_upos or not deprel:
                continue
            
            # 句読点を除外（オプション）
            if exclude_punct and (dep_upos == "PUNCT" or head_upos == "PUNCT"):
                continue
            
            # DEPRELからサブタイプを除去
            base_deprel = deprel.split(':')[0]
            
            # マージが有効な場合、カテゴリを変換
            if use_merged:
                head_upos = merge_upos(head_upos)
                dep_upos = merge_upos(dep_upos)
                base_deprel = merge_deprel(deprel)
            
            pair_key = (head_upos, dep_upos, base_deprel)
            
            pair_counts[pair_key][1] += 1  # 総出現回数
            
            # Head-Initialの判定
            if head_token["id"] < token["id"]:
                pair_counts[pair_key][0] += 1
    
    return {k: tuple(v) for k, v in pair_counts.items()}


def calculate_head_initial_rates(
    pair_counts: Dict[PairKey, Tuple[int, int]]
) -> Dict[PairKey, float]:
    """
    ペアごとのカウントからHead-Initial率を計算
    
    Args:
        pair_counts: {ペアキー: (head_initial_count, total_count)}
    
    Returns:
        {ペアキー: head_initial_rate (0.0 ~ 1.0)}
    
    total_count が 0 の場合は 0.5（中立）を返す
    """
    rates = {}
    
    for pair_key, (head_initial, total) in pair_counts.items():
        if total > 0:
            rates[pair_key] = head_initial / total
        else:
            rates[pair_key] = 0.5
    
    return rates


# ============================================================
# 言語特徴ベクトルの作成
# ============================================================

def create_feature_vectors(
    all_language_data: Dict[str, List[Dict]],
    use_merged: bool = False,
    min_occurrences: int = 10,
    min_languages: int = None
) -> Tuple[np.ndarray, List[str], List[PairKey]]:
    """
    全言語のHead-Initial率から特徴ベクトル行列を作成
    
    Args:
        all_language_data: {言語名: 文リスト}
        use_merged: マージ後のカテゴリを使用するかどうか
        min_occurrences: 各言語でこれ以上出現するペアのみ使用
        min_languages: 最低でもこの数の言語で出現するペアのみ使用
                      （Noneの場合は半数以上の言語で出現するペアのみ）
    
    Returns:
        (特徴行列, 言語リスト, ペアキーリスト)
        
        - 特徴行列: shape = (言語数, ペア数) の numpy配列
        - 言語リスト: 行に対応する言語名のリスト
        - ペアキーリスト: 列に対応するペアキーのリスト
    """
    languages = sorted(all_language_data.keys())
    n_languages = len(languages)
    
    if min_languages is None:
        min_languages = max(1, int(n_languages * 0.5))
    
    print(f"  言語数: {n_languages}")
    print(f"  マージモード: {'有効' if use_merged else '無効'}")
    print(f"  最低出現言語数: {min_languages}")
    
    # ステップ1: 各言語のペアカウントを取得
    print("  ステップ1: ペア抽出中...")
    language_pair_counts: Dict[str, Dict[PairKey, Tuple[int, int]]] = {}
    
    for lang in languages:
        pair_counts = extract_head_dependent_pairs(
            all_language_data[lang],
            use_merged=use_merged
        )
        language_pair_counts[lang] = pair_counts
    
    # ステップ2: 共通ペアの特定
    print("  ステップ2: 共通ペアの特定中...")
    
    pair_language_count: Dict[PairKey, int] = defaultdict(int)
    
    for lang in languages:
        for pair_key, (_, total) in language_pair_counts[lang].items():
            if total >= min_occurrences:
                pair_language_count[pair_key] += 1
    
    common_pairs = sorted([
        pair for pair, count in pair_language_count.items()
        if count >= min_languages
    ])
    
    print(f"  共通ペア数: {len(common_pairs)}")
    
    if len(common_pairs) == 0:
        print("  警告: 共通ペアがありません。min_occurrences または min_languages を下げてください。")
        return np.array([]), languages, []
    
    # ステップ3: 特徴行列の作成
    print("  ステップ3: 特徴行列の作成中...")
    
    feature_matrix = np.zeros((n_languages, len(common_pairs)))
    
    for i, lang in enumerate(languages):
        pair_counts = language_pair_counts[lang]
        rates = calculate_head_initial_rates(pair_counts)
        
        for j, pair_key in enumerate(common_pairs):
            feature_matrix[i, j] = rates.get(pair_key, 0.5)
    
    return feature_matrix, languages, common_pairs


# ============================================================
# 距離行列の計算
# ============================================================

def calculate_distance_matrix_cosine(feature_matrix: np.ndarray) -> np.ndarray:
    """
    コサイン距離に基づく言語間距離行列を計算
    
    Args:
        feature_matrix: 特徴行列 (言語数 x ペア数)
    
    Returns:
        距離行列 (言語数 x 言語数)、0-1の範囲
    """
    similarity = cosine_similarity(feature_matrix)
    distance = 1 - similarity
    
    distance = np.clip(distance, 0, None)
    np.fill_diagonal(distance, 0)
    
    return distance


def calculate_distance_matrix_euclidean(feature_matrix: np.ndarray) -> np.ndarray:
    """
    ユークリッド距離に基づく言語間距離行列を計算
    
    Args:
        feature_matrix: 特徴行列 (言語数 x ペア数)
    
    Returns:
        距離行列 (言語数 x 言語数)、正規化済み（0-1の範囲に近似）
    """
    n_features = feature_matrix.shape[1]
    
    condensed = pdist(feature_matrix, metric='euclidean')
    distance = squareform(condensed)
    
    # 正規化
    max_possible_distance = np.sqrt(n_features)
    if max_possible_distance > 0:
        distance = distance / max_possible_distance
    
    return distance


# ============================================================
# 結果保存
# ============================================================

def save_head_initial_rates_csv(
    all_language_data: Dict[str, List[Dict]],
    output_path: Path,
    use_merged: bool = False,
    min_occurrences: int = 10
) -> None:
    """
    各言語のHead-Initial率をCSVとして保存
    
    Args:
        all_language_data: {言語名: 文リスト}
        output_path: 出力CSVファイルパス
        use_merged: マージ後のカテゴリを使用するかどうか
        min_occurrences: 最低出現回数
    """
    languages = sorted(all_language_data.keys())
    
    language_rates: Dict[str, Dict[PairKey, float]] = {}
    all_pairs: Set[PairKey] = set()
    
    for lang in languages:
        pair_counts = extract_head_dependent_pairs(
            all_language_data[lang],
            use_merged=use_merged
        )
        filtered_counts = {
            k: v for k, v in pair_counts.items()
            if v[1] >= min_occurrences
        }
        rates = calculate_head_initial_rates(filtered_counts)
        language_rates[lang] = rates
        all_pairs.update(filtered_counts.keys())
    
    sorted_pairs = sorted(all_pairs)
    
    with open(output_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        
        header = ['HeadUPOS', 'DepUPOS', 'DEPREL'] + languages
        writer.writerow(header)
        
        for pair in sorted_pairs:
            row = list(pair)
            for lang in languages:
                rate = language_rates[lang].get(pair, '')
                if rate != '':
                    row.append(f'{rate:.4f}')
                else:
                    row.append('')
            writer.writerow(row)
    
    print(f"  Head-Initial率CSV保存: {output_path.name}")


def find_most_similar_pairs(
    matrix: np.ndarray,
    languages: List[str],
    top_n: int = 10
) -> List[Tuple[str, str, float]]:
    """
    最も類似している（距離が小さい）言語ペアを抽出
    
    Args:
        matrix: 距離行列
        languages: 言語名リスト
        top_n: 上位何件を返すか
    
    Returns:
        [(言語1, 言語2, 距離), ...] のリスト（距離昇順）
    """
    pairs = []
    n = len(languages)
    
    for i in range(n):
        for j in range(i + 1, n):
            pairs.append((languages[i], languages[j], matrix[i, j]))
    
    pairs.sort(key=lambda x: x[2])
    
    return pairs[:top_n]
