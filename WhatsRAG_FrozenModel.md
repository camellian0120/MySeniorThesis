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
# RAG
## RAGとは何か
RAG(Retrieval-Augmented Generation)は、以下の流れで行われる**事前学習していない外部知識を検索して、その情報に基づいて文章を生成する手法**。
1. クエリを埋め込み表現にして、類似する情報をデータベースから検索。
2. 得られたコンテキストをプロンプトに追加。
3. LLMにプロンプトを入力し、推論。

![](./WhatsRAG-1.png)
図1. RAGの流れ

埋め込み表現(Embedding) …  単語や文章をベクトルに変換する操作

## 参考文献
RAGの概要【入門者向けの基礎知識】｜サクッと始めるRAG開発【LangChain / Python】
> https://zenn.dev/umi_mori/books/llm-rag-langchain-python/viewer/what-is-rag

■技術解説■ 生成AIのハルシネーションを低減するRAG。図表データまで特定できる"企業向けRAG"とは？（前編）
> https://blog-ja.allganize.ai/allganize_rag-1/

<br/>

# Frozen Model
## AutoRAG-LoRAより
> 実装では、凍結モデルのトークンとソフトマックス関数を使って
> $$P_{ret}(y) = softmax(f_{frozen} (x^′, D))$$

上記のように定数でない関数のように扱われている。

## Frozen Modelとは何か
Frozen Model/LLMとは、LLMのパラメータを固定したモデル/LLMのこと。\
理由が不明なものの、画像を使うマルチモーダルなLLMに凍結モデルを使うことがある。
![](./Flamingo_architecture.png)
図1. マルチモーダルなLLMの1つである、Flamingoのアーキテクチャ

<br/>

NTTドコモソリューションズ | エバンジェリストが語るICTの未来 | 生成AIの里 第四回：Promptがうまく言えなくて。。。：Pronto？Llama3、アンモナイトについて教えて！
> https://www.nttcom.co.jp/evangelist/column/kawamae_14/#section2

マルチモーダルLLMを理解する #生成AI - Qiita
> https://qiita.com/Dataiku/items/3e86c8012b2a7a7a3cf0#%E3%83%9E%E3%83%AB%E3%83%81%E3%83%A2%E3%83%BC%E3%83%80%E3%83%ABllm%E3%81%AE%E3%82%A2%E3%83%AB%E3%82%B4%E3%83%AA%E3%82%BA%E3%83%A0
