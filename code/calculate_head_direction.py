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

【本手法の利点】
- 文全体を単純比較するのではなく、文法的な役割ごとに分解して語順を評価
- 文の長さや構造の複雑さに依存しない堅牢なスコアが得られる
- SVO/SOVといった大局的な語順と、修飾語の位置といった局所的な語順を
  独立した特徴量として扱える

【参考文献】
- Dryer, Matthew S. (2013). "Order of Subject, Object and Verb." 
  In: World Atlas of Language Structures Online. Leipzig: Max Planck Institute.
- Universal Dependencies Guidelines: https://universaldependencies.org/
"""

import json
import csv
import numpy as np
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Tuple, Optional, Set

import matplotlib
matplotlib.use('Agg')  # GUIなしで使用
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.cluster.hierarchy import dendrogram, linkage
from scipy.spatial.distance import squareform, cosine, pdist
from sklearn.manifold import MDS
from sklearn.metrics.pairwise import cosine_similarity

# ローカルモジュールからインポート
from utils import merge_upos, merge_deprel


# ============================================================
# 型エイリアス
# ============================================================
# Head-Dependentペアを表すタプル
# (HeadのUPOS, DependentのUPOS, DEPREL)
PairKey = Tuple[str, str, str]

# 言語ごとのHead-Initial率
# {言語名: {ペアキー: (head_initial_count, total_count)}}
LanguagePairCounts = Dict[str, Dict[PairKey, Tuple[int, int]]]


# ============================================================
# データ読み込み
# ============================================================

def load_all_languages(processed_dir: Path) -> Dict[str, List[Dict]]:
    """
    全言語のパース済みデータを読み込む
    
    Args:
        processed_dir: パース済みJSONファイルが格納されたディレクトリ
    
    Returns:
        {言語名: [文データ, ...]} の辞書
        各文データには 'tokens' キーがあり、トークンのリストを含む
    
    Example:
        >>> data = load_all_languages(Path('data/processed'))
        >>> print(data.keys())
        dict_keys(['Arabic', 'Chinese', 'Czech', ...])
    """
    data = {}
    
    for json_file in sorted(processed_dir.glob("*.json")):
        with open(json_file, 'r', encoding='utf-8') as f:
            file_data = json.load(f)
        
        language = file_data["language"]
        data[language] = file_data["sentences"]
        
    return data


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
    
    【処理の流れ】
    1. 各文の全トークンについてループ
    2. トークンのHead（係り先）を特定
    3. (HeadのUPOS, DepのUPOS, DEPREL) のタプルをキーとして集計
    4. HeadのIDがDepのIDより小さい場合、head_initial_count を増加
    
    【Head-Initial率の解釈】
    - 1.0 に近い: Head が Dependent より前に来る（例: 英語の動詞-目的語）
    - 0.0 に近い: Head が Dependent より後に来る（例: 日本語の動詞-目的語）
    - 0.5 付近: 順序が一定しない、または言語内で変動がある
    """
    # ペアごとのカウント
    # キー: (HeadUPOS, DepUPOS, DEPREL)
    # 値: [head_initial_count, total_count]
    pair_counts: Dict[PairKey, List[int]] = defaultdict(lambda: [0, 0])
    
    for sentence in sentences:
        tokens = sentence.get("tokens", [])
        
        # トークンIDからトークンへのマッピングを作成
        # （HeadのIDでHeadトークンを検索するため）
        token_map = {token["id"]: token for token in tokens}
        
        for token in tokens:
            # Headの取得（0はROOTを示す）
            head_id = token.get("head", 0)
            
            # ROOTは係り受け分析から除外
            if head_id == 0:
                continue
            
            # Headトークンの取得
            head_token = token_map.get(head_id)
            if head_token is None:
                continue
            
            # UPOSとDEPRELの取得
            dep_upos = token.get("upos", "")
            head_upos = head_token.get("upos", "")
            deprel = token.get("deprel", "")
            
            # 無効なタグはスキップ
            if not dep_upos or not head_upos or not deprel:
                continue
            
            # 句読点を除外（オプション）
            if exclude_punct and (dep_upos == "PUNCT" or head_upos == "PUNCT"):
                continue
            
            # DEPRELからサブタイプを除去（例: nsubj:pass -> nsubj）
            base_deprel = deprel.split(':')[0]
            
            # マージが有効な場合、カテゴリを変換
            if use_merged:
                head_upos = merge_upos(head_upos)
                dep_upos = merge_upos(dep_upos)
                base_deprel = merge_deprel(deprel)
            
            # ペアキーの作成
            pair_key = (head_upos, dep_upos, base_deprel)
            
            # カウントの更新
            pair_counts[pair_key][1] += 1  # 総出現回数
            
            # Head-Initialの判定:
            # HeadのIDがDependentのIDより小さい = Headが前にある
            if head_token["id"] < token["id"]:
                pair_counts[pair_key][0] += 1  # head_initial_count
    
    # リストをタプルに変換して返す
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
    
    【計算式】
    head_initial_rate = head_initial_count / total_count
    
    total_count が 0 の場合は 0.5（中立）を返す
    """
    rates = {}
    
    for pair_key, (head_initial, total) in pair_counts.items():
        if total > 0:
            rates[pair_key] = head_initial / total
        else:
            # データがない場合は中立値
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
                      （Noneの場合は全言語で出現するペアのみ）
    
    Returns:
        (特徴行列, 言語リスト, ペアキーリスト)
        
        - 特徴行列: shape = (言語数, ペア数) の numpy配列
        - 言語リスト: 行に対応する言語名のリスト
        - ペアキーリスト: 列に対応するペアキーのリスト
    
    【処理の流れ】
    1. 各言語でHead-Dependentペアを抽出
    2. 全言語で共通に出現するペアを特定
    3. 各言語・各ペアのHead-Initial率を計算
    4. 特徴行列として整形
    """
    languages = sorted(all_language_data.keys())
    n_languages = len(languages)
    
    if min_languages is None:
        min_languages = n_languages
    
    print(f"  言語数: {n_languages}")
    print(f"  マージモード: {'有効' if use_merged else '無効'}")
    
    # ステップ1: 各言語のペアカウントを取得
    print("  ステップ1: ペア抽出中...")
    language_pair_counts: Dict[str, Dict[PairKey, Tuple[int, int]]] = {}
    
    for lang in languages:
        pair_counts = extract_head_dependent_pairs(
            all_language_data[lang],
            use_merged=use_merged
        )
        language_pair_counts[lang] = pair_counts
    
    # ステップ2: 十分な出現回数を持つペアを各言語で特定
    print("  ステップ2: 共通ペアの特定中...")
    
    # 各ペアが出現する言語数をカウント
    pair_language_count: Dict[PairKey, int] = defaultdict(int)
    
    for lang in languages:
        for pair_key, (_, total) in language_pair_counts[lang].items():
            if total >= min_occurrences:
                pair_language_count[pair_key] += 1
    
    # min_languages 以上の言語で出現するペアのみ使用
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
            # そのペアが存在しない場合は0.5（中立）
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
    
    【コサイン距離について】
    コサイン距離 = 1 - コサイン類似度
    
    コサイン類似度は、2つのベクトルの方向の類似性を測定する。
    スケールに依存しないため、各ペアの絶対的な頻度ではなく、
    言語全体でのパターンの類似性を評価する。
    """
    # sklearn の cosine_similarity は類似度を返すので、1から引いて距離に変換
    similarity = cosine_similarity(feature_matrix)
    distance = 1 - similarity
    
    # 数値誤差による負の値や対角成分の補正
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
    
    【ユークリッド距離について】
    ユークリッド距離は、多次元空間での2点間の直線距離。
    各ペアのHead-Initial率の絶対的な差を測定する。
    
    【正規化について】
    ペア数によって距離のスケールが変わるため、
    最大距離（全次元が0と1の差）で正規化する。
    """
    n_features = feature_matrix.shape[1]
    
    # scipy.spatial.distance.pdist を使用して効率的に計算
    # condensed distance matrix を返す
    condensed = pdist(feature_matrix, metric='euclidean')
    
    # squareform で正方行列に変換
    distance = squareform(condensed)
    
    # 正規化: 最大可能距離 = sqrt(n_features) （全次元が0と1の差の場合）
    max_possible_distance = np.sqrt(n_features)
    if max_possible_distance > 0:
        distance = distance / max_possible_distance
    
    return distance


# ============================================================
# 可視化
# ============================================================

def plot_heatmap(
    matrix: np.ndarray,
    languages: List[str],
    title: str,
    output_path: Path,
    cmap: str = 'YlOrRd'
):
    """
    距離行列のヒートマップを作成
    
    Args:
        matrix: 距離行列
        languages: 言語名リスト
        title: グラフタイトル
        output_path: 出力ファイルパス
        cmap: カラーマップ
    """
    plt.figure(figsize=(14, 12))
    
    ax = sns.heatmap(
        matrix,
        xticklabels=languages,
        yticklabels=languages,
        cmap=cmap,
        annot=True,
        fmt='.2f',
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
    
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"    ヒートマップ保存: {output_path.name}")


def plot_dendrogram(
    matrix: np.ndarray,
    languages: List[str],
    title: str,
    output_path: Path
):
    """
    距離行列から樹形図を作成
    
    Args:
        matrix: 距離行列
        languages: 言語名リスト
        title: グラフタイトル
        output_path: 出力ファイルパス
    """
    plt.figure(figsize=(12, 8))
    
    # 距離行列を凝縮形式に変換
    condensed = squareform(matrix)
    
    # 階層的クラスタリング（UPGMA法）
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
    
    print(f"    樹形図保存: {output_path.name}")


def plot_mds(
    matrix: np.ndarray,
    languages: List[str],
    title: str,
    output_path: Path
):
    """
    MDS（多次元尺度構成法）による2次元散布図を作成
    
    Args:
        matrix: 距離行列
        languages: 言語名リスト
        title: グラフタイトル
        output_path: 出力ファイルパス
    
    【MDSについて】
    高次元の距離関係を低次元（ここでは2次元）に射影する手法。
    元の距離関係をできるだけ保持しながら可視化できる。
    """
    plt.figure(figsize=(12, 10))
    
    # MDS による次元削減
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
    
    print(f"    MDS散布図保存: {output_path.name}")


# ============================================================
# 結果保存
# ============================================================

def save_head_initial_rates_csv(
    all_language_data: Dict[str, List[Dict]],
    output_path: Path,
    use_merged: bool = False,
    min_occurrences: int = 10
):
    """
    各言語のHead-Initial率をCSVとして保存
    
    Args:
        all_language_data: {言語名: 文リスト}
        output_path: 出力CSVファイルパス
        use_merged: マージ後のカテゴリを使用するかどうか
        min_occurrences: 最低出現回数
    
    出力CSVの形式:
    - 行: 各ペア (HeadUPOS, DepUPOS, DEPREL)
    - 列: 各言語
    - 値: Head-Initial率 (0.0 ~ 1.0)
    """
    languages = sorted(all_language_data.keys())
    
    # 各言語のペアカウントを取得
    language_rates: Dict[str, Dict[PairKey, float]] = {}
    all_pairs: Set[PairKey] = set()
    
    for lang in languages:
        pair_counts = extract_head_dependent_pairs(
            all_language_data[lang],
            use_merged=use_merged
        )
        # min_occurrences 以上のペアのみ保持
        filtered_counts = {
            k: v for k, v in pair_counts.items()
            if v[1] >= min_occurrences
        }
        rates = calculate_head_initial_rates(filtered_counts)
        language_rates[lang] = rates
        all_pairs.update(filtered_counts.keys())
    
    # ペアをソート
    sorted_pairs = sorted(all_pairs)
    
    # CSV書き込み
    with open(output_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        
        # ヘッダー
        header = ['HeadUPOS', 'DepUPOS', 'DEPREL'] + languages
        writer.writerow(header)
        
        # データ行
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


def save_distance_matrix_csv(
    matrix: np.ndarray,
    languages: List[str],
    output_path: Path
):
    """
    距離行列をCSVとして保存
    
    Args:
        matrix: 距離行列
        languages: 言語名リスト
        output_path: 出力CSVファイルパス
    """
    with open(output_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        
        # ヘッダー
        writer.writerow([''] + languages)
        
        # データ行
        for i, lang in enumerate(languages):
            row = [lang] + [f'{x:.4f}' for x in matrix[i]]
            writer.writerow(row)
    
    print(f"  距離行列CSV保存: {output_path.name}")


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


# ============================================================
# メイン処理
# ============================================================

def main():
    """
    メイン処理
    
    【実行フロー】
    1. データ読み込み
    2. Raw版（マージなし）の分析
    3. Merged版（マージあり）の分析
    4. 結果の比較サマリー
    """
    print("=" * 80)
    print("Head Direction分析")
    print("（係り受けの方向性に基づく言語間距離の算出）")
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
    all_data = load_all_languages(processed_dir)
    print(f"  読み込んだ言語: {', '.join(sorted(all_data.keys()))}")
    
    # ============================================================
    # 2. Raw版（マージなし）の分析
    # ============================================================
    print("\n" + "=" * 80)
    print("【Raw版】（元のUPOS/DEPRELを使用）")
    print("=" * 80)
    
    print("\n2a. 特徴ベクトル作成中...")
    feature_matrix_raw, languages, pairs_raw = create_feature_vectors(
        all_data,
        use_merged=False,
        min_occurrences=50,  # ノイズ削減のため閾値を高めに設定
        min_languages=max(1, len(all_data) // 2)  # 半数以上の言語で共通するペアのみ
    )
    
    if len(pairs_raw) > 0:
        print(f"\n2b. Head-Initial率CSV保存中...")
        save_head_initial_rates_csv(
            all_data,
            results_dir / "head_direction_rates_raw.csv",
            use_merged=False,
            min_occurrences=50
        )
        
        print("\n2c. 距離行列計算中...")
        
        # コサイン距離
        distance_cosine_raw = calculate_distance_matrix_cosine(feature_matrix_raw)
        save_distance_matrix_csv(
            distance_cosine_raw, languages,
            results_dir / "head_direction_distance_cosine_raw.csv"
        )
        
        # ユークリッド距離
        distance_euclidean_raw = calculate_distance_matrix_euclidean(feature_matrix_raw)
        save_distance_matrix_csv(
            distance_euclidean_raw, languages,
            results_dir / "head_direction_distance_euclidean_raw.csv"
        )
        
        # 最も類似している言語ペア
        print("\n  最も類似している言語ペア Top 10 (コサイン距離, Raw版):")
        top_pairs = find_most_similar_pairs(distance_cosine_raw, languages)
        for i, (lang1, lang2, dist) in enumerate(top_pairs, 1):
            print(f"    {i:2d}. {lang1:15s} - {lang2:15s}: 距離={dist:.4f}")
        
        # 可視化
        print("\n2d. 可視化中...")
        plot_heatmap(
            distance_cosine_raw, languages,
            "Head Direction Distance (Cosine, Raw)\nHead-Initial率に基づく言語間距離",
            viz_dir / "head_direction_heatmap_cosine_raw.png"
        )
        plot_dendrogram(
            distance_cosine_raw, languages,
            "Hierarchical Clustering (Head Direction, Raw)",
            viz_dir / "head_direction_dendrogram_raw.png"
        )
        plot_mds(
            distance_cosine_raw, languages,
            "MDS Visualization (Head Direction, Raw)",
            viz_dir / "head_direction_mds_raw.png"
        )
    else:
        print("  警告: Raw版で共通ペアが見つかりませんでした。")
    
    # ============================================================
    # 3. Merged版（マージあり）の分析
    # ============================================================
    print("\n" + "=" * 80)
    print("【Merged版】（マージ後のカテゴリを使用）")
    print("=" * 80)
    
    print("\n3a. 特徴ベクトル作成中...")
    feature_matrix_merged, languages, pairs_merged = create_feature_vectors(
        all_data,
        use_merged=True,
        min_occurrences=50,
        min_languages=max(1, len(all_data) // 2)  # 半数以上の言語で共通するペアのみ
    )
    
    if len(pairs_merged) > 0:
        print(f"\n3b. Head-Initial率CSV保存中...")
        save_head_initial_rates_csv(
            all_data,
            results_dir / "head_direction_rates_merged.csv",
            use_merged=True,
            min_occurrences=50
        )
        
        print("\n3c. 距離行列計算中...")
        
        # コサイン距離
        distance_cosine_merged = calculate_distance_matrix_cosine(feature_matrix_merged)
        save_distance_matrix_csv(
            distance_cosine_merged, languages,
            results_dir / "head_direction_distance_cosine_merged.csv"
        )
        
        # ユークリッド距離
        distance_euclidean_merged = calculate_distance_matrix_euclidean(feature_matrix_merged)
        save_distance_matrix_csv(
            distance_euclidean_merged, languages,
            results_dir / "head_direction_distance_euclidean_merged.csv"
        )
        
        # 最も類似している言語ペア
        print("\n  最も類似している言語ペア Top 10 (コサイン距離, Merged版):")
        top_pairs = find_most_similar_pairs(distance_cosine_merged, languages)
        for i, (lang1, lang2, dist) in enumerate(top_pairs, 1):
            print(f"    {i:2d}. {lang1:15s} - {lang2:15s}: 距離={dist:.4f}")
        
        # 可視化
        print("\n3d. 可視化中...")
        plot_heatmap(
            distance_cosine_merged, languages,
            "Head Direction Distance (Cosine, Merged)\nHead-Initial率に基づく言語間距離（マージ版）",
            viz_dir / "head_direction_heatmap_cosine_merged.png"
        )
        plot_dendrogram(
            distance_cosine_merged, languages,
            "Hierarchical Clustering (Head Direction, Merged)",
            viz_dir / "head_direction_dendrogram_merged.png"
        )
        plot_mds(
            distance_cosine_merged, languages,
            "MDS Visualization (Head Direction, Merged)",
            viz_dir / "head_direction_mds_merged.png"
        )
    else:
        print("  警告: Merged版で共通ペアが見つかりませんでした。")
    
    # ============================================================
    # 4. 完了
    # ============================================================
    print("\n" + "=" * 80)
    print("分析完了!")
    print(f"  結果保存先: {results_dir}")
    print(f"  可視化保存先: {viz_dir}")
    print("=" * 80)


if __name__ == "__main__":
    main()
