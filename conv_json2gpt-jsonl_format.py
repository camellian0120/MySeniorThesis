import json

# 入出力ファイル名（必要に応じて変更）
input_file = "jvn_results_wordpress202304.json"        # 変換前の元データ
output_file = "jvn_results_wordpress202304_conv.jsonl"     # 最終的な出力（1行1件）

# === Step 1. JSON読み込み ===
with open(input_file, "r", encoding="utf-8") as f:
    data = json.load(f)

converted = {}

# === Step 2. 各要素を新形式に変換 ===
for jvn_id, info in data.items():
    title = info.get("title", "")
    description = info.get("description", "")
    technologies = info.get("technologies", "")

    # 新しい形式
    new_value = [
        {
            "from": "human",
            "value": f"{jvn_id} について教えてください"
        },
        {
            "from": "gpt",
            "value": f"{jvn_id} とは {title} のことです。{description} この脆弱性を受けるバージョンは {technologies} です"
        }
    ]

    converted[jvn_id] = new_value

# === Step 3. "messages"にリネームして1件ずつJSONLとして出力 ===
with open(output_file, "w", encoding="utf-8") as f:
    for key, messages in converted.items():
        json.dump({"messages": messages}, f, ensure_ascii=False)
        f.write("\n")

print("変換と分割が完了しました！出力ファイル:", output_file)
