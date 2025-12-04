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
    load_in_4bit = True,
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

# すでにテーブルがあるか確認
if TABLE_NAME in db.table_names():
    print(f"テーブル {TABLE_NAME} は既に存在します。ロードします...")
    table = db.open_table(TABLE_NAME)
else:
    print(f"テーブル {TABLE_NAME} が存在しないため、新規作成します...")

    print("確認: 埋め込み次元を取得しています...")
    sample_dim = len(embed("this is a sample"))
    print("Embedding dim detected:", sample_dim)
    EMB_DIM = sample_dim

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
# 4) JSON 読み込みとデータ投入 (重複回避版)
# ----------------------------
if JSON_PATH.exists():
    with JSON_PATH.open("r", encoding="utf-8") as f:
        data = json.load(f)

    # ★追加: 既にDBに入っているIDのセットを取得する
    existing_ids = set()
    if len(table) > 0:
        # 既存データをスキャンしてID列だけ取得
        # (データ量が数百万件など膨大な場合はメモリに注意が必要ですが、通常のRAGならこれで十分です)
        existing_ids = set(table.to_pandas()["id"].tolist())
        print(f"既存データ数: {len(existing_ids)} 件 - 重複はスキップします")

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
            
            # 今回生成するID
            unique_id = f"{url}#{idx}"

            # ★追加: IDが既にDBにあれば処理をスキップ
            if unique_id in existing_ids:
                continue
            
            # ここで初めてEmbedding計算（重い処理）を行うので、スキップ時は高速になります
            emb = embed(ch)

            rows_to_insert.append({
                "id": unique_id,
                "title": title,
                "chunk": ch,
                "embedding": emb,
                "url": url
            })
            
            if len(rows_to_insert) >= BATCH_SIZE:
                table.add(rows_to_insert)
                print(f"✓ {len(rows_to_insert)} 件追加しました")
                rows_to_insert = [] 

    if rows_to_insert:
        table.add(rows_to_insert)
        print(f"✓ 残りの {len(rows_to_insert)} 件を追加しました")
        
    if len(existing_ids) > 0 and len(rows_to_insert) == 0:
        print("新規に追加すべきデータはありませんでした。")

else:
    print(f"警告: {JSON_PATH} が見つかりません。")

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

def rag_answer(question: str, code: str, k: int = 5):
    docs = search(question, k=k)
    
    # 検索結果デバッグ用
    # for d in docs:
    #     print(f"Found: {d['title']}")

    if not docs:
        print("関連ドキュメントが見つかりませんでした。")
        return

    context = build_context(docs)
    
    # プロンプト内の変数を適切に埋め込み
    system_prompt = f"""You are a white hat hacker tasked with discovering vulnerabilities in the provided source code.
Perform the following three actions on the source code below:
1. Identify the vulnerability
2. Present the risks of leaving it unaddressed
3. Provide a solution to eliminate the vulnerability

Ensure your output adheres to the following three points:
1. Output in Japanese
2. Be clear and concise
3. Use Markdown format
"""

    user_message = f"""Detect vulnerabilities based on the following examples of dangerous syntax.
{context}

Question: {question}
---
{code}
"""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message}
    ]

    print("\nprompt:\n" + messages[0]["content"] +"\n"+ messages[1]["content"] +"\nanswer:\n")

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
    q = "What vulnerabilities are present in the following source code?"
    c = """
<?php
// create.php
require 'db.php';

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $title = $_POST['title'];
    $end_time = $_POST['end_time'];
    $options = $_POST['options']; // 配列として受け取る

    // バリデーション（空欄チェック）
    $valid_options = array_filter($options, function($v) { return trim($v) !== ''; });
    
    if ($title && $end_time && count($valid_options) >= 2) {
        // トランザクション開始
        $pdo->beginTransaction();
        try {
            // スレッド保存
            $stmt = $pdo->prepare("INSERT INTO polls (title, end_time) VALUES (?, ?)");
            $stmt->execute([$title, $end_time]);
            $poll_id = $pdo->lastInsertId();

            // 選択肢保存
            $stmt_opt = $pdo->prepare("INSERT INTO options (poll_id, name) VALUES (?, ?)");
            foreach ($valid_options as $opt_name) {
                $stmt_opt->execute([$poll_id, $opt_name]);
            }

            $pdo->commit();
            header("Location: index.php"); // メインへリダイレクト
            exit;
        } catch (Exception $e) {
            $pdo->rollBack();
            $error = "作成に失敗しました。";
        }
    } else {
        $error = "タイトル、終了時間、および2つ以上の選択肢を入力してください。";
    }
}
?>
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <title>スレッド作成</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <div class="header">
        <h1>新規スレッド作成</h1>
    </div>

    <?php if (isset($error)): ?>
        <p style="color: red;"><?= h($error) ?></p>
    <?php endif; ?>

    <form method="post" id="createForm">
        <div class="form-group">
            <label>タイトル</label>
            <input type="text" name="title" class="form-control" required placeholder="例: 好きなプログラミング言語は？">
        </div>

        <div class="form-group">
            <label>終了時間</label>
            <input type="datetime-local" name="end_time" class="form-control" required>
        </div>

        <div class="form-group">
            <label>選択肢 (2つ以上必須)</label>
            <div id="options-container">
                <input type="text" name="options[]" class="form-control" placeholder="選択肢 1" required style="margin-bottom:5px;">
                <input type="text" name="options[]" class="form-control" placeholder="選択肢 2" required style="margin-bottom:5px;">
            </div>
            <div class="add-option" onclick="addOption()">＋ 選択肢を追加する</div>
        </div>

        <div style="margin-top: 20px;">
            <button type="submit" class="btn btn-primary">作成する</button>
            <a href="index.php" class="btn btn-secondary">キャンセル</a>
        </div>
    </form>

    <script>
        function addOption() {
            const container = document.getElementById('options-container');
            const input = document.createElement('input');
            input.type = 'text';
            input.name = 'options[]';
            input.className = 'form-control';
            input.placeholder = '選択肢 ' + (container.children.length + 1);
            input.style.marginBottom = '5px';
            input.required = true;
            container.appendChild(input);
        }
    </script>
</body>
</html>

---
<?php
// db.php
try {
    // データベースファイルを作成/接続
    $pdo = new PDO('sqlite:voting_app.db');
    $pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);

    // スレッド（polls）テーブル作成
    $pdo->exec("CREATE TABLE IF NOT EXISTS polls (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        end_time DATETIME NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )");

    // 選択肢（options）テーブル作成
    $pdo->exec("CREATE TABLE IF NOT EXISTS options (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        poll_id INTEGER,
        name TEXT NOT NULL,
        votes INTEGER DEFAULT 0,
        FOREIGN KEY (poll_id) REFERENCES polls(id)
    )");

} catch (PDOException $e) {
    die("データベース接続エラー: " . $e->getMessage());
}

// XSS対策用関数
function h($str) {
    return htmlspecialchars($str, ENT_QUOTES, 'UTF-8');
}
?>

---
<?php
// index.php
require 'db.php';

// スレッド一覧を取得（終了時間が新しい順）
$stmt = $pdo->query("SELECT * FROM polls ORDER BY created_at DESC");
$polls = $stmt->fetchAll(PDO::FETCH_ASSOC);
?>
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <title>投票アプリ - メイン</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <div class="header">
        <h1>スレッド一覧</h1>
        <a href="create.php" class="btn btn-primary">＋ スレッド作成</a>
    </div>

    <div class="poll-list">
        <?php if (count($polls) === 0): ?>
            <p>現在スレッドはありません。</p>
        <?php else: ?>
            <?php foreach ($polls as $poll): ?>
                <?php 
                    $is_expired = new DateTime() > new DateTime($poll['end_time']);
                    $status_text = $is_expired ? '<span style="color:red">【終了】</span>' : '<span style="color:green">【受付中】</span>';
                ?>
                <a href="vote.php?id=<?= h($poll['id']) ?>" class="poll-link">
                    <div class="card">
                        <h2><?= $status_text ?> <?= h($poll['title']) ?></h2>
                        <div class="meta">終了日時: <?= h($poll['end_time']) ?></div>
                    </div>
                </a>
            <?php endforeach; ?>
        <?php endif; ?>
    </div>
</body>
</html>

---
<?php
// vote.php
require 'db.php';

$poll_id = $_GET['id'] ?? null;
if (!$poll_id) { header("Location: index.php"); exit; }

// スレッド情報の取得
$stmt = $pdo->prepare("SELECT * FROM polls WHERE id = ?");
$stmt->execute([$poll_id]);
$poll = $stmt->fetch(PDO::FETCH_ASSOC);

if (!$poll) { die("スレッドが見つかりません"); }

// 選択肢情報の取得
$stmt = $pdo->prepare("SELECT * FROM options WHERE poll_id = ?");
$stmt->execute([$poll_id]);
$options = $stmt->fetchAll(PDO::FETCH_ASSOC);

// 状態判定
$cookie_name = "voted_poll_" . $poll_id;
$has_voted = isset($_COOKIE[$cookie_name]);
$is_expired = new DateTime() > new DateTime($poll['end_time']);
$show_results = $has_voted || $is_expired;

// 投票処理（POST時）
if ($_SERVER['REQUEST_METHOD'] === 'POST' && !$show_results) {
    $option_id = $_POST['option_id'];
    
    // 投票数を加算
    $stmt = $pdo->prepare("UPDATE options SET votes = votes + 1 WHERE id = ? AND poll_id = ?");
    $stmt->execute([$option_id, $poll_id]);

    // Cookieをセット（有効期限30日）
    setcookie($cookie_name, '1', time() + (86400 * 30), "/");
    
    // 再読み込みして結果を表示
    header("Location: vote.php?id=" . $poll_id);
    exit;
}

// 総投票数の計算（割合表示用）
$total_votes = 0;
foreach ($options as $opt) { $total_votes += $opt['votes']; }
?>
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <title><?= h($poll['title']) ?> - 投票</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <div class="header">
        <h1>投票画面</h1>
        <a href="index.php" class="btn btn-secondary">← 一覧に戻る</a>
    </div>

    <div class="card">
        <h2><?= h($poll['title']) ?></h2>
        <p class="meta">終了期限: <?= h($poll['end_time']) ?></p>
        
        <?php if ($is_expired && !$has_voted): ?>
            <p style="color: red;">※ この投票は終了しました。</p>
        <?php elseif ($has_voted): ?>
            <p style="color: green;">※ 投票済みです。</p>
        <?php endif; ?>

        <hr>

        <?php if ($show_results): ?>
            <h3>現在の投票結果（総数: <?= $total_votes ?>票）</h3>
            <?php foreach ($options as $opt): ?>
                <?php 
                    $percent = $total_votes > 0 ? round(($opt['votes'] / $total_votes) * 100) : 0;
                ?>
                <div style="margin-bottom: 15px;">
                    <div><?= h($opt['name']) ?> (<?= $opt['votes'] ?>票)</div>
                    <div class="result-bar-bg">
                        <div class="result-bar-fill" style="width: <?= $percent ?>%;"></div>
                        <div class="result-text"><?= $percent ?>%</div>
                    </div>
                </div>
            <?php endforeach; ?>

        <?php else: ?>
            <form method="post">
                <?php foreach ($options as $opt): ?>
                    <button type="submit" name="option_id" value="<?= $opt['id'] ?>" class="btn btn-vote">
                        <?= h($opt['name']) ?> に投票する
                    </button>
                <?php endforeach; ?>
            </form>
        <?php endif; ?>
    </div>
</body>
</html>

---
/* style.css */
body { font-family: sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; background-color: #f9f9f9; }
h1, h2 { color: #333; }
.header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; border-bottom: 2px solid #ddd; padding-bottom: 10px; }
.btn { padding: 10px 20px; text-decoration: none; border-radius: 5px; border: none; cursor: pointer; display: inline-block; }
.btn-primary { background-color: #007bff; color: white; }
.btn-secondary { background-color: #6c757d; color: white; margin-left: 10px; }
.btn-vote { background-color: #28a745; color: white; width: 100%; margin-top: 5px; padding: 15px; font-size: 16px; }
.card { background: white; border: 1px solid #ddd; padding: 15px; margin-bottom: 10px; border-radius: 5px; }
.card:hover { box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
.poll-link { text-decoration: none; color: inherit; display: block; }
.meta { font-size: 0.85em; color: #666; margin-top: 5px; }
.form-group { margin-bottom: 15px; }
.form-group label { display: block; margin-bottom: 5px; font-weight: bold; }
.form-control { width: 100%; padding: 10px; box-sizing: border-box; }
.result-bar-bg { background: #e9ecef; border-radius: 5px; height: 25px; margin-top: 5px; position: relative; }
.result-bar-fill { background-color: #007bff; height: 100%; border-radius: 5px; transition: width 0.3s; }
.result-text { position: absolute; left: 10px; top: 2px; font-size: 0.9em; color: #000; font-weight: bold;}
.add-option { margin-top: 5px; font-size: 0.9em; color: #007bff; cursor: pointer; text-decoration: underline; }
"""
    rag_answer(q, c, k=5)
