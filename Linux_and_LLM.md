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
- Linuxへの攻撃者の行動データを探す\
 -> 攻撃者がよく使うコマンドから攻撃の有無を調べるため(nmap, curl, wget等？)

- Linuxの仮想環境でLLMにシェルやGUIを使わせてみる\
 -> LLMが応答生成の際に何をしているか、PCとの相互作用をしているか調べる

- マルチノード環境の最適化\
 -> 複数の端末を利用して行う計算のプログラムをLLMに作らせ、修正させていく

1. LLMで強化学習をする方法、どう使われているか
1. 環境の準備(Docker, 脆弱性あり)
1. どのような環境を作るのが望ましいか、どんな攻撃をかけているのか
1. 報酬付け(suを取れたら等)

<br/>

## 攻撃者のよく使うコマンドは？そのデータセットは？
### 攻撃の流れから見るよく使うもの
1. 攻撃対象の発見\
システム検索: nmap, arp
2. 防御回避\
サービスの停止: systemctl stop\
モジュール確認: lsmod
3. 権限昇格\
パスワード確認: cat /etc/shadow\
特権ユーザ確認: cat /stc/sudoers
4. 攻撃\
C&C: wget, curl\
モジュールのロード: modprobe, insmod

### Dataset: Shell Commands Used by Participants of Hands-on Cybersecurity Training
nmap, set, ssh/scp, fcrackzip等
> https://www.sciencedirect.com/science/article/pii/S2352340921006806

上記のデータ/解析ツール
> https://zenodo.org/records/5517479

### OS Command Injection Dataset
Windows+Linux
> https://www.kaggle.com/datasets/sanketpawase/os-command-injection

### CICAPT-IIoT: A Provenance-Based APT Attack Dataset for IIoT Environment
IoT向けLinux環境(RaspberryPi/Ubuntu等)でのAPT(高度な持続的脅威)検知用のデータセット
> https://arxiv.org/html/2407.11278v1

---

### SSHセッションにおけるLinuxコマンドのリスクレベルによる分類
コマンドのリスクレベルを推定することを目的とした機械学習ワークフロー
> https://www.kaggle.com/datasets/thuyngandao/bashlogs

論文
> https://pure.unamur.be/ws/portalfiles/portal/53931631/2020_DaoThuyN_memoire.pdf

```md
攻撃者からハニーポットへ送信されるコマンドのリスクを自動推定

コマンドのリスクを2手法で考えた
1.  通常(0)/危険(1)の2値分類
2.  5段階(R0~R4)の多クラス分類問題

セータセットの自動データラベリングに課題あり
```

---

### Linux-APT-Dataset-2024
一般的なアクティビティと疑わしいアクティビティが混在するデータセット\
シミュレートされた攻撃は、CVE、キーロガー、APT
> https://zenodo.org/records/10685642

### harpomaxx/unix-commands - huggingface
全てのユースケースのユーザのコマンド履歴
> https://huggingface.co/datasets/harpomaxx/unix-commands

### Awesome-Cybersecurity-Datasets
セキュリティデータセット置き場\
Linux関連は"The ADFA Intrusion Detection Datasets"位
> https://github.com/shramos/Awesome-Cybersecurity-Datasets

<br/>

## LLMは応答生成の際に検証をしているか？
ソースコードが実行可能な状態かの確認\
-> 不明

ソースコードの脆弱性に関する確認\
-> してない？

```
GPT-4oが生成したコードに対して脆弱性診断を行った結果、いくつかの脆弱性が検出されました。
```

コード生成AIは安全か？LLMアプリのセキュリティ検証を実施してみた - zenn
> https://zenn.dev/chillstack/articles/2025-04-22-llm-web-diagnosis

## LLM+terminal
フロントエンドにllmへのチャットとターミナルの機能を備えるターミナルエミュレータ
1. Warp
> https://www.warp.dev/
2. almightty
> https://www.almightty.org/

terminal上でLLMにコマンドを生成/実行してもらうプロジェクト
1. sgpt … コードの生成/実行の有無の決定
> https://github.com/TheR1D/shell_gpt
2. llm-term … sgpt同様
> https://www.reddit.com/r/commandline/comments/1f4e0nu/llmterm_a_simple_terminal_assistant/?tl=ja

以下の繰り返しの流れは、まだあまりなさそう？
1. ユーザが行いたい作業を入力
2. llmが応答を生成/実行
3. 実行結果を次の入力に
4. 2~3を繰り返す

