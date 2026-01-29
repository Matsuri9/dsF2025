#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
可視化モジュール

言語間距離の可視化機能を提供します。
- ヒートマップ
- 樹形図（デンドログラム）
- MDS散布図
- t-SNE散布図
- 距離行列のCSV出力
"""

import csv
import numpy as np
from pathlib import Path
from typing import List

import matplotlib
matplotlib.use('Agg')  # GUIなしで使用
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.cluster.hierarchy import dendrogram, linkage
from scipy.spatial.distance import squareform
from sklearn.manifold import MDS, TSNE


# ============================================================
# ヒートマップ
# ============================================================

def plot_heatmap(
    matrix: np.ndarray,
    languages: List[str],
    title: str,
    output_path: Path,
    cmap: str = 'YlOrRd',
    fmt: str = '.2f'
) -> None:
    """
    距離行列のヒートマップを作成
    
    Args:
        matrix: 距離行列
        languages: 言語名リスト
        title: グラフタイトル
        output_path: 出力ファイルパス
        cmap: カラーマップ
        fmt: 数値フォーマット
    """
    plt.figure(figsize=(14, 12))
    
    ax = sns.heatmap(
        matrix,
        xticklabels=languages,
        yticklabels=languages,
        cmap=cmap,
        annot=True,
        fmt=fmt,
        square=True,
        cbar_kws={'label': 'Distance'},
        linewidths=0.5
    )
    
    plt.title(title, fontsize=16, pad=20)
    plt.xlabel('Language', fontsize=12)
    plt.ylabel('Language', fontsize=12)
    plt.xticks(rotation=45, ha='right')
    plt.yticks(rotation=0)
    plt.tight_layout()
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"  ヒートマップ保存: {output_path.name}")


# ============================================================
# 樹形図（デンドログラム）
# ============================================================

def plot_dendrogram(
    matrix: np.ndarray,
    languages: List[str],
    title: str,
    output_path: Path,
    method: str = 'average',
    color_threshold_ratio: float = 0.7
) -> None:
    """
    距離行列から樹形図を作成
    
    Args:
        matrix: 距離行列
        languages: 言語名リスト
        title: グラフタイトル
        output_path: 出力ファイルパス
        method: クラスタリング手法（'average', 'ward', 'complete', 'single'）
        color_threshold_ratio: 色分けの閾値（最大距離に対する比率）
    """
    plt.figure(figsize=(12, 8))
    
    # 距離行列を凝縮形式に変換
    condensed = squareform(matrix)
    
    # 階層的クラスタリング
    linkage_matrix = linkage(condensed, method=method)
    
    # 樹形図描画
    dendrogram(
        linkage_matrix,
        labels=languages,
        leaf_font_size=10,
        color_threshold=color_threshold_ratio * max(linkage_matrix[:, 2])
    )
    
    plt.title(title, fontsize=16, pad=20)
    plt.xlabel('Language', fontsize=12)
    plt.ylabel('Distance', fontsize=12)
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"  樹形図保存: {output_path.name}")


# ============================================================
# MDS散布図
# ============================================================

def plot_mds(
    matrix: np.ndarray,
    languages: List[str],
    title: str,
    output_path: Path,
    point_size: int = 100,
    point_color: str = 'steelblue'
) -> None:
    """
    MDS（多次元尺度構成法）による2次元散布図を作成
    
    Args:
        matrix: 距離行列
        languages: 言語名リスト
        title: グラフタイトル
        output_path: 出力ファイルパス
        point_size: ポイントのサイズ
        point_color: ポイントの色
    
    【MDSについて】
    高次元の距離関係を低次元（ここでは2次元）に射影する手法。
    元の距離関係をできるだけ保持しながら可視化できる。
    """
    plt.figure(figsize=(12, 10))
    
    # MDS による次元削減
    mds = MDS(n_components=2, dissimilarity='precomputed', random_state=42, normalized_stress='auto')
    coords = mds.fit_transform(matrix)
    
    # プロット
    plt.scatter(coords[:, 0], coords[:, 1], s=point_size, alpha=0.7, c=point_color)
    
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
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"  MDS散布図保存: {output_path.name}")


# ============================================================
# t-SNE散布図
# ============================================================

def plot_tsne(
    matrix: np.ndarray,
    languages: List[str],
    title: str,
    output_path: Path,
    perplexity: int = None,
    point_size: int = 100
) -> None:
    """
    t-SNEによる2次元散布図を作成
    
    Args:
        matrix: 距離行列
        languages: 言語名リスト
        title: グラフタイトル
        output_path: 出力ファイルパス
        perplexity: t-SNEのperplexityパラメータ（Noneなら自動設定）
        point_size: ポイントのサイズ
    """
    plt.figure(figsize=(12, 10))
    
    # perplexityは言語数より小さくする必要がある
    if perplexity is None:
        perplexity = min(5, len(languages) - 1)
    
    tsne = TSNE(
        n_components=2, 
        perplexity=perplexity, 
        random_state=42, 
        metric='precomputed', 
        init='random'
    )
    coords = tsne.fit_transform(matrix)
    
    # プロット
    plt.scatter(coords[:, 0], coords[:, 1], s=point_size, alpha=0.7)
    
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
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"  t-SNE散布図保存: {output_path.name}")


# ============================================================
# CSV出力
# ============================================================

def save_distance_matrix_csv(
    matrix: np.ndarray,
    languages: List[str],
    output_path: Path,
    precision: int = 4
) -> None:
    """
    距離行列をCSVとして保存
    
    Args:
        matrix: 距離行列
        languages: 言語名リスト
        output_path: 出力CSVファイルパス
        precision: 小数点以下の桁数
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        
        # ヘッダー
        writer.writerow([''] + languages)
        
        # データ行
        for i, lang in enumerate(languages):
            row = [lang] + [f'{x:.{precision}f}' for x in matrix[i]]
            writer.writerow(row)
    
    print(f"  距離行列CSV保存: {output_path.name}")


# ============================================================
# 一括可視化
# ============================================================

def visualize_distance_matrix(
    matrix: np.ndarray,
    languages: List[str],
    output_dir: Path,
    name_prefix: str,
    title_suffix: str = "",
    include_tsne: bool = False
) -> None:
    """
    距離行列の一括可視化を実行
    
    ヒートマップ、樹形図、MDS散布図を生成します。
    
    Args:
        matrix: 距離行列
        languages: 言語名リスト
        output_dir: 出力ディレクトリ
        name_prefix: ファイル名のプレフィックス
        title_suffix: タイトルのサフィックス
        include_tsne: t-SNE散布図も生成するか
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # ヒートマップ
    plot_heatmap(
        matrix, languages,
        f"Language Distance Heatmap{title_suffix}",
        output_dir / f"{name_prefix}_heatmap.png"
    )
    
    # 樹形図
    plot_dendrogram(
        matrix, languages,
        f"Hierarchical Clustering{title_suffix}",
        output_dir / f"{name_prefix}_dendrogram.png"
    )
    
    # MDS散布図
    plot_mds(
        matrix, languages,
        f"MDS Visualization{title_suffix}",
        output_dir / f"{name_prefix}_mds.png"
    )
    
    # t-SNE散布図（オプション）
    if include_tsne and len(languages) > 5:
        plot_tsne(
            matrix, languages,
            f"t-SNE Visualization{title_suffix}",
            output_dir / f"{name_prefix}_tsne.png"
        )
    
    # CSV
    save_distance_matrix_csv(
        matrix, languages,
        output_dir / f"{name_prefix}_distance.csv"
    )
