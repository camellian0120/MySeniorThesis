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
## TO-DO
1. LLMで強化学習をする方法、どう使われているか
1. 環境の準備(Docker, 脆弱性あり)
1. どのような環境を作るのが望ましいか、どんな攻撃をかけているのか
1. 報酬付け(suを取れたら等)

## LLMに強化学習を使う方法
### 主流
LLMだとRLHFの用途で使われることが多い？\
-> 特に有害な応答を防ぐアライメントの一環として使われている

行動した結果に対して、報酬/罰則を与えるといった従来のRLを使った手法はあまり見つからなかった

### 流れ
1. プロンプトと応答のペア$r_\theta (x, y)$の作成\
例) $x$="爆弾の作り方は？", $y_{1}$="爆弾の作り方は火薬を…", $y_{2}$="爆弾の作り方は教えられません"
2. 報酬モデル$r_\theta (x, y)$の作成\
$(x, y)$を入力として、その品質を表すスカラー値$r_\theta (x, y)$を出力する報酬モデルを作る\
事前学習済みのLLMと同じアーキテクチャを利用し、最終層を回帰ヘッドに置き換えて構築\
最終埋め込みに対して線形層をかませて報酬を予測\
例) $r_\theta (x, y_{1}) = 0.8, \ r_\theta (x, y_{2}) = 0.5$
$$r_\theta (x, y) = {RewardModel}_\theta (concat (x, y)) \tag{1}$$
3. 報酬モデル$r_\theta (x, y)$の学習\
Bradley-Terryモデルなどから人間の選好を確率的にモデル化(式. 2)\
損失関数を最小化する(式. 3)\
$\sigma$はシグモイド関数、$y_{1}≻y_{2}$は$y_{1}$が$y_{2}$より好まれることを表す\
また、$D$は$P$を元に作った人間の比較したデータセット、$y_w$好まれる応答、$y_l$は劣る応答である
$$\begin{align}
P(y_{1}≻y_{2}) &= \frac{\exp(r(x,y_1))}{\exp(r(x,y_1)+\exp(r(x,y_2)} \tag{2} \\
\mathcal L_{BT} &= - \sum_{(x, y_w, y_l)\in D} \log \sigma(r_\theta(x,y_w)-r_\theta(x,y_l)) \tag{3}
\end{align}$$
4. 方策$\mathcal J(\theta)$の最適化\
強化学習の目的である**期待報酬を最大化**し、**元の方策から大きく離れない**ようにする\
実装においては、Proximal Policy Optimization(PPO)などが利用される\
$\pi_{ref}$は参照方策、$D_{KL}$はKLダイバージェンス、$\beta$は正則化の強さを制御するハイパーパラメータ
$$\mathcal J(\theta) = \mathbb E_{x~D, y~\pi_\theta(\cdot | x)} [r(x, y)] - \beta \cdot D_{KL} [\pi_\theta || \pi_{ref}] \tag{4}$$


回帰ヘッド … スカラー値を回帰する小さな出力ヘッド。値が微調整されていく？

参照方策 … 元のモデルの方策？

LLMにおける強化学習の基礎 - zenn
> https://zenn.dev/questlico/articles/4067769a826160

【LLM強化学習】RLHFとDPOについて理解したい！【ざっくりLLM解説】 - みうのAIテックブログ
> https://miu-ai-techblog.com/about_rlhf_dpo/

Bradley–Terry model - Wikipedia
> https://en.wikipedia.org/wiki/Bradley%E2%80%93Terry_model

## 環境の準備
docker install
> https://qiita.com/tf63/items/c21549ba44224722f301

add docker group
> https://qiita.com/tifa2chan/items/9dc28a56efcfb50c7fbe

docker command
> https://qiita.com/nimusukeroku/items/72bc48a8569a954c7aa2

安全でないLinux環境をどう用意するか\
-> サポート終了済みディストロ $\cap$ DockerHubからコンテナをクローン可
- centos6/7 2020/2024年にEOS
> https://hub.docker.com/_/centos

## どのような攻撃がなされているか
Trend MicroのクラウドのLinux環境への攻撃は、2022年時点ではWebベースの攻撃が9割強である\
Dos攻撃やデータの取得/改竄等が目的\
例) SQLインジェクション, クロスサイトスクリプティング etc\
非Web攻撃は3%程度。\
特定のアプリケーションプロトコルが狙われやすい\
例) SSH, FTP, SMTP etc
> https://www.trendmicro.com/vinfo/us/security/news/cybercrime-and-digital-threats/the-linux-threat-landscape-report

非サーバLinuxへの攻撃は、

侵入テスト用に使われるKali, black archのパッケージ/リポジトリにあるものは使う？
> https://www.kali.org/tools/ \
> https://blackarch.org/tools.html