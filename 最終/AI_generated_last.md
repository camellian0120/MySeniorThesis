---
marp: true
math: mathjax
header: "大規模言語モデルによるソフトウェア脆弱性の検出"
paginate: true
style: |
  section{
    font-size: 38px;
  }
  strong {
    color: #F79428;
  }
  em {
    font-style: normal;
    color: #0B3E8D;
    font-weight: bold;
  }
  h1 {
    font-size:48px;
    color: #0B3E8D;
  }
  h2 {
    font-size:48px;
    color: #0B3E8D;
    margin-bottom:-.2em;
  }
  h2 strong {
    font-size:48px;
    color: chocolate;
  }
  h3 {
    font-size:40px;
    color: #0B3E8D;
    margin-top:-.2em;
    margin-bottom:-.1em;
  }
  h3 strong {
    color: chocolate;
  }
  .columns {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 1rem;
  }
  .columns.var {
    display: grid;
    grid-template-columns: var(--ratio) 1fr;
    gap: 1rem;
  }
  .columns.spaced {
    display: grid;
    grid-template-columns: var(--ratio) 10% 1fr;
    gap: 1rem;
  }
  .gray {
    background: whitesmoke;
  }
  .theorem {
    background: whitesmoke;
    padding-top: 0.1em;
    padding-bottom: 0.1em;
    padding-left: 0.4em;
  }
  .statement {
    margin-top: -0.5em;
    padding-left: 0.7em;
  }
  .quote {
    background: whitesmoke;
    margin-left: 5%;
    margin-right: 5%;
    margin-bottom: 3%;
  }
  .quote.white {
    background: white;
  }  .katex .delimcenter,
  .katex .op-symbol {
    display: inline-block;
  }  
  .arrow {
    margin-top: auto;
    margin-bottom: auto;
    margin-left: auto;
    margin-right: auto;
    width: 0; 
    height: 0;   
  }
  .arrow.right {
    border-top: 40px solid transparent;
    border-bottom: 40px solid transparent;
    border-left: 40px solid gray;
  }
  .arrow.down {
    border-left: 40px solid transparent;
    border-right: 40px solid transparent;
    border-top: 40px solid gray;
  }
  .arrow.up {
    border-left: 40px solid transparent;
    border-right: 40px solid transparent;
    border-bottom: 40px solid gray;
  }
  .center {
    margin-right: auto;
    margin-left: auto;
    text-align: center; 
        font-size: 28px;
  }
  .middle {
    margin-top: auto;
    margin-bottom: auto;
  }
  .large {
    font-size: 28pt;
  }
  .hline {
    margin-top:20px;
    margin-bottom:20px;
    margin-left: 0%;
    margin-right: 0%;
    width: 1fr; 
    height: 0;   
    border-top: 2px solid gray;
  }
  .vline {
    margin-top:0%;
    margin-bottom:0%;
    margin-left: 20px;
    margin-right: 20px;
    width: 0; 
    height: 1fr;   
    border-left: 2px solid gray;
  }
  .shade {
    width: 1fr;
    background: white;
    opacity: 0.7;   
  }
  .white {
    width: 1fr;
    background: white;
  }
  .split{
    display: table;
  }
  .split-item {
    display: table-cell;
    padding: 0px;
  }
  .split-left {
    position: fixed;
  }
  .split-right {
    position: fixed;
    right: 0;
  }
---

# 大規模言語モデルによる  
# ソフトウェア脆弱性の検出


#### 高知大学 理工学部情報科学科
#### 木脇研究室 B4 横川武典

---

## 研究背景

- Webアプリケーションにおける  
  **ソフトウェア脆弱性**は依然として深刻
- 既存の静的解析・ルールベース手法には  
  - ルール作成コスト  
  - 新種脆弱性への追従困難  
  という課題がある

<div class="hline"></div>

- **大規模言語モデル (LLM)** は  
  ソースコード理解能力を持つ点で注目されている

---

## 研究目的

本研究の目的は以下の2点である：

- **LLMを用いた脆弱性検出の有効性の検証**
- モデル構成の違いが  
  検出性能に与える影響の分析

<div class="theorem">
<em>Base / Fine-Tuned / RAG</em>  
という3構成を比較対象とする
</div>

---

## 対象とする脆弱性

本研究では以下のような  
**Webアプリケーション脆弱性**を対象とした：

- XSS（Cross-Site Scripting）
- CSRF（Cross-Site Request Forgery）
- セッション管理の不備 など

<div class="statement">
主にPHPで記述された  
小規模Webアプリケーションを評価対象とする
</div>

---

## LLM構成①：Base LLM

- 事前学習済みのLLMを  
  **そのまま使用**
- 脆弱性検出用の追加学習は行わない

<div class="theorem">
<strong>利点</strong>：追加コストなしで利用可能

<strong>課題</strong>：脆弱性特有の判断が不安定
</div>

---

## LLM構成②：Fine-Tuned LLM

- 脆弱性検出データセットを用いて  
  **追加学習（Fine-Tuning）**
- 出力形式・観点をモデルに明示

<div class="theorem">
<strong>期待</strong>：  
脆弱性判断の一貫性向上
</div>

---

## LLM構成③：RAG-augmented LLM

- 脆弱性に関する知識を  
  **外部文書として検索・付与**
- LLMは推論に専念

<div class="theorem">
<strong>特徴</strong>：  
最新・詳細な知識を柔軟に反映可能
</div>

---

## 評価方法

- 各構成に対し同一コードを入力
- 出力結果から脆弱性検出を判定
- 以下の指標を用いて性能を評価

<div class="quote">
- Precision<br/>
- Recall<br/>
- F1-score<br/>
- AUC（Area Under the ROC Curve）
</div>

---

## 実験結果（概要）

- **Base LLM**
  - Recallは高いがFPが多い
- **Fine-Tuned LLM**
  - PrecisionとRecallのバランスが改善
- **RAG構成**
  - 特定脆弱性で最も安定した性能

　$\rightarrow$ モデル構成により  
　 検出特性が大きく異なる

---

## 考察

- Fine-Tuningは  
  **汎用的な検出精度の底上げ**に有効
- RAGは  
  **知識依存度の高い脆弱性**に強い
- 一方で：
  - 過検出（False Positive）
  - 判断根拠の不透明さ  
 といった課題も残る

---

## まとめ

- LLMは  
  **ソフトウェア脆弱性検出に有望**
- 構成の工夫により  
  性能特性を制御可能
- 用途に応じた  
  **Base / FT / RAGの使い分け**が重要

---

## 今後の課題（任意）

- より大規模・多様なコードへの適用
- 脆弱性種別ごとの最適構成の検討
- 検出理由の可視化・説明性向上

---

## ご清聴ありがとうございました
