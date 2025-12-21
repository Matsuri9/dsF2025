#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
語順分析スクリプト

レーベンシュタイン距離とn-gramを用いて言語間の語順を比較・分析する。
- レーベンシュタイン距離: 各文のUPOS/DEPREL列の編集距離を計算
- n-gram: 各言語で頻出する品詞パターンを抽出
- 可視化: MDS/t-SNEによる散布図、デンドログラム
"""

import json
import csv
import numpy as np
from pathlib import Path
from collections import Counter, defaultdict
from typing import Dict, List, Tuple
from itertools import combinations

import matplotlib
matplotlib.use('Agg')  # GUIなしで使用
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.cluster.hierarchy import dendrogram, linkage
from scipy.spatial.distance import squareform
from sklearn.manifold import MDS, TSNE


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
    
    # 初期化
    for i in range(m + 1):
        dp[i][0] = i
    for j in range(n + 1):
        dp[0][j] = j
    
    # DP
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


# ============================================================
# データ読み込み
# ============================================================

def load_sentences_upos(processed_dir: Path) -> Dict[str, List[List[str]]]:
    """
    各言語の文をUPOS列として読み込む
    
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
    
    Returns:
        {language: [[head_upos1, head_upos2, ...], ...]}
    """
    data = {}
    
    for json_file in sorted(phrases_dir.glob("*_pud_phrases.json")):
        with open(json_file, 'r', encoding='utf-8') as f:
            file_data = json.load(f)
        
        language = file_data["language"]
        sentences = []
        
        for sent in file_data["sentences"]:
            head_upos_seq = []
            for phrase in sent.get("phrases", []):
                head_upos = phrase.get("head_upos")
                if head_upos:
                    head_upos_seq.append(head_upos)
            if head_upos_seq:
                sentences.append(head_upos_seq)
        
        data[language] = sentences
    
    return data


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
    
    # 最小の文数を取得（パラレルコーパスなので同じはずだが念のため）
    min_sentences = min(len(lang_sentences[lang]) for lang in languages)
    
    if sample_size:
        min_sentences = min(min_sentences, sample_size)
    
    print(f"  比較する文数: {min_sentences}")
    
    # 距離行列
    distance_matrix = np.zeros((n_langs, n_langs))
    
    for i, lang1 in enumerate(languages):
        for j, lang2 in enumerate(languages):
            if i >= j:  # 対角線と下三角はスキップ（後で対称にコピー）
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


# ============================================================
# 可視化
# ============================================================

def plot_distance_heatmap(
    matrix: np.ndarray,
    languages: List[str],
    title: str,
    output_path: Path
):
    """距離行列のヒートマップを作成"""
    plt.figure(figsize=(14, 12))
    
    ax = sns.heatmap(
        matrix,
        xticklabels=languages,
        yticklabels=languages,
        cmap='YlOrRd',  # 小さい=黄色（類似）、大きい=赤（非類似）
        annot=True,
        fmt='.3f',
        square=True,
        cbar_kws={'label': 'Normalized Levenshtein Distance'},
        linewidths=0.5
    )
    
    plt.title(title, fontsize=16, pad=20)
    plt.xlabel('Language', fontsize=12)
    plt.ylabel('Language', fontsize=12)
    plt.xticks(rotation=45, ha='right')
    plt.yticks(rotation=0)
    plt.tight_layout()
    
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"  ヒートマップ保存: {output_path.name}")


def plot_dendrogram_from_distance(
    matrix: np.ndarray,
    languages: List[str],
    title: str,
    output_path: Path
):
    """距離行列から樹形図を作成"""
    plt.figure(figsize=(12, 8))
    
    # 距離行列を凝縮形式に変換
    condensed = squareform(matrix)
    
    # 階層的クラスタリング
    linkage_matrix = linkage(condensed, method='average')
    
    # 樹形図描画
    dendrogram(
        linkage_matrix,
        labels=languages,
        leaf_font_size=10,
        color_threshold=0.7 * max(linkage_matrix[:, 2])
    )
    
    plt.title(title, fontsize=16, pad=20)
    plt.xlabel('Language', fontsize=12)
    plt.ylabel('Distance', fontsize=12)
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"  樹形図保存: {output_path.name}")


def plot_mds_scatter(
    matrix: np.ndarray,
    languages: List[str],
    title: str,
    output_path: Path
):
    """MDSによる2次元散布図を作成"""
    plt.figure(figsize=(12, 10))
    
    # MDS (sklearn)
    mds = MDS(n_components=2, dissimilarity='precomputed', random_state=42, normalized_stress='auto')
    coords = mds.fit_transform(matrix)
    
    # プロット
    plt.scatter(coords[:, 0], coords[:, 1], s=100, alpha=0.7)
    
    # ラベル
    for i, lang in enumerate(languages):
        plt.annotate(
            lang,
            (coords[i, 0], coords[i, 1]),
            xytext=(5, 5),
            textcoords='offset points',
            fontsize=10
        )
    
    plt.title(title, fontsize=16, pad=20)
    plt.xlabel('MDS Dimension 1', fontsize=12)
    plt.ylabel('MDS Dimension 2', fontsize=12)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"  MDS散布図保存: {output_path.name}")


def plot_tsne_scatter(
    matrix: np.ndarray,
    languages: List[str],
    title: str,
    output_path: Path
):
    """t-SNEによる2次元散布図を作成"""
    plt.figure(figsize=(12, 10))
    
    # t-SNE（距離行列から特徴ベクトルとして使用）
    # perplexityは言語数より小さくする必要がある
    perplexity = min(5, len(languages) - 1)
    
    tsne = TSNE(n_components=2, perplexity=perplexity, random_state=42, metric='precomputed', init='random')
    coords = tsne.fit_transform(matrix)
    
    # プロット
    plt.scatter(coords[:, 0], coords[:, 1], s=100, alpha=0.7)
    
    # ラベル
    for i, lang in enumerate(languages):
        plt.annotate(
            lang,
            (coords[i, 0], coords[i, 1]),
            xytext=(5, 5),
            textcoords='offset points',
            fontsize=10
        )
    
    plt.title(title, fontsize=16, pad=20)
    plt.xlabel('t-SNE Dimension 1', fontsize=12)
    plt.ylabel('t-SNE Dimension 2', fontsize=12)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"  t-SNE散布図保存: {output_path.name}")


# ============================================================
# n-gram分析と出力
# ============================================================

def analyze_ngrams_all_languages(
    lang_sentences: Dict[str, List[List[str]]],
    n_values: List[int] = [2, 3],
    top_k: int = 20
) -> Dict[str, Dict[int, List[Tuple]]]:
    """
    全言語のn-gram分析を実行
    
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
):
    """n-gram分析結果をCSVとして保存"""
    
    for n in [2, 3]:
        output_file = output_dir / f"{tag_type}_ngram_{n}gram_top20.csv"
        
        with open(output_file, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            
            # ヘッダー
            header = ['Rank']
            languages = sorted(ngram_results.keys())
            for lang in languages:
                header.extend([f'{lang}_pattern', f'{lang}_count'])
            writer.writerow(header)
            
            # データ行
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
            writer.writerow([lang] + [f'{x:.4f}' for x in matrix[i]])
    
    print(f"  距離行列CSV保存: {output_path.name}")


def find_most_similar_pairs(
    matrix: np.ndarray,
    languages: List[str],
    top_n: int = 10
) -> List[Tuple[str, str, float]]:
    """最も類似している（距離が小さい）言語ペアを抽出"""
    pairs = []
    n = len(languages)
    
    for i in range(n):
        for j in range(i + 1, n):
            pairs.append((languages[i], languages[j], matrix[i, j]))
    
    pairs.sort(key=lambda x: x[2])  # 距離が小さい順
    
    return pairs[:top_n]


# ============================================================
# メイン処理
# ============================================================

def main():
    """メイン処理"""
    print("=" * 80)
    print("語順分析（レーベンシュタイン距離 + n-gram）")
    print("=" * 80)
    
    # パスの設定
    project_root = Path(__file__).parent.parent
    processed_dir = project_root / "data" / "processed"
    results_dir = project_root / "data" / "results"
    viz_dir = results_dir / "visualizations"
    
    # ディレクトリ作成
    viz_dir.mkdir(parents=True, exist_ok=True)
    
    # ============================================================
    # 1. データ読み込み
    # ============================================================
    print("\n1. データ読み込み中...")
    upos_sentences = load_sentences_upos(processed_dir)
    deprel_sentences = load_sentences_deprel(processed_dir)
    
    # Phraseデータ
    phrases_dir = project_root / "data" / "phrases"
    phrase_head_sentences = load_sentences_phrase_heads(phrases_dir)
    
    print(f"  言語数: {len(upos_sentences)}")
    print(f"  言語: {', '.join(sorted(upos_sentences.keys()))}")
    
    # ============================================================
    # 2. UPOS列でのレーベンシュタイン距離分析
    # ============================================================
    print("\n" + "=" * 80)
    print("【UPOS列でのレーベンシュタイン距離分析】")
    print("=" * 80)
    
    print("\n2a. 言語間距離の計算...")
    upos_distance_matrix, languages = calculate_pairwise_levenshtein(upos_sentences)
    
    # CSV保存
    save_distance_matrix_csv(
        upos_distance_matrix,
        languages,
        results_dir / "upos_levenshtein_distance.csv"
    )
    
    # 最も類似している言語ペア
    print("\n  最も類似している言語ペア Top 10（UPOS）:")
    top_pairs = find_most_similar_pairs(upos_distance_matrix, languages)
    for i, (lang1, lang2, dist) in enumerate(top_pairs, 1):
        similarity = 1 - dist
        print(f"    {i:2d}. {lang1:15s} - {lang2:15s}: 距離={dist:.4f} (類似度={similarity:.4f})")
    
    # 可視化
    print("\n2b. 可視化...")
    plot_distance_heatmap(
        upos_distance_matrix, languages,
        "Language Distance based on UPOS Sequence\n(Normalized Levenshtein Distance)",
        viz_dir / "upos_levenshtein_heatmap.png"
    )
    
    plot_dendrogram_from_distance(
        upos_distance_matrix, languages,
        "Hierarchical Clustering of Languages\n(UPOS Levenshtein Distance)",
        viz_dir / "upos_levenshtein_dendrogram.png"
    )
    
    plot_mds_scatter(
        upos_distance_matrix, languages,
        "MDS Visualization of Language Distances\n(UPOS Levenshtein)",
        viz_dir / "upos_levenshtein_mds.png"
    )
    
    plot_tsne_scatter(
        upos_distance_matrix, languages,
        "t-SNE Visualization of Language Distances\n(UPOS Levenshtein)",
        viz_dir / "upos_levenshtein_tsne.png"
    )
    
    # ============================================================
    # 3. DEPREL列でのレーベンシュタイン距離分析
    # ============================================================
    print("\n" + "=" * 80)
    print("【DEPREL列でのレーベンシュタイン距離分析】")
    print("=" * 80)
    
    print("\n3a. 言語間距離の計算...")
    deprel_distance_matrix, _ = calculate_pairwise_levenshtein(deprel_sentences)
    
    # CSV保存
    save_distance_matrix_csv(
        deprel_distance_matrix,
        languages,
        results_dir / "deprel_levenshtein_distance.csv"
    )
    
    # 最も類似している言語ペア
    print("\n  最も類似している言語ペア Top 10（DEPREL）:")
    top_pairs = find_most_similar_pairs(deprel_distance_matrix, languages)
    for i, (lang1, lang2, dist) in enumerate(top_pairs, 1):
        similarity = 1 - dist
        print(f"    {i:2d}. {lang1:15s} - {lang2:15s}: 距離={dist:.4f} (類似度={similarity:.4f})")
    
    # 可視化
    print("\n3b. 可視化...")
    plot_distance_heatmap(
        deprel_distance_matrix, languages,
        "Language Distance based on DEPREL Sequence\n(Normalized Levenshtein Distance)",
        viz_dir / "deprel_levenshtein_heatmap.png"
    )
    
    plot_dendrogram_from_distance(
        deprel_distance_matrix, languages,
        "Hierarchical Clustering of Languages\n(DEPREL Levenshtein Distance)",
        viz_dir / "deprel_levenshtein_dendrogram.png"
    )
    
    plot_mds_scatter(
        deprel_distance_matrix, languages,
        "MDS Visualization of Language Distances\n(DEPREL Levenshtein)",
        viz_dir / "deprel_levenshtein_mds.png"
    )
    
    # ============================================================
    # 4. n-gram分析
    # ============================================================
    print("\n" + "=" * 80)
    print("【n-gram分析】")
    print("=" * 80)
    
    print("\n4a. UPOS n-gram分析...")
    upos_ngram_results = analyze_ngrams_all_languages(upos_sentences, n_values=[2, 3], top_k=20)
    save_ngram_results(upos_ngram_results, results_dir, tag_type="upos")
    
    # 各言語のトップ3 bi-gramを表示
    print("\n  各言語のトップ3 bi-gram（UPOS）:")
    for lang in sorted(upos_ngram_results.keys()):
        top3 = upos_ngram_results[lang][2][:3]
        patterns = [f"{'-'.join(p)}({c})" for p, c in top3]
        print(f"    {lang:15s}: {', '.join(patterns)}")
    
    print("\n4b. DEPREL n-gram分析...")
    deprel_ngram_results = analyze_ngrams_all_languages(deprel_sentences, n_values=[2, 3], top_k=20)
    save_ngram_results(deprel_ngram_results, results_dir, tag_type="deprel")
    
    # ============================================================
    # 5. Phrase（句の主辞UPOS列）でのレーベンシュタイン距離分析
    # ============================================================
    print("\n" + "=" * 80)
    print("【Phrase Head UPOS列でのレーベンシュタイン距離分析】")
    print("=" * 80)
    
    print("\n5a. 言語間距離の計算...")
    phrase_head_distance_matrix, _ = calculate_pairwise_levenshtein(phrase_head_sentences)
    
    # CSV保存
    save_distance_matrix_csv(
        phrase_head_distance_matrix,
        languages,
        results_dir / "phrase_head_levenshtein_distance.csv"
    )
    
    # 最も類似している言語ペア
    print("\n  最も類似している言語ペア Top 10（Phrase Head）:")
    top_pairs = find_most_similar_pairs(phrase_head_distance_matrix, languages)
    for i, (lang1, lang2, dist) in enumerate(top_pairs, 1):
        similarity = 1 - dist
        print(f"    {i:2d}. {lang1:15s} - {lang2:15s}: 距離={dist:.4f} (類似度={similarity:.4f})")
    
    # 可視化
    print("\n5b. 可視化...")
    plot_distance_heatmap(
        phrase_head_distance_matrix, languages,
        "Language Distance based on Phrase Head UPOS Sequence\n(Normalized Levenshtein Distance)",
        viz_dir / "phrase_head_levenshtein_heatmap.png"
    )
    
    plot_dendrogram_from_distance(
        phrase_head_distance_matrix, languages,
        "Hierarchical Clustering of Languages\n(Phrase Head Levenshtein Distance)",
        viz_dir / "phrase_head_levenshtein_dendrogram.png"
    )
    
    plot_mds_scatter(
        phrase_head_distance_matrix, languages,
        "MDS Visualization of Language Distances\n(Phrase Head Levenshtein)",
        viz_dir / "phrase_head_levenshtein_mds.png"
    )
    
    # ============================================================
    # 6. Phrase Head n-gram分析
    # ============================================================
    print("\n" + "=" * 80)
    print("【Phrase Head n-gram分析】")
    print("=" * 80)
    
    print("\n6a. Phrase Head n-gram分析...")
    phrase_head_ngram_results = analyze_ngrams_all_languages(phrase_head_sentences, n_values=[2, 3], top_k=20)
    save_ngram_results(phrase_head_ngram_results, results_dir, tag_type="phrase_head")
    
    # 各言語のトップ3 bi-gramを表示
    print("\n  各言語のトップ3 bi-gram（Phrase Head）:")
    for lang in sorted(phrase_head_ngram_results.keys()):
        top3 = phrase_head_ngram_results[lang][2][:3]
        patterns = [f"{'-'.join(p)}({c})" for p, c in top3]
        print(f"    {lang:15s}: {', '.join(patterns)}")

    # ============================================================
    # 完了
    # ============================================================
    print("\n" + "=" * 80)
    print("分析完了!")
    print(f"結果保存先: {results_dir}")
    print(f"可視化保存先: {viz_dir}")
    print("=" * 80)


if __name__ == "__main__":
    main()
