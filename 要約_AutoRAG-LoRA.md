---
marp: false
math: mathjax
header: "ESL輪読"
paginate: true
style: |
  strong {
    color: #F79428;
  }
  em {
    font-style: normal;
    color: #0B3E8D;
    font-weight: bold;
  }
  h1 {
    color: #0B3E8D;
  }
  h2 {
    color: #0B3E8D;
    margin-bottom:-.2em;
  }
  h2 strong {
    color: chocolate;
  }
  h3 {
    color: #0B3E8D;
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
  .images {
    float: left;
  }
---

# AutoRAG-LoRA 軽量アダプタを使ったハルシネーションをきっかけとする知識の再チューニング
## TL;DR
- ハルシネーションを検出、対処するフレームワーク
- 多くの手法を組み合わせることで、ハルシネーションを抑制可能
- 曖昧さや多義性、記号接地の弱いクエリでは性能の期待が不可

記号接地 … 記号と意味・概念に対応付けること
クエリ … 問い合わせ・要求

## 概要
ハルシネーションに対処するRAG(検索拡張生成)用フレームワーク、AutoRAG-LoRAを開発。
### 特徴
- 以下の3つのパイプラインを含む
1. 自動プロンプト書き換え (再定式化)
2. ハイブリッド検索 (疎と密)
3. 検索結果を応答の基盤とするLoRA

- ハルシネーション検出モジュール
1. 分類器ベースと自己評価手法の2つ
2. 生成された回答の信頼度を付与
3. フィードバックによる修正ループ (KL正則化)

## 要約
### 1. 導入
従来のRAGは外部証拠に基づいて出力の精度を向上。\
$\rightarrow$ だが、ハルシネーションは依然として存在。\
 　 ハルシネーションを検出し、反応して実行されるプロセスが必要。\
 　 $\rightarrow$ AutoRAG-LoRA

### 2. 方法論
#### クエリの変換
生の入力クエリをタスク指向のプロンプトへ変換
