# -*- coding: utf-8 -*-
from unsloth import FastLanguageModel
import transformers
import torch

import json
from pathlib import Path
from typing import List, Dict, Any
import os
import math

import pyarrow as pa
import lancedb
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
import numpy as np
import time

# ----------------------------
# Config
# ----------------------------
EMBED_MODEL = "./infloat_multilingual-e5-large/"
DB_PATH = "./LanceDB/rules.lancedb"
TABLE_NAME = "rules"
JSON_PATH = Path("./rspec_rules.json")
BATCH_SIZE = 256
USE_DEVICE = "cuda"

# モデルのロード
model, tokenizer = FastLanguageModel.from_pretrained(
    model_name = "unsloth/Qwen3-14B-unsloth-bnb-4bit",
    max_seq_length = 40960,
    load_in_4bit = False,
    load_in_8bit = False,
)

pipe = transformers.pipeline(
    'text-generation',
    model=model,
    tokenizer=tokenizer,
    max_new_tokens=1024,
    dtype=torch.float16
)

# LangChainのHuggingFacePipelineは非推奨の警告が出ることがあるため、
# 直接呼び出すか、必要な場合のみインポートしてください。
# ここではRAG部分で直接 generate を呼んでいるため llm 変数は必須ではありませんが、
# 念のため残す場合は transformers の pipeline をラップします。
# from langchain_huggingface import HuggingFacePipeline
# llm = HuggingFacePipeline(pipeline=pipe)

# ----------------------------
# 1) Embedding モデル
# ----------------------------
emb_model = HuggingFaceEmbeddings(
    model_name=EMBED_MODEL,
    model_kwargs={"device": USE_DEVICE},
    encode_kwargs={"normalize_embeddings": True},
)

def embed(text: str) -> List[float]:
    """E5 埋め込みを取得"""
    formatted = f"passage: {text}"
    emb = emb_model.embed_query(formatted)
    arr = np.asarray(emb, dtype=np.float32)
    return arr.tolist()

# ----------------------------
# 2) Splitter
# ----------------------------
splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=100,
    length_function=len,
)

# ----------------------------
# 3) LanceDB 接続 & schema 作成
# ----------------------------
db = lancedb.connect(DB_PATH)

if TABLE_NAME in db.table_names():
    print(f"テーブル {TABLE_NAME} が存在するため削除します...")
    db.drop_table(TABLE_NAME)

print("確認: 埋め込み次元を取得しています...")
sample_dim = len(embed("this is a sample"))
print("Embedding dim detected:", sample_dim)
EMB_DIM = sample_dim

# 【修正点1】 list_size=EMB_DIM を追加して固定長リストにする
schema = pa.schema([
    ("id", pa.string()),
    ("title", pa.string()),
    ("chunk", pa.string()),
    ("embedding", pa.list_(pa.float32(), list_size=EMB_DIM)), 
    ("url", pa.string()),
])

table = db.create_table(TABLE_NAME, schema=schema, mode="overwrite")
print(f"テーブル {TABLE_NAME} を作成しました。")

# ----------------------------
# 4) JSON 読み込みとデータ投入
# ----------------------------
if JSON_PATH.exists():
    with JSON_PATH.open("r", encoding="utf-8") as f:
        data = json.load(f)

    rows_to_insert = []
    
    print("データ処理を開始します...")
    for item in data:
        title = item["title"]
        description = item["description"]
        url = item.get("url", "")

        base_text = f"{title}\n\n{description}"
        chunks = splitter.split_text(base_text)

        for idx, ch in enumerate(chunks):
            if ch.strip() == title:
                continue
            
            emb = embed(ch)

            rows_to_insert.append({
                "id": f"{url}#{idx}",
                "title": title,
                "chunk": ch,
                "embedding": emb,
                "url": url
            })
            
            # 【修正点2】 メモリ節約のため一定数たまったらinsertしてリストをクリアする
            if len(rows_to_insert) >= BATCH_SIZE:
                table.add(rows_to_insert)
                print(f"✓ {len(rows_to_insert)} 件追加しました")
                rows_to_insert = [] # リセット

    # ループ終了後に残っているデータを追加
    if rows_to_insert:
        table.add(rows_to_insert)
        print(f"✓ 残りの {len(rows_to_insert)} 件を追加しました")

else:
    print(f"警告: {JSON_PATH} が見つかりません。ダミーデータなしで検索に進みます。")

# ----------------------------
# 5) 検索関数
# ----------------------------
def search(query: str, k: int = 5):
    formatted = f"query: {query}"
    query_emb = emb_model.embed_query(formatted)

    results = (
        table.search(query_emb)
        .metric("cosine")
        .limit(k)
        .to_list()
    )
    return results

# ----------------------------
# 6) コンテキスト生成と RAG
# ----------------------------
def build_context(docs: List[Dict[str, Any]]):
    parts = []
    for i, d in enumerate(docs):
        title = d.get("title", "")
        chunk = d.get("chunk", "")
        # LanceDBのバージョンによっては _distance だったり score だったりします
        score = d.get("_score", d.get("_distance", 0.0))
        parts.append(f"[{i+1}] (score={score:.4f}) {title}\n{chunk}")
    return "\n\n----\n\n".join(parts)

def rag_answer(question: str, k: int = 5):
    docs = search(question, k=k)
    
    # 検索結果デバッグ用
    # for d in docs:
    #     print(f"Found: {d['title']}")

    if not docs:
        print("関連ドキュメントが見つかりませんでした。")
        return

    context = build_context(docs)
    
    # プロンプト内の変数を適切に埋め込み
    system_prompt = """You are a white hat hacker tasked with discovering vulnerabilities in the provided source code.
Perform the following three actions on the source code below:
1. Identify the vulnerability
2. Present the risks of leaving it unaddressed
3. Provide a solution to eliminate the vulnerability

Ensure your output adheres to the following three points:
1. Output in Japanese
2. Be clear and concise
3. Use Markdown format"""

    user_message = f"""Answer based on the following context.
{context}

Question:
{question}
"""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message}
    ]

    text = tokenizer.apply_chat_template(
        messages,
        tokenize = False,
        add_generation_prompt = True,
    )

    from transformers import TextStreamer
    streamer = TextStreamer(tokenizer, skip_prompt=True)
    
    _ = model.generate(
        **tokenizer(text, return_tensors = "pt").to("cuda"),
        max_new_tokens = 4096,
        temperature = 0.6,
        top_p = 0.95,
        top_k = 20,
        streamer = streamer,
    )

# ----------------------------
# 7) 実行
# ----------------------------
if __name__ == "__main__":
    q = "Can anyone tell me about some dangerous implementations of php?"
    print("\nQUESTION:", q)
    print("\n=== ANSWER ===\n")
    rag_answer(q, k=5)
