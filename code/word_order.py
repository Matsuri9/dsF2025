#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
語順分析モジュール

レーベンシュタイン距離とn-gramを用いた言語間語順比較機能を提供します。
"""

import csv
import numpy as np
from pathlib import Path
from collections import Counter
from typing import Dict, List, Tuple


# ============================================================
# レーベンシュタイン距離
# ============================================================

def levenshtein_distance(seq1: List[str], seq2: List[str]) -> int:
    """
    2つのシーケンス間のレーベンシュタイン距離を計算
    
    Args:
        seq1: 文字列のリスト（例: ['DET', 'NOUN', 'VERB']）
        seq2: 文字列のリスト
    
    Returns:
        編集距離（挿入・削除・置換の最小回数）
    """
    m, n = len(seq1), len(seq2)
    
    # DPテーブル
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    
    for i in range(m + 1):
        dp[i][0] = i
    for j in range(n + 1):
        dp[0][j] = j
    
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if seq1[i - 1] == seq2[j - 1]:
                dp[i][j] = dp[i - 1][j - 1]
            else:
                dp[i][j] = 1 + min(
                    dp[i - 1][j],      # 削除
                    dp[i][j - 1],      # 挿入
                    dp[i - 1][j - 1]   # 置換
                )
    
    return dp[m][n]


def normalized_levenshtein(seq1: List[str], seq2: List[str]) -> float:
    """
    正規化レーベンシュタイン距離（0-1の範囲）
    
    Returns:
        0 = 完全一致, 1 = 完全に異なる
    """
    if len(seq1) == 0 and len(seq2) == 0:
        return 0.0
    
    distance = levenshtein_distance(seq1, seq2)
    max_len = max(len(seq1), len(seq2))
    
    return distance / max_len


# ============================================================
# n-gram分析
# ============================================================

def extract_ngrams(sequence: List[str], n: int) -> List[Tuple[str, ...]]:
    """
    シーケンスからn-gramを抽出
    
    Args:
        sequence: 文字列のリスト
        n: n-gramのn
    
    Returns:
        n-gramのリスト（タプルのリスト）
    """
    if len(sequence) < n:
        return []
    
    return [tuple(sequence[i:i+n]) for i in range(len(sequence) - n + 1)]


def count_ngrams(sentences: List[List[str]], n: int) -> Counter:
    """
    複数文からn-gramをカウント
    
    Args:
        sentences: 文のリスト（各文はUPOSタグのリスト）
        n: n-gramのn
    
    Returns:
        n-gramの出現回数カウンター
    """
    counter = Counter()
    
    for sentence in sentences:
        ngrams = extract_ngrams(sentence, n)
        counter.update(ngrams)
    
    return counter


def analyze_ngrams_all_languages(
    lang_sentences: Dict[str, List[List[str]]],
    n_values: List[int] = [2, 3],
    top_k: int = 20
) -> Dict[str, Dict[int, List[Tuple]]]:
    """
    全言語のn-gram分析を実行
    
    Args:
        lang_sentences: {言語名: [文のリスト]}
        n_values: 分析するn-gramのサイズ
        top_k: 上位何件を保持するか
    
    Returns:
        {language: {n: [(ngram, count), ...]}}
    """
    results = {}
    
    for language, sentences in lang_sentences.items():
        results[language] = {}
        
        for n in n_values:
            counter = count_ngrams(sentences, n)
            top_ngrams = counter.most_common(top_k)
            results[language][n] = top_ngrams
    
    return results


def save_ngram_results(
    ngram_results: Dict[str, Dict[int, List[Tuple]]],
    output_dir: Path,
    tag_type: str = "upos"
) -> None:
    """
    n-gram分析結果をCSVとして保存
    
    Args:
        ngram_results: n-gram分析結果
        output_dir: 出力ディレクトリ
        tag_type: タグ種類（upos, deprel, phrase_head）
    """
    for n in [2, 3]:
        output_file = output_dir / f"{tag_type}_ngram_{n}gram_top20.csv"
        
        with open(output_file, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            
            header = ['Rank']
            languages = sorted(ngram_results.keys())
            for lang in languages:
                header.extend([f'{lang}_pattern', f'{lang}_count'])
            writer.writerow(header)
            
            for rank in range(20):
                row = [rank + 1]
                for lang in languages:
                    ngrams = ngram_results[lang].get(n, [])
                    if rank < len(ngrams):
                        pattern, count = ngrams[rank]
                        pattern_str = '-'.join(pattern)
                        row.extend([pattern_str, count])
                    else:
                        row.extend(['', ''])
                writer.writerow(row)
        
        print(f"  n-gram結果保存: {output_file.name}")


# ============================================================
# 言語間距離計算
# ============================================================

def calculate_pairwise_levenshtein(
    lang_sentences: Dict[str, List[List[str]]],
    sample_size: int = None
) -> Tuple[np.ndarray, List[str]]:
    """
    言語ペア間の平均レーベンシュタイン距離を計算
    
    PUDは同一内容のパラレルコーパスなので、同じインデックスの文同士を比較する。
    
    Args:
        lang_sentences: {language: [[tag1, tag2, ...], ...]}
        sample_size: サンプリングする文数（Noneなら全文）
    
    Returns:
        (距離行列, 言語リスト)
    """
    languages = sorted(lang_sentences.keys())
    n_langs = len(languages)
    
    # 最小の文数を取得
    min_sentences = min(len(lang_sentences[lang]) for lang in languages)
    
    if sample_size:
        min_sentences = min(min_sentences, sample_size)
    
    print(f"  比較する文数: {min_sentences}")
    
    distance_matrix = np.zeros((n_langs, n_langs))
    
    for i, lang1 in enumerate(languages):
        for j, lang2 in enumerate(languages):
            if i >= j:
                continue
            
            total_distance = 0.0
            
            for sent_idx in range(min_sentences):
                seq1 = lang_sentences[lang1][sent_idx]
                seq2 = lang_sentences[lang2][sent_idx]
                
                dist = normalized_levenshtein(seq1, seq2)
                total_distance += dist
            
            avg_distance = total_distance / min_sentences
            distance_matrix[i, j] = avg_distance
            distance_matrix[j, i] = avg_distance  # 対称
    
    return distance_matrix, languages


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
        [(言語1, 言語2, 距離), ...]（距離昇順）
    """
    pairs = []
    n = len(languages)
    
    for i in range(n):
        for j in range(i + 1, n):
            pairs.append((languages[i], languages[j], matrix[i, j]))
    
    pairs.sort(key=lambda x: x[2])
    
    return pairs[:top_n]
