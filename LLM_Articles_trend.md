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
# LLMの論文の傾向
## NeurIPS 2024
### LLM
1. InContext leaning(文脈内学習)
2. models/llms via(モデル/LLM経由) … 
3. Preference Optimization(嗜好最適化) … モデルを人間の嗜好に合わせる事
4. Prompt Optimization(プロンプト最適化)
5. LLM Agents
6. Code Generation

#### 考察
2024年のLLMのトレンドとしては多いのは、
1. 安全性 (有害な出力の抑制)
2. 性能向上 (InContext leaning, FT, Activation Steering等)

LLMに求められるものが性能が高いことは前提として、安全であることが求められている。

また、他分野との連携への利用として多いのは、
1. 医療
2. 数学

### 参考
NeurIPS 2024 poster (LLM)
> https://neurips2024.vizhub.ai/?brushed=%255B%255B291.3500061035156%252C-0.09167194366455078%255D%252C%255B558.8749389648438%252C226.43331909179688%255D%255D

## Qiita/Zenn (arXiv)
2024年最新LLM技術まとめ｜大規模言語モデルの研究動向とトレンド(随時更新予定) #生成AI - Qiita
> https://qiita.com/sergicalsix/items/84e4a2552e2245435540

arXivから2024年のLLMトレンド追ってみた - Zenn
> https://zenn.dev/mkj/articles/329499f577c728

### 考察_Qiita
計算量の削減やRAGの研究が行われている。\
また、RAGの研究に合わせて非常に長い入力(ロングコンテキスト)に関する研究も行われている。

### 考察_Zenn
LLMを別の分野で活用することに関して、音声処理/認識分野で活用が進んでいる。
主なトピックとしては、
1. マルチモーダル
2. 訓練の効率化
3. 攻撃手法/安全性
4. 医療への応用
5. 社会への影響
6. RAG
7. AIエージェント
8. 推論能力の向上

## 私見
RAGや計算量の削減による恩恵は小規模なLLMも享受できるため、研究のジャンルとして選択するか悩ましい。

