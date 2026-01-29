# Grammatical Similarity Research

Universal Dependencies (UD) コーパスを用いた多言語間の文法的類似性分析プロジェクト。

## 概要

33言語のCoNLL-Uデータから品詞(UPOS)・依存関係(DEPREL)・Head Directionを抽出し、言語間の文法的距離を測定する。

## セットアップ

```bash
pip install -r requirements.txt
```

## 使い方

```bash
# データ準備
python3 code/extract_zips.py
python3 code/parse_conllu.py
python3 code/merge_to_phrases.py

# 分析実行
python3 code/calculate_head_direction.py
python3 code/analyze_word_order.py
```

結果は `data/results/` に出力される。

## Web UI

```bash
cd frontend
npm install
npm run dev
```

デプロイ: https://matsuri9.github.io/dsF2025/

## ファイル構成

```
code/
├── utils.py                 # CoNLL-Uパーサ
├── data_loader.py           # データ読み込み
├── head_direction.py        # Head Direction分析
├── word_order.py            # 語順分析
├── visualization.py         # 可視化
├── parse_conllu.py          # CoNLL-U→JSON変換
├── calculate_head_direction.py
├── analyze_word_order.py
├── merge_to_phrases.py
└── extract_zips.py

data/
├── raw/        # 生データ (.gitignore)
├── processed/  # JSON
├── phrases/    # 句単位データ
└── results/    # 分析結果
```

## 対象言語

**PUD (20言語):** ar, zh, cs, en, fi, fr, gl, de, hi, is, id, it, ja, ko, pt, ru, es, sv, th, tr

**追加 (13言語):** af, fo, he, ga, kpv, yrk, no, sa, tl, ta, uz, vi, sah
