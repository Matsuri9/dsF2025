#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Head Direction分析スクリプト

Universal Dependencies (UD) の係り受け構造を用い、言語ごとに
「統語的な親（Head）と子（Dependent）の相対的な位置関係」を
統計的にスコア化し、特徴ベクトルとして比較する。

【手法の概要】
1. UDコーパス内の全データに対し、Head-Dependentペアを抽出
2. 各ペアについて、HeadがDependentより「前にある」か「後ろにある」かを判定
3. 各文法関係パターンについて、Head-Initial率（0.0～1.0）を算出
4. 言語間のベクトル類似度（コサイン類似度・ユークリッド距離）を計算

【参考文献】
- Dryer, Matthew S. (2013). "Order of Subject, Object and Verb." 
  In: World Atlas of Language Structures Online.
- Universal Dependencies Guidelines: https://universaldependencies.org/
"""

from pathlib import Path

# ローカルモジュールからインポート
from data_loader import load_all_languages
from head_direction import (
    create_feature_vectors,
    calculate_distance_matrix_cosine,
    calculate_distance_matrix_euclidean,
    save_head_initial_rates_csv,
    find_most_similar_pairs,
)
from visualization import (
    plot_heatmap,
    plot_dendrogram,
    plot_mds,
    save_distance_matrix_csv,
)


def run_analysis(
    all_data,
    results_dir: Path,
    viz_dir: Path,
    use_merged: bool,
    label: str
):
    """
    Head Direction分析を実行
    
    Args:
        all_data: 全言語データ
        results_dir: 結果保存ディレクトリ
        viz_dir: 可視化保存ディレクトリ
        use_merged: マージモードを使用するか
        label: ラベル（'raw' or 'merged'）
    """
    print(f"\n{'=' * 80}")
    print(f"【{label.upper()}版】{'（マージ後のカテゴリを使用）' if use_merged else '（元のUPOS/DEPRELを使用）'}")
    print("=" * 80)
    
    print("\n特徴ベクトル作成中...")
    feature_matrix, languages, pairs = create_feature_vectors(
        all_data,
        use_merged=use_merged,
        min_occurrences=50,
        min_languages=max(1, len(all_data) // 2)
    )
    
    if len(pairs) == 0:
        print(f"  警告: {label}版で共通ペアが見つかりませんでした。")
        return
    
    # Head-Initial率CSV保存
    print("\nHead-Initial率CSV保存中...")
    save_head_initial_rates_csv(
        all_data,
        results_dir / f"head_direction_rates_{label}.csv",
        use_merged=use_merged,
        min_occurrences=50
    )
    
    # 距離行列計算
    print("\n距離行列計算中...")
    
    # コサイン距離
    distance_cosine = calculate_distance_matrix_cosine(feature_matrix)
    save_distance_matrix_csv(
        distance_cosine, languages,
        results_dir / f"head_direction_distance_cosine_{label}.csv"
    )
    
    # ユークリッド距離
    distance_euclidean = calculate_distance_matrix_euclidean(feature_matrix)
    save_distance_matrix_csv(
        distance_euclidean, languages,
        results_dir / f"head_direction_distance_euclidean_{label}.csv"
    )
    
    # 最も類似している言語ペア
    print(f"\n最も類似している言語ペア Top 10 (コサイン距離, {label}版):")
    top_pairs = find_most_similar_pairs(distance_cosine, languages)
    for i, (lang1, lang2, dist) in enumerate(top_pairs, 1):
        print(f"  {i:2d}. {lang1:15s} - {lang2:15s}: 距離={dist:.4f}")
    
    # 可視化
    print("\n可視化中...")
    plot_heatmap(
        distance_cosine, languages,
        f"Head Direction Distance (Cosine, {label.capitalize()})\nHead-Initial率に基づく言語間距離",
        viz_dir / f"head_direction_heatmap_cosine_{label}.png"
    )
    plot_dendrogram(
        distance_cosine, languages,
        f"Hierarchical Clustering (Head Direction, {label.capitalize()})",
        viz_dir / f"head_direction_dendrogram_{label}.png"
    )
    plot_mds(
        distance_cosine, languages,
        f"MDS Visualization (Head Direction, {label.capitalize()})",
        viz_dir / f"head_direction_mds_{label}.png"
    )


def main():
    """メイン処理"""
    print("=" * 80)
    print("Head Direction分析")
    print("（係り受けの方向性に基づく言語間距離の算出）")
    print("=" * 80)
    
    # パスの設定
    project_root = Path(__file__).resolve().parent.parent
    processed_dir = project_root / "data" / "processed"
    results_dir = project_root / "data" / "results"
    viz_dir = results_dir / "visualizations"
    
    # ディレクトリ作成
    viz_dir.mkdir(parents=True, exist_ok=True)
    
    # データ読み込み
    print("\n1. データ読み込み中...")
    all_data = load_all_languages(processed_dir)
    print(f"  読み込んだ言語: {', '.join(sorted(all_data.keys()))}")
    
    # Raw版（マージなし）の分析
    run_analysis(all_data, results_dir, viz_dir, use_merged=False, label="raw")
    
    # Merged版（マージあり）の分析
    run_analysis(all_data, results_dir, viz_dir, use_merged=True, label="merged")
    
    # 完了
    print("\n" + "=" * 80)
    print("分析完了!")
    print(f"  結果保存先: {results_dir}")
    print(f"  可視化保存先: {viz_dir}")
    print("=" * 80)


if __name__ == "__main__":
    main()
