# 文法的類似性研究 (Grammatical Similarity Research)

Universal Dependencies (UD) の Parallel Universal Dependencies (PUD) コーパスを用いて、多言語間の文法的類似性を定量的に分析・可視化する研究プロジェクトです。

## 📌 プロジェクト概要

本プロジェクトでは、20の異なる言語における同一の1000文（パラレルコーパス）を対象に、品詞（UPOS）や依存関係（DEPREL）の分布を比較することで、言語間の「文法的な距離」を測定します。

### 主な目的
- 言語間の文法的類似度の定量化
- 言語系統樹と計算された類似度の比較・検証
- 構文パターンや句構造の共通性の発見

## 🚀 機能と特徴

- **データ処理パイプライン**: CoNLL-U形式の生データを扱いやすいJSON形式に変換・構造化
- **多角的な類似度分析**:
  - 4つのメトリクスを採用: Cosine Similarity, Jaccard Similarity, Jensen-Shannon Divergence, Euclidean Distance
  - UPOS（品詞）とDEPREL（依存関係）それぞれの観点から分析
- **可視化**:
  - 言語間類似度ヒートマップ
  - 階層的クラスタリングによる樹形図 (Dendrogram)
- **インタラクティブWeb UI**:
  - ブラウザ上で2言語を選択し、文単位でタグや構造を比較可能
  - 類似度スコアの確認

## 📂 プロジェクト構造

```
grammatical_similarity_research/
├── .github/workflows/            # GitHub Actions (デプロイ自動化)
├── code/
│   ├── extract_zips.py           # データ解凍
│   ├── parse_conllu.py           # CoNLL-U → JSON変換
│   ├── calculate_head_direction.py  # Head Direction分析
│   ├── merge_to_phrases.py       # 句単位へのマージ処理
│   └── utils.py                  # 共通ユーティリティ
├── data/
│   ├── processed/                # 変換済みJSONデータ
│   ├── phrases/                  # 句単位データ
│   └── results/                  # 分析結果 (CSV, JSON)
├── docs/                         # ドキュメント・進捗レポート
├── frontend/                     # React + TypeScript Web UI
│   ├── src/
│   │   ├── components/           # Reactコンポーネント
│   │   ├── hooks/                # カスタムフック
│   │   ├── types/                # TypeScript型定義
│   │   └── constants/            # 定数・マッピング
│   └── public/data/              # デプロイ用データ
└── requirements.txt              # Python依存ライブラリ
```

## 🛠️ セットアップと実行方法

### 1. 環境構築
Python 3.x が必要です。依存ライブラリをインストールします。

```bash
pip install -r requirements.txt
```

### 2. データ準備
ZIPファイルを解凍し、JSON形式に変換します。

```bash
python code/extract_zips.py
python code/parse_conllu.py
```

### 3. 分析の実行
統計情報の生成と類似度分析を行います。

```bash
python code/generate_statistics.py
python code/analyze_tags.py
python code/calculate_similarity.py
```
結果は `data/results/` および `data/results/visualizations/` に出力されます。

### 4. Web UIの起動 (React版)
React + TypeScript によるモダンなWeb UIを使用します。

```bash
cd frontend
npm install
npm run dev
```
ブラウザで `http://localhost:5173/` にアクセスしてください。

### 5. デプロイ (GitHub Pages)
GitHub Actions による自動デプロイが設定されています。`main` ブランチにプッシュすると自動的にデプロイされます。

デプロイ先: https://matsuri9.github.io/dsF2025/

## 📊 対象言語 (33言語)

**PUD言語 (20言語):**
Arabic (ar), Chinese (zh), Czech (cs), English (en), Finnish (fi), French (fr), Galician (gl), German (de), Hindi (hi), Icelandic (is), Indonesian (id), Italian (it), Japanese (ja), Korean (ko), Portuguese (pt), Russian (ru), Spanish (es), Swedish (sv), Thai (th), Turkish (tr)

**追加言語 (13言語):**
Afrikaans (af), Faroese (fo), Hebrew (he), Irish (ga), Komi Zyrian (kpv), Nenets (yrk), Norwegian Nynorsk (no), Sanskrit (sa), Tagalog (tl), Tamil (ta), Uzbek (uz), Vietnamese (vi), Yakut (sah)


## 🔮 今後の展望 (Future Work)

1. **句・文レベルの構造分析**:
   - 単語単位だけでなく、句（Phrase）単位でのパターンマッチング (`merge_to_phrases.py` の活用)
   - n-gram分析による構文パターンの抽出
2. **より高度な可視化**:
   - 依存関係ツリーの視覚的比較機能の実装
3. **言語類型論との照合**:
   - SVO/SOVなどの語順タイプや、形態論的特徴との相関分析

---
**Last Updated**: 2025-12-21

