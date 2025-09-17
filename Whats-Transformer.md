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
## 論文のテーマ
1. ML系\
設計の改善等 (残りの時間でやるのは大変)

2. DS系\
このデータに適応してみた等 (身近な問題に適応してみる)\
例)   2-1. 高知大Moodleアシスタント, 古のコードの解析等\
 　 2-2. csで解けないとされる問題をllmに解かせてみる。\
 　 2-3. 難解な文章を読ませてみる(古文書, 怪文書etc)

3. CodeGen
日々のコーディングで不満な点\
$\rightarrow$ 変数名の付け方が安定しない、正規表現を見たくない等。\
コード生成AIをアシスタントを使っていて不満な点\
$\rightarrow$ 最も保守性の高いAI支援コーディングが、AIに生成して貰う $\rightarrow$ リファクタリングする/コードレビューをガッツリする な現状。

## TransformerのKey/Query/Valueはどうなっているか
- 注意機構のKey/Query/Valueとは\
 $\cdot$ Key $...$ 他のトークンへのインデックス\
 $\cdot$ Query $...$ 他のトークンとの関心度・関連度\
 $\cdot$ Value $...$ 単語そのものの特徴量

- 自己注意機構とKey/Query/Value 
1. 入力文から入力埋め込み$h_i$を作る $ (1, 2, ..., N)$
2. 入力埋込み$h_i$からクエリ埋め込み$q_i$、キー埋め込み$k_i$、バリュー埋め込み$v_i$を作成 ($D$次元ベクトル)\
クエリ行列$W_q$、 キー行列$W_k$、バリュー行列$W_v$は、$D \times D$次元の重み。訓練時に学習する部分
$$\begin{align}
q_i &= W_q h_i \\
k_i &= W_k h_i \\
v_i &= W_v h_i
\end{align} \tag{1}$$
3. $i$番目のクエリ埋込みと$j$番目のキー埋め込みの内積をとり、関連性スコアとする\
この時、$\sqrt D$をとることで値が大きくなりすぎないようにする
$$s_{ij} = \frac{q_i^T k_j}{\sqrt D} \tag{2}$$
4. 関連スコアをSoftmax関数を使って正規化した重み$\alpha_{ij}$とする
$$\alpha_{ij} = \frac{exp(s_{ij})}{\sum^N_{j' = 1} exp(s_{ij'})} \tag{3}$$
5. 出力埋め込み$o_i$は正規化した重み$\alpha_{ij}$とバリュー埋め込み$v_j$の重み付き和
$$o_i = \sum^N_{j = 1} \alpha_{ij} v_j \tag{4}$$

- マルチヘッド注意機構のKey/Query/Value\
同時に複数の注意機構を適応する手法\
$M$個の注意機構を同時に動かすとき、各埋め込みは$\frac{D}{M}$次元、$\frac{D}{M} \times D$次元 (ただし、$M$は$D$の約数)\
$1, ..., M$番目のヘッドの個数$m$を使って、各ヘッドごとにKey/Query/Valueを計算
$$\begin{align}
q^{(m)}_i &= W^{(m)}_q h_i \\
k^{(m)}_i &= W^{(m)}_k h_i \\
v^{(m)}_i &= W^{(m)}_v h_i
\end{align} \tag{4}$$
同様に関連スコア、正規化した重み、出力埋め込みも各ヘッドで計算
$$\begin{align}
s^{(m)}_{ij} &= \frac{q_i^{(m)T} k_j^{(m)}}{\sqrt{D/M}} \\
\alpha^{(m)}_{ij} &= \frac{exp(s^{(m)}_{ij})}{\sum^N_{j' = 1} exp(s^{(m)}_{ij'})} \\
o^{(m)}_i &= \sum^N_{j = 1} \alpha^{(m)}_{ij} v^{(m)}_j
\end{align} \tag{5}$$
各ヘッドごとの出力埋め込みを連結して、$i$番目の出力表現とする ($D \times D$行列)
$$o_i = W_o \begin{bmatrix}\ o_i^{(1)} \\ \vdots \\ o_i^{(M)} \end{bmatrix} \tag{6}$$

\
自然言語処理モデルを直感的に理解したい（１）　Transformer | 自然言語処理を使ったソフトウエア開発
> https://nagomi-informal.net/archives/1772

大規模言語モデル入門 (技術評論社) p.20~

## Attesion機構が何をしている
A. 似ている情報を結びつけている\
QueryとKeyの類似度から、Valueのどの値に注意を向けるべきかを計算する機構

- Attensionの式の原文\
特に以下の式をScaled Dot-Product Attentionという。\
詳細な流れは上記の自己注意機構を参照
$$Attension(Q, K, V) = softmax \bigg( \frac{QK ^ T}{\sqrt{d_k}} \bigg) V  \tag{7}$$

複数のScaled Dot-Product Attentionの出力埋め込みを連結することでマルチヘッド注意機構も実現可能

\
大規模言語モデル入門 (技術評論社) p.20~

Transformerを理解したい - Zenn
> https://zenn.dev/sunbluesome/articles/078ac9a9afca6a#attention

Attention Is All You Need - arXiv
>  https://arxiv.org/html/1706.03762v7

イラストだけで理解するTransformer／自己注意機構 #LLM - Qiita
> https://qiita.com/qOpenDev/items/e388509324e29d338a84#515-%E8%87%AA%E5%B7%B1%E6%B3%A8%E6%84%8F%E6%A9%9F%E6%A7%8B%E3%81%AE%E6%B0%97%E6%8C%81%E3%81%A1

--- 

## LLMとSLMの互換性はどう取っている (元論文参照)
ステアリングベクトルはどのトークン位置/レイヤー/モデル部分でも適応・抽出が可能?

> It is important to mention that the vector can be extracted and applied to different token positions,layers, and parts of the model, which are treated as hyperparameters or design choices.


KV Cache Steering p.3 中央
> https://arxiv.org/pdf/2507.08799
