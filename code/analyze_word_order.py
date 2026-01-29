#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
語順分析スクリプト

レーベンシュタイン距離とn-gramを用いて言語間の語順を比較・分析する。
- レーベンシュタイン距離: 各文のUPOS/DEPREL列の編集距離を計算
- n-gram: 各言語で頻出する品詞パターンを抽出
- 可視化: MDS/t-SNEによる散布図、デンドログラム
"""

from pathlib import Path

# ローカルモジュールからインポート
from data_loader import (
    load_sentences_upos,
    load_sentences_deprel,
    load_sentences_phrase_heads,
)
from word_order import (
    calculate_pairwise_levenshtein,
    analyze_ngrams_all_languages,
    save_ngram_results,
    find_most_similar_pairs,
)
from visualization import (
    plot_heatmap,
    plot_dendrogram,
    plot_mds,
    plot_tsne,
    save_distance_matrix_csv,
)


def analyze_levenshtein(
    lang_sentences,
    results_dir: Path,
    viz_dir: Path,
    tag_type: str,
    title_label: str
):
    """
    レーベンシュタイン距離分析を実行
    
    Args:
        lang_sentences: 言語ごとの文データ
        results_dir: 結果保存ディレクトリ
        viz_dir: 可視化保存ディレクトリ
        tag_type: タグ種類（upos, deprel, phrase_head）
        title_label: タイトル用ラベル
    """
    print(f"\n{'=' * 80}")
    print(f"【{title_label}でのレーベンシュタイン距離分析】")
    print("=" * 80)
    
    print("\n言語間距離の計算...")
    distance_matrix, languages = calculate_pairwise_levenshtein(lang_sentences)
    
    # CSV保存
    save_distance_matrix_csv(
        distance_matrix,
        languages,
        results_dir / f"{tag_type}_levenshtein_distance.csv"
    )
    
    # 最も類似している言語ペア
    print(f"\n最も類似している言語ペア Top 10（{title_label}）:")
    top_pairs = find_most_similar_pairs(distance_matrix, languages)
    for i, (lang1, lang2, dist) in enumerate(top_pairs, 1):
        similarity = 1 - dist
        print(f"  {i:2d}. {lang1:15s} - {lang2:15s}: 距離={dist:.4f} (類似度={similarity:.4f})")
    
    # 可視化
    print("\n可視化...")
    plot_heatmap(
        distance_matrix, languages,
        f"Language Distance based on {title_label} Sequence\n(Normalized Levenshtein Distance)",
        viz_dir / f"{tag_type}_levenshtein_heatmap.png",
        fmt='.3f'
    )
    
    plot_dendrogram(
        distance_matrix, languages,
        f"Hierarchical Clustering of Languages\n({title_label} Levenshtein Distance)",
        viz_dir / f"{tag_type}_levenshtein_dendrogram.png"
    )
    
    plot_mds(
        distance_matrix, languages,
        f"MDS Visualization of Language Distances\n({title_label} Levenshtein)",
        viz_dir / f"{tag_type}_levenshtein_mds.png"
    )
    
    if len(languages) > 5:
        plot_tsne(
            distance_matrix, languages,
            f"t-SNE Visualization of Language Distances\n({title_label} Levenshtein)",
            viz_dir / f"{tag_type}_levenshtein_tsne.png"
        )


def main():
    """メイン処理"""
    print("=" * 80)
    print("語順分析（レーベンシュタイン距離 + n-gram）")
    print("=" * 80)
    
    # パスの設定
    project_root = Path(__file__).resolve().parent.parent
    processed_dir = project_root / "data" / "processed"
    phrases_dir = project_root / "data" / "phrases"
    results_dir = project_root / "data" / "results"
    viz_dir = results_dir / "visualizations"
    
    # ディレクトリ作成
    viz_dir.mkdir(parents=True, exist_ok=True)
    
    # データ読み込み
    print("\n1. データ読み込み中...")
    upos_sentences = load_sentences_upos(processed_dir)
    deprel_sentences = load_sentences_deprel(processed_dir)
    phrase_head_sentences = load_sentences_phrase_heads(phrases_dir)
    
    print(f"  言語数: {len(upos_sentences)}")
    print(f"  言語: {', '.join(sorted(upos_sentences.keys()))}")
    
    # UPOS列での分析
    analyze_levenshtein(upos_sentences, results_dir, viz_dir, "upos", "UPOS")
    
    # DEPREL列での分析
    analyze_levenshtein(deprel_sentences, results_dir, viz_dir, "deprel", "DEPREL")
    
    # Phrase Head UPOS列での分析
    if phrase_head_sentences:
        analyze_levenshtein(phrase_head_sentences, results_dir, viz_dir, "phrase_head", "Phrase Head UPOS")
    
    # n-gram分析
    print(f"\n{'=' * 80}")
    print("【n-gram分析】")
    print("=" * 80)
    
    print("\nUPOS n-gram分析...")
    upos_ngram_results = analyze_ngrams_all_languages(upos_sentences)
    save_ngram_results(upos_ngram_results, results_dir, tag_type="upos")
    
    print("\n各言語のトップ3 bi-gram（UPOS）:")
    for lang in sorted(upos_ngram_results.keys()):
        top3 = upos_ngram_results[lang][2][:3]
        patterns = [f"{'-'.join(p)}({c})" for p, c in top3]
        print(f"  {lang:15s}: {', '.join(patterns)}")
    
    print("\nDEPREL n-gram分析...")
    deprel_ngram_results = analyze_ngrams_all_languages(deprel_sentences)
    save_ngram_results(deprel_ngram_results, results_dir, tag_type="deprel")
    
    if phrase_head_sentences:
        print("\nPhrase Head n-gram分析...")
        phrase_head_ngram_results = analyze_ngrams_all_languages(phrase_head_sentences)
        save_ngram_results(phrase_head_ngram_results, results_dir, tag_type="phrase_head")
    
    # 完了
    print("\n" + "=" * 80)
    print("分析完了!")
    print(f"結果保存先: {results_dir}")
    print(f"可視化保存先: {viz_dir}")
    print("=" * 80)


if __name__ == "__main__":
    main()
