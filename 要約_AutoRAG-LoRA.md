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
元論文
> https://arxiv.org/abs/2507.10586 \
> https://arxiv.org/html/2507.10586

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
2. 生成された回答に信頼度を付与
3. フィードバックによる修正ループ (KL正則化)

## 要約
### 1. 導入
従来のRAGは外部証拠に基づいて出力の精度を向上。\
$\rightarrow$ だが、ハルシネーションは依然として存在。\
 　 ハルシネーションを検出し、反応して実行されるプロセスが必要。\
 　 $\rightarrow$ AutoRAG-LoRA

### 2. 方法論
![](./system_architecture.jpg)
図1. プロンプト書き換え、ハイブリット検索、ハルシネーション検出、アダプタラーニング、KLフィードバック修正を示すAutoRAG-LoRAのシステムアーキテクチャ

#### クエリの変換
生の入力クエリ$x$をタスク指向のプロンプト$x^′$へ変換\
この研究では、**静的テンプレート** + **軽量な学習済みT5エンコーダ**で動的なプロンプトエンジニアリング\
T5エンコーダは、**命令のデータセット**と**クエリと命令のペア**の混合でFT\
ex) 「日光はがんを引き起こすか？」$\rightarrow$ 「事実に基づいて答えなさい:日光はがんを引き起こすか？」

T5エンコーダ … Text-to-Text Transfer Transformerの略\
　　　　　　Encoder-DecoderのTransformerモデルに基づく\
　　　　　　大規模なテキストコーパスで一般的な知識を獲得済み
> https://qiita.com/Yuhei0531/items/ca23b198e7ab6e27eac0

#### ハイブリッド検索
密/疎な表現を使うハイブリッド文書選択\
候補文書毎にハイブリッド検索スコア$d_i$を計算\
疎な表現にBM25、密な表現$sim_{dense}$にBERT等を使う\
論文中では、$\alpha = 0.6$として疎の類似度を優先し、上位10件の文章に$k = 60$でRRFを適応
$$score⁢(d_i)=α⋅BM25(x^′,d_i)+(1−α)⋅sim_{dense}(x^′,d_i) 　 where 　 α∈[0,1]$$

BM25 … 情報検索で文書の関連度をスコアリング\
　　　　クエリとドキュメントの類似度を数値で示す
> https://zenn.dev/m_nakano_teppei/articles/b91b8ab59c15e7

BERT … TransfoermerのEncoder部分を使ったモデル\
　 　 　コサイン類似度を使って、2つの文章の類似度を計算できる
> https://qiita.com/Tadataka_Takahashi/items/6abc22b0b6d94a6da4d1#43-%E6%96%87%E8%84%88%E5%8C%96%E3%81%95%E3%82%8C%E3%81%9F%E5%8D%98%E8%AA%9E%E5%9F%8B%E3%82%81%E8%BE%BC%E3%81%BF%E3%81%AE%E5%8F%96%E5%BE%97

RRF … システム$i$の文章$d$の逆順位とハイパーパラメータ$k$に基づいてスコアを計算して総和を取る
$$RRF(d) = \sum_i \frac{1}{k + rank_i (d)}$$
> https://hironsan.hatenablog.com/entry/rank-fusion-algorithms#RRF

#### スコア決定メカニズム
- 複数の表現で中程度にランク付けされたドキュメントが、1つの表現で高ランクを付けられたドキュメントよりも優先

- 学習可能な文章選択の為の検索ポリシーアダプタ\
学習された関連性に基づいて、整列された文書の動的な優先順位付けが可能\
LoRAで強調された重みを持つ2層の多層パーセプトロン\
以下の式で、プロンプト$x^′$を条件として文章$d_i$のスコア付けを学習\
$f(x^′,d_i)$はプロンプトと文章のペアの特徴表現を表し、$W_{LoRA}$はLoRAを介して適応された低ランク行列
$$π⁢(d_i∣x^′)=softmax(W_{LoRA}f(x^′,d_i))$$
入力表現は、プロンプトと文章のCLS埋め込みの連結で構築
$$f(x^′,d_i) = [CLS⁢(x^′);CLS(d_i)]$$

特徴表現 $\fallingdotseq$ 特徴量？\
低ランク行列 … $\mathbf L = \mathbf M \mathbf N$の右辺の様に低いランクの積で表せる行列？
> https://www.cc.u-tokyo.ac.jp/research/files/24.pdf

CLS … BERTモデルにおいて、先頭に追加されるトークン\
　　　特定の意味を持たず、処理を通じて全体の文脈を捉える
> https://kento1109.hatenablog.com/entry/2019/04/28/142507
> https://www.anlp.jp/proceedings/annual_meeting/2021/pdf_dir/C4-2.pdf
> https://note.com/shima_7_7/n/n6258e03cfb50

#### 学習状況
以下は、現状未使用であるが、利用可能追加可能なモジュール\
動的な文書の際ランク付けとハルシネーションの軽減に向けて準備中\
$d^+$は正しい意味付けをされた文章、$d_j^-$は誤った意味付けをされた文章\
2値の対照損失:
$$ℒ_{contrast} = −log \frac{exp(sim(f(x^′,d^+)))}
                           {exp⁡(sim(f(x^′,d^+)))+∑_j exp(sim(f(x^′,d_j^−)))}$$

対照損失 (contrastive loss)
> https://www.hello-statisticians.com/ml/deeplearning/simclr1.html#i-3

#### LoRAを強化したデコードによる接地生成
タスク指向のプロンプト$x^′$と上位$K$件の検索文章$D$を元に生成モジュール$y \sim P_{gen}(y | x^′, D)$を利用\
$y$はLoRAで計算効率を維持しつつ事実との整合性を強化するために微調整\
実装では、微調整の際の安定化の為にドロップアウトを利用
$$y = Wh + \alpha \cdot BAh$$

LoRA … Low-Rank Adaptation\
　 　 　元の学習機の重み$W$に加えて$\Delta W$を追加し、学習時に$\Delta W$の値のみ変化させることで微調整が可\
　 　 　$\Delta W$は、低ランク行列$A$と$B$より、$\Delta W = BA$と表せる\
　 　 　論文中では、$\Delta W$に対してハイパーパラメータ$\alpha$を設けている\
　 　 　$W^′ = W+\Delta W = W+BA$

Q層/V層 … 自己注意機構のクエリ行列(Q)とバリュー行列(V)のこと？
> https://qiita.com/qOpenDev/items/e388509324e29d338a84#51-%E8%87%AA%E5%B7%B1%E6%B3%A8%E6%84%8F%E6%A9%9F%E6%A7%8B

#### 条件付きのアダプター経路制御
ハルシネーションのリスクが高いと判断された場合にLoRAアダプタを起動する判断を取る\
ハルシネーション分類器のソフト出力$p_{hall} \in [0,1]$をリスクの基準とする\
具体的には、閾値$\tau$(デフォルトでは$0.7$)より分岐する
$$AdapterActive = \bigg\{ \frac{1 \ \ if \ h_{hall} > \tau}{0 \ \ \ \ otherwise}$$
1. AdapterActiveが$1$を取ると、ハルシネーションを起こしやすいと判定され、学習中のフィードバック補正の為にLoRAアダプタを起動
2. AdapterActiveが$0$を取ると、重みを固定してLoRAアダプタを非アクティブにして出力の生成を進める

今後の展望として、この部分は改善したいらしい

![](./adapter_activator.jpg)
図2. ハルシネーションのスコア$p_{hall}$に基づくLoRAアダプタの条件付き経路選択ロジック\
 アダプターがハルシネーションの確率の閾値を超えた場合にのみ作動

#### ハルシネーションの検出
タスク指向のプロンプト$x^′$等を使っても、取得した文章$d_i$と生成された出力$y \sim P_{gen}(y | x^′, D)$との不一致より、ハルシネーションが起きる可能性\
検出モジュールにより、出力が取得された証拠に正しく基づいているか判断

- 分類器に基づく検出
ハルシネーションの確率を出力$y$を元に計算\
出力$y$と文章$D$の連結$[y;D]$、シグモイド活性化関数$\sigma(\cdot)$、学習可能な分類器のパラメータ$W_{clf}$と$b$より
$$p_{hall} = \sigma(W_{clf} [y; D] + b)$$

- 分類器の訓練用データセットの構築
分類器に使うRoBERTaベースのモデルをファインチューニングする為に利用\
人の書いた文章または証拠に基づいて補完された例$(y_{true} = 0)$\
　 +\
合成ハルシネーション … 正しい文章の一部に誤った内容に置き換えたもの$(y_{true} = 1)$

- 説明可能で自己評価可能なアプローチ\
2値のハルシネーションフラグ、連続値を取る信頼スコア等を元に多角的な事実一致の視点を提供
1. 関連性伝播または統合勾配法を使い、トークン毎の貢献度を評価
2. 注意エントロピーを使って、拡散的または焦点の定まらない推論を特定
3. $P_{gen}(y | x^′, D)$と$P_{ret}(y|D)$のコサイン類似度やJSダイバージェンス等意味ドリフトの指標

- 統合勾配法 … 特徴量からモデルの予測間の関係を説明
> https://www.tensorflow.org/tutorials/interpretability/integrated_gradients?hl=ja

- JSダイバージェンス … 確率分布の類似度を表す指標、対称性が存在
> https://www.hello-statisticians.com/explain-terms-cat/js_divergence1.html#JS-2

#### KL正則化フィードバック補正ループ
ハルシネーション検出モジュールの出力$y \sim P_{gen}(y | x^′ ,D)$が文章$D$を不一致と判定したら有効になる
以下の繰り返しで生成結果を事実に基づくようにファインチューニング
1. KL正則化
2. 対比学習

- 参照分布 $P_{ret}$
取得条件付き参照分布$P_{ret}(y | x^′, D)$を取得した文章に厳密に条件付けられたデコード分布として定義
実装では、凍結モデルのトークンとソフトマックス関数を使って
$$P_{ret}(y) = softmax(f_{frozen} (x^′, D))$$

- KLダイバージェンスペナルティ
モデルの生成と調整された参照間のKLダイバージェンス
$$ℒ_{KL}=\sum_y P_{gen}(y∣x^′,D) \cdot \log \frac{P_{gen}(y∣x^′,D)}{P_{ret}(y∣x^′,D)}$$

KLダイバージェンス … 2つの確率分布がどれだけ似ているかを示すもの
> https://qiita.com/harmegiddo/items/2a24a36418fade0eaf44#2-jensenshannon-divergence

- 対照的ハルシネーション損失
事実の整合性をさらに明確にするため、対照的なKL項を導入\
$P^+ : $高い一致度と低いハルシネーションスコア$(p_{hall} < 0.3)$で生成された根拠に基づく補完\
$P^- : $高いハルシネーションスコア$(p_{hall} > 0.7)$を持つ補完。\
　　以前のモデルのチェックポイントからのサンプリングや合成否定文\
下式により根拠のある分布に収束する
$$ℒ_{contrast}=KL(P^+ || {ret})−KL(P^− || P_{ret})$$

合成否定文 … 正しい文章の一部を変更して、誤った文章にしたもの

- 総生成損失
最終的な訓練対象は、交差エントロピー損失と上記の損失、ハイパーパラメータを使って、
$$ℒ_{total}=ℒ_{CE}+λ_1⋅ℒ_{KL}+λ_2⋅ℒ_{contrast}$$

#### 評価指標と最終出力の解釈
- KLダイバージェンスのドリフト\
生成モデル$P_{gen}(y∣x^′,D)$と取得文脈に一致した参照分布$P_{ret}(y∣x^′,D)$間の分布的乖離を、KL距離を用いて測定\
生成が取得した情報にどれだけ準拠しているかを示す指標\
$$KL_{Drift}=∑_y P_{gen}(y∣x^′,D) ⋅ log P_{gen}(y∣x^′,D)P_{ret}(y∣x^′,D)$$

ドリフト … 予期せぬ変化によって、モデルの予測性能が時間経過とともに劣化すること
> https://atmarkit.itmedia.co.jp/ait/articles/2202/21/news033.html

- 意味的ジェンセン・シャノン・ダイバージェンス (JSD)
意味的な重複を考慮し、文体の差によるペナルティを回避するために、生成された出力と取得情報間のJSDを計算\
この指標は、事実に対する一貫性を測定

JSD … KLダイバージェンスに平滑性と対称性を加えたもの。KLダイバージェンスと比べて、距離として扱える。
> https://qiita.com/harmegiddo/items/2a24a36418fade0eaf44#2-jensenshannon-divergence

- トークン関連性と帰属
トークン単位の解釈可能性技術を使い、取得した文章の一部 → 生成された出力への影響を可視化・説明\
帰属重みを強調し、ハルシネーションのデバッグや取得効果の検証に有効
1. レイヤー別関連性伝播 (LRP) … NNの逆伝播により、重みを動した際の予測値の変化を調べる(=出力への**貢献度**)。入力値が重要
> https://zenn.dev/pluck/articles/d29dafe92cdfc1#lrp%EF%BC%88layer-wise-relevance-propagation%EF%BC%89
2. 統合勾配 … 特徴量からモデルの予測間の関係を説明

- 注意エントロピーと焦点メトリクス
デコードステップ全体で注意エントロピーを分析\
高いエントロピーの際にハルシネーション的な文脈と関連

- 最終出力
出力に含まれるものは、
1. タスク指向プロンプト$x^′$と取得した文章$D$を条件に生成された応答$y$
2. ハルシネーション信頼スコア・2値フラグ (分類器/自己評価より)
3. 説明の追跡 (オプション)
4. アダプタ活性化、検索スコア、修正ループのトリガのログ

### 4. 結果
Mistral-7B に対してAutoRAG-LoRAあり/無しで比較

ハルシネーション率低下
$$35.4\% \rightarrow 18.9\%$$

KLダイバージェンスのドリフトの低減
$$0.78 \rightarrow 0.42$$

意味的JSDで測定される一貫性の増加
$$0.62 \rightarrow 0.31$$

流暢性と関連性 (ROUGE-L)
$$37.5 \rightarrow 64.8$$

ROUGE(ルージュ) … テキスト要約の評価の際に使われる指標。いくつかのフレーバーがある\
　　　　　　　ROUGE-Lでは、生成した要約と人の作成した要約の、**一致する最長のシーケンス**を評価する。
> https://qiita.com/icoxfog417/items/65faecbbe27d3c53d212#rouge-lrouge-w

#### 限界と今後の課題
1. 曖昧または多目的なクエリに対して性能低下
2. 高品質な検索が必要不可欠
3. LoRAアダプタを有効にする閾値に連続的な活性化ダイナミクス
4. アダプタの更新を隔離して過学習を回避
　$\rightarrow$ ドメインシフトの対応が困難な可能性

ドメインシフト … モデルの訓練に使ったデータとモデルを適応したいデータ間の**分布の違い**
> https://note.com/bdomestic/n/n5c577028cdc2

#### 議論
$p_{hall}$を通じて定義される、高リスクな生成領域ではアダプタを選択的に更新することで過学習を回避。
