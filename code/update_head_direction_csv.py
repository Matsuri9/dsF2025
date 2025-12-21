#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Head Direction率のCSV生成スクリプト（可視化なし版）
新しい言語を含めてHead-Initial率と距離行列を計算
"""

import json
import csv
import numpy as np
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Tuple, Set
from sklearn.metrics.pairwise import cosine_similarity

# ローカルモジュールからインポート
from utils import merge_upos, merge_deprel

# 型エイリアス
PairKey = Tuple[str, str, str]


def load_all_languages(processed_dir: Path) -> Dict[str, List[Dict]]:
    """全言語のパース済みデータを読み込む"""
    data = {}
    
    for json_file in sorted(processed_dir.glob("*.json")):
        with open(json_file, 'r', encoding='utf-8') as f:
            file_data = json.load(f)
        
        language = file_data["language"]
        data[language] = file_data["sentences"]
        
    return data


def extract_head_dependent_pairs(
    sentences: List[Dict],
    use_merged: bool = False,
    exclude_punct: bool = True
) -> Dict[PairKey, Tuple[int, int]]:
    """Head-Dependentペアを抽出してカウント"""
    pair_counts: Dict[PairKey, List[int]] = defaultdict(lambda: [0, 0])
    
    for sentence in sentences:
        tokens = sentence.get("tokens", [])
        token_map = {token["id"]: token for token in tokens}
        
        for token in tokens:
            head_id = token.get("head", 0)
            
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
            
            if exclude_punct and (dep_upos == "PUNCT" or head_upos == "PUNCT"):
                continue
            
            base_deprel = deprel.split(':')[0]
            
            if use_merged:
                head_upos = merge_upos(head_upos)
                dep_upos = merge_upos(dep_upos)
                base_deprel = merge_deprel(deprel)
            
            pair_key = (head_upos, dep_upos, base_deprel)
            
            pair_counts[pair_key][1] += 1
            
            if head_token["id"] < token["id"]:
                pair_counts[pair_key][0] += 1
    
    return {k: tuple(v) for k, v in pair_counts.items()}


def calculate_head_initial_rates(
    pair_counts: Dict[PairKey, Tuple[int, int]]
) -> Dict[PairKey, float]:
    """Head-Initial率を計算"""
    rates = {}
    
    for pair_key, (head_initial, total) in pair_counts.items():
        if total > 0:
            rates[pair_key] = head_initial / total
        else:
            rates[pair_key] = 0.5
    
    return rates


def save_head_initial_rates_csv(
    all_language_data: Dict[str, List[Dict]],
    output_path: Path,
    use_merged: bool = False,
    min_occurrences: int = 10
):
    """Head-Initial率をCSVとして保存"""
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


def calculate_distance_matrix_cosine(feature_matrix: np.ndarray) -> np.ndarray:
    """コサイン距離に基づく言語間距離行列を計算"""
    similarity = cosine_similarity(feature_matrix)
    distance = 1 - similarity
    
    distance = np.clip(distance, 0, None)
    np.fill_diagonal(distance, 0)
    
    return distance


def save_distance_matrix_csv(
    matrix: np.ndarray,
    languages: List[str],
    output_path: Path
):
    """距離行列をCSVとして保存"""
    with open(output_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        
        writer.writerow([''] + languages)
        
        for i, lang in enumerate(languages):
            row = [lang] + [f'{x:.4f}' for x in matrix[i]]
            writer.writerow(row)
    
    print(f"  距離行列CSV保存: {output_path.name}")


def create_feature_vectors(
    all_language_data: Dict[str, List[Dict]],
    use_merged: bool = False,
    min_occurrences: int = 10,
    min_languages: int = None
) -> Tuple[np.ndarray, List[str], List[PairKey]]:
    """特徴ベクトル行列を作成"""
    languages = sorted(all_language_data.keys())
    n_languages = len(languages)
    
    if min_languages is None:
        min_languages = max(1, int(n_languages * 0.5))  # 半数以上の言語で出現
    
    print(f"  言語数: {n_languages}")
    print(f"  最低出現言語数: {min_languages}")
    
    language_pair_counts: Dict[str, Dict[PairKey, Tuple[int, int]]] = {}
    
    for lang in languages:
        pair_counts = extract_head_dependent_pairs(
            all_language_data[lang],
            use_merged=use_merged
        )
        language_pair_counts[lang] = pair_counts
    
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
        return np.array([]), languages, []
    
    feature_matrix = np.zeros((n_languages, len(common_pairs)))
    
    for i, lang in enumerate(languages):
        pair_counts = language_pair_counts[lang]
        rates = calculate_head_initial_rates(pair_counts)
        
        for j, pair_key in enumerate(common_pairs):
            feature_matrix[i, j] = rates.get(pair_key, 0.5)
    
    return feature_matrix, languages, common_pairs


def main():
    """メイン処理"""
    print("=" * 80)
    print("Head Direction率とCSV生成")
    print("=" * 80)
    
    project_root = Path(__file__).parent.parent
    processed_dir = project_root / "data" / "processed"
    results_dir = project_root / "data" / "results"
    
    results_dir.mkdir(parents=True, exist_ok=True)
    
    print("\n1. データ読み込み中...")
    all_data = load_all_languages(processed_dir)
    print(f"  読み込んだ言語数: {len(all_data)}")
    print(f"  言語: {', '.join(sorted(all_data.keys()))}")
    
    # Merged版のみ処理
    print("\n2. Merged版の処理...")
    
    print("\n2a. Head-Initial率CSV保存中...")
    save_head_initial_rates_csv(
        all_data,
        results_dir / "head_direction_rates_merged.csv",
        use_merged=True,
        min_occurrences=50
    )
    
    print("\n2b. 特徴ベクトル作成中...")
    feature_matrix, languages, pairs = create_feature_vectors(
        all_data,
        use_merged=True,
        min_occurrences=50,
        min_languages=None
    )
    
    if len(pairs) > 0:
        print("\n2c. 距離行列計算中...")
        distance_cosine = calculate_distance_matrix_cosine(feature_matrix)
        save_distance_matrix_csv(
            distance_cosine, languages,
            results_dir / "head_direction_distance_cosine_merged.csv"
        )
        
        print("\n完了！")
        print(f"  処理した言語数: {len(languages)}")
        print(f"  使用したペア数: {len(pairs)}")
    else:
        print("\n警告: 共通ペアが見つかりませんでした。")
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
