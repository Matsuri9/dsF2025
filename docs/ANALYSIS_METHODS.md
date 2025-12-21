# 語順分析手法 解説ドキュメント

本プロジェクトでは、Universal Dependencies (UD) コーパスを用いて言語間の文法的類似性を分析します。
以下の分析手法を実装しています。

---

## 目次

1. [n-gram分析](#1-n-gram分析)
2. [レーベンシュタイン距離分析](#2-レーベンシュタイン距離分析)
3. [Head Direction分析（語順方向分析）](#3-head-direction分析語順方向分析)

---

## 1. n-gram分析

### 概要

文中で連続して出現するタグ（UPOS/DEPREL）のパターンを抽出し、言語ごとの頻出パターンを比較する手法。

### 対象データ

- **UPOS n-gram**: 品詞タグの連続パターン（例: `DET-NOUN-VERB`）
- **DEPREL n-gram**: 係り受け関係タグの連続パターン（例: `det-nsubj-root`）
- **Phrase Head n-gram**: 句の主辞UPOSの連続パターン

### 手順

```
1. 各文からタグ列を取得
2. n個の連続タグを抽出（2-gram, 3-gram等）
3. 言語ごとに頻度をカウント
4. 上位パターンを比較
```

### 出力ファイル

| ファイル名 | 内容 |
|-----------|------|
| `upos_ngram_2gram_top20.csv` | UPOS bi-gram 上位20パターン |
| `upos_ngram_3gram_top20.csv` | UPOS tri-gram 上位20パターン |
| `deprel_ngram_*.csv` | DEPREL n-gram パターン |
| `phrase_head_ngram_*.csv` | Phrase Head n-gram パターン |

### 利点・限界

| 利点 | 限界 |
|------|------|
| シンプルで直感的 | 順序のみに着目、構造を無視 |
| パターン発見に有効 | 言語間の距離計算には不向き |

---

## 2. レーベンシュタイン距離分析

### 概要

2つの文（タグ列）間の編集距離を計算し、言語間の平均距離を求める手法。
PUDコーパスはパラレルコーパスのため、同一内容の文同士を直接比較できる。

### 計算式

```
レーベンシュタイン距離 = 挿入・削除・置換の最小回数

正規化距離 = レーベンシュタイン距離 / max(文1の長さ, 文2の長さ)
```

### 対象データ

- **UPOS列**: 品詞タグの編集距離
- **DEPREL列**: 係り受け関係タグの編集距離
- **Phrase Head列**: 句主辞の編集距離

### 出力ファイル

| ファイル名 | 内容 |
|-----------|------|
| `upos_levenshtein_distance.csv` | UPOS列の言語間距離行列 |
| `deprel_levenshtein_distance.csv` | DEPREL列の言語間距離行列 |
| `phrase_head_levenshtein_distance.csv` | Phrase Head列の距離行列 |

### 可視化

- ヒートマップ: 距離行列の視覚化
- 樹形図（デンドログラム）: 階層的クラスタリング
- MDS/t-SNE: 2次元散布図

### 利点・限界

| 利点 | 限界 |
|------|------|
| 文全体の構造を比較 | 文の長さに影響を受ける |
| パラレル文の直接比較 | 個別の文法関係を区別しない |

---

## 3. Head Direction分析（語順方向分析）

### 概要

UD係り受け構造を用い、**Head（親）とDependent（子）の相対位置**を統計的にスコア化する手法。
各文法関係について「Head-Initial率」を算出し、言語間の語順的距離を計算する。

### 理論的背景

言語類型論では、語順を以下のように分類する：

| 分類 | 説明 | 例 |
|------|------|-----|
| **Head-Initial** | Head（主辞）が前に来る | 英語: eat apple (VERB-OBJ) |
| **Head-Final** | Head（主辞）が後に来る | 日本語: りんごを 食べる (OBJ-VERB) |

### Head-Initial率

```
Head-Initial率 = HeadがDependentより前にある回数 / 総出現回数

0.0 = 完全にHead-Final（例: 日本語の動詞-目的語）
1.0 = 完全にHead-Initial（例: 英語の動詞-目的語）
0.5 = 順序が一定しない
```

### ペアの種類

各トークンについて `(HeadのUPOS, DependentのUPOS, DEPREL)` の組み合わせを抽出：

```
例: "The dog eats food"

dog  → eats (NOUN → VERB, nsubj) → VERB-NOUN-nsubj ペア
food → eats (NOUN → VERB, obj)   → VERB-NOUN-obj ペア
```

### UPOS/DEPRELマージ

次元削減のため、意味的に近いタグをグループ化：

**UPOS マージ（17種類 → 6カテゴリ）**

| カテゴリ | 元のタグ |
|---------|---------|
| NOMINAL | NOUN, PROPN, PRON |
| VERBAL | VERB, AUX |
| MODIFIER | ADJ, ADV |
| FUNCTION | ADP, DET, PART, SCONJ, CCONJ |
| OTHER | NUM, INTJ, SYM, X |
| PUNCT | PUNCT |

**DEPREL マージ（37種類 → 7カテゴリ）**

| カテゴリ | 元のタグ |
|---------|---------|
| CORE_ARG | nsubj, obj, iobj, csubj, ccomp, xcomp |
| OBLIQUE | obl, advcl |
| MODIFIER | amod, advmod, nummod, acl |
| FUNCTION | case, det, mark, cop, aux |
| NOMINAL_MOD | nmod, appos |
| COMPOUND | compound, flat, fixed |
| COORD | conj, cc |

### 距離計算

言語ごとにHead-Initial率のベクトルを作成し、以下の距離を計算：

| 距離 | 計算式 | 特徴 |
|------|-------|------|
| コサイン距離 | 1 - cosine_similarity | ベクトルの方向を比較（スケール不変） |
| ユークリッド距離 | sqrt(Σ(xi - yi)²) | 絶対的な差を測定 |

### 出力ファイル

| ファイル名 | 内容 |
|-----------|------|
| `head_direction_rates_raw.csv` | Head-Initial率（生データ版） |
| `head_direction_rates_merged.csv` | Head-Initial率（マージ版） |
| `head_direction_distance_cosine_*.csv` | コサイン距離行列 |
| `head_direction_distance_euclidean_*.csv` | ユークリッド距離行列 |

### 実行例の結果

**最も類似している言語ペア（コサイン距離）**

```
 1. Italian - Spanish      : 0.0007
 2. French  - Portuguese   : 0.0015
 3. Italian - Portuguese   : 0.0016
```

ロマンス語系が最も類似 → 言語類型論的に妥当な結果

### 利点・限界

| 利点 | 限界 |
|------|------|
| 文法関係ごとに独立した分析が可能 | 係り受け解析の精度に依存 |
| 文の長さに依存しない | 一部の文法関係はスパース |
| SVO/SOV等の大局的語順と局所的語順を両方捉える | |

---

## スクリプト一覧

| スクリプト | 説明 |
|-----------|------|
| `parse_conllu.py` | CoNLL-UファイルをJSONに変換 |
| `merge_to_phrases.py` | トークンを句単位にマージ |
| `analyze_word_order.py` | n-gram・レーベンシュタイン分析 |
| `calculate_head_direction.py` | Head Direction分析 |
| `utils.py` | 共通ユーティリティ（マージマッピング等） |

---

## 参考文献

- Dryer, Matthew S. (2013). "Order of Subject, Object and Verb." In: WALS Online.
- Universal Dependencies Guidelines: https://universaldependencies.org/
- PUD (Parallel Universal Dependencies): 20言語のパラレルコーパス
