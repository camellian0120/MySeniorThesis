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
# 小規模言語モデルにおける推論誘導のためのKVキャッシュステアリング
元論文
> https://arxiv.org/abs/2507.08799 \
> https://arxiv.org/pdf/2507.08799

## Task
**1**-**3**. ちゃんとまとめる\
**4**. 適当\
**5**-**7**. 改善点、今後の課題を軸にまとめる\
付録が充実してて良き

## TL;DR
- 推論時にKVキャッシュをワンショットで変更することでモデル挙動を制御する新規技術。
- 大規模モデルから推論スタイルを蒸留し、調整なしで小型モデルへ転移可。
- 

## 概要
KVキャッシュに直接ワンショットで適応される「**キャッシュステアリング**」を提案。\
$\rightarrow$ 思考連鎖推論の為

GPT-4oの推論トレースを活用して、多段階推論へ導く誘導ベクトルの作成。\
微調整やプロンプトの変更は無し。

KVキャッシュ(キーバリューキャッシュ) … 短期記憶のようなもの。
> https://jp.micron.com/about/blog/company/insights/from-buzzword-to-bottom-line-understanding-the-why-behind-kv-cache-in-ai

## はじめに
モデルの内部隠れ状態を直接変更し、挙動を導く**活性化誘導**。\
有用であるものの、デコードプロセス全体を通して、各トークン生成ステップで**継続的な介入**が必要な場合が多い。\
この操作が**不安定性**を生じさせ、ハイパーパラメータ選択を極めて敏感に生成品質を落としかねない。

本研究では、キャッシュステアリングを導入。\
$\rightarrow$ TransformerモデルのKVキャッシュを直接、1度の修正を行うことで動作。

GPT-4oの様な高性能なモデルのステアリングベクトルを小型モデルのKey/Value表現に使うことで、推論軌道を誘導。\
トークン生成前の1度の処理で適用されるため、簡潔に明示的な多段階推論に誘導。

### 利点
- 従来の活性化誘導と比べ、ハイパーパラメータが安定/頑健
- 推論時のオーバーヘッド削減
- 標準的なTransformerでは容易に統合可
- 各ベンチにおいて、精度の上昇
<br/><br/>

ステアリングベクトル … 信号処理、特に音源分離において、ビーム方向(音を強調する方向)を決定するベクトル\
　　　　　　　　取り出したい音源方向のステアリングベクトルと信号の行列積より、強調可
> https://nettyukobo.com/beamformer/

## 関連研究
### 推論と思考の連鎖プロンプティング
プロンプト内で段階的な推論プロセス(思考の連鎖: CoT)を含む問題を示す方法(文脈内学習: ICL)がある。\
これを、小例学習プロンプティングという。
- CoTプロンプティングのゼロショット変種 $\rightarrow$「段階的に考えよ」等指示を追加し、簡略化できる

上記の知見では、
1. 言語モデルでCoT推論を単に誘発するだけでは不十分
2. 推論の様式が重要

よって、キャッシュレベルの介入により、大規模言語モデルさながらの推論行動への誘導を目指す。
<br/><br/>

CoT(Chain of thoughts)
> https://www.ibm.com/jp-ja/think/topics/chain-of-thoughts

ICL(in-context learning) … 少数の入出力のペアに基づいて、新しい入力に対して答えを推論
> https://www.anlp.jp/proceedings/annual_meeting/2024/pdf_dir/P9-14.pdf

### 活性化ステアリング
線形介入を通じて、デコード中の中間層の活性化を操作し、LLMの生成プロセスを暗黙的に制御する技術。\
再学習無しでモデルの行動を誘導/抑制できるために利用できる。

活性化ステアリングの流れは、
1. ベクトル抽出
2. 推論時のモデル活性化へのベクトル注入

ベクトル抽出では、ステアリングベクトルを計算。\
肯定的プロンプト$p^+$と否定的プロンプト$p^-$から活性化を集約、対照セット$C$を作成。
$$C = {(p^+_0, p^−_0),(p^+_1, p^−_1), ...,(p^+_N , p^−_N)}$$
最も一般的な集約手法のDifference-in-Means(Wehner et al., 2025)を使う。\
ベクトルがペア化されている場合には平均差と同一 :
$$s_l = \frac{1}{N} \sum_{(p^+,p^−)∈C} f_l(p^+) − f_l(p^−)$$
- $f_l$は層$l$におけるTransformerモデルの一部
- $N$は対照データセット$C$内の例の数

推論中に、特定の層の活性化関数にステアリングベクトルを加算
$$h^*_l = h_l + c s_l$$
- $h_l$は、ステアリング前の層$l$における活性化関数
- $s_l$は、層$l$から抽出されたステアリングベクトル
- $c$は、ステアリングの強さを決定する係数\
 $c$の値を決定するには、グリッド検索一般的にを行う
<br/><br/>

活性化ステアリング (Activation steering) 元論文
> https://arxiv.org/html/2308.10248v5

Difference-in-Means (DiM) … 両クラスの平均値を単純に計算し、正の値から負の値を引く手法\
　　　　　　　　　　　　　負例を正例に一致させるベクトルを特定するのに最適。
> https://arxiv.org/html/2502.19649v3#S4

平均差 … データの中の2つの単位の値の差の絶対値を、全データに渡って総平均したもの
> http://www.wwq.jp/stacalcul2/meandeff.htm

### キャッシュ操作
本研究では使用されていないが、\
生成前のステップで、KVキャッシュを拡張する手法もある。

また、KVキャッシュのメリットは、
- メモリの使用量の削減
- コンテキスト表現の圧縮 (圧縮出来るのが何故嬉しいのか不明)
<br/><br/>

コンテキスト … データが**意味づけ**され情報になり、複数の情報から特定の目的下で**関連付け**られたもの
> https://zenn.dev/caphtech/articles/ai-context-making-foundations#1.-%E3%80%8C%E3%82%B3%E3%83%B3%E3%83%86%E3%82%AD%E3%82%B9%E3%83%88%E3%80%8D%E3%81%AE%E6%AD%A3%E4%BD%93%EF%BC%9A%E5%8D%98%E3%81%AA%E3%82%8B%E6%83%85%E5%A0%B1%E3%81%8B%E3%82%89%E6%84%8F%E5%91%B3%E3%81%AE%E3%81%82%E3%82%8B%E6%96%87%E8%84%88%E3%81%B8

## キャッシュステアリング
### 事前知識
Transformerベースのモデルでは、
- Query/Key/Valueのベクトル集合に対する自己注意機構に依存
- 文脈化されたトークン表現を計算

入力シーケンスに対して、層$l$の注意機構の出力は、
$$Attention(Q^l, K^l,V^l) = softmax \bigg(\frac{Q^l (K^l)^⊤}{\sqrt {D_h}} \bigg) V^l$$
ただし、$Q^l, K^l,V^l ∈ R^{T×H×D_h}$は層$l$における Query/Key/Value のテンソルであり、
- $T$はシーケンス長
- $H$はアテンションヘッド数
- $D_h$は各ヘッドの次元数

自己回帰的デコード中に、モデルが処理済みトークンに対応する$K^l$と$V^l$を保存。



テンソル … 多次元配列のこと

自己回帰的デコード(autoregressive decoding) … 
> https://qiita.com/m3yrin/items/7a6df0d7f5d44f0b5efc#auto-regressive%E3%81%A7left-to-right%E3%81%AA%E3%83%86%E3%82%AD%E3%82%B9%E3%83%88%E7%94%9F%E6%88%90
