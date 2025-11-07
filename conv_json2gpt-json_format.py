import json

# 入出力ファイル名
input_file = "jvn_results_wordpress202304.json"        # 変換前の元データ
output_with_ids = "jvn_results_wordpress202304_conv.json"       # JVNDBキー付きの変換結果
output_no_ids =  "jvn_results_wordpress202304_conv_no-id.json"    # JVNDBキーを削除したリスト形式

# === Step 1. JSON読み込み ===
with open(input_file, "r", encoding="utf-8") as f:
    data = json.load(f)

converted = {}

# === Step 2. 各要素を human/gpt 形式に変換 ===
for jvn_id, info in data.items():
    title = info.get("title", "")
    description = info.get("description", "")
    technologies = info.get("technologies", "")

    new_value = {
            "instruction": f"{jvn_id} について教えてください",
            "output": f"{jvn_id} とは {title} のことです。{description} この脆弱性を受けるバージョンは {technologies} です"
        }

    converted[jvn_id] = new_value

# === Step 3. JVNDBキー付き形式を保存 ===
with open(output_with_ids, "w", encoding="utf-8") as f:
    json.dump(converted, f, ensure_ascii=False, indent=4)

# === Step 4. JVNDBキー削除版（リスト化）を作成 ===
no_id_list = list(converted.values())

with open(output_no_ids, "w", encoding="utf-8") as f:
    json.dump(no_id_list, f, ensure_ascii=False, indent=4)

print("✔ 変換が完了しました！")
print(f"├─ JVNDBキー付き出力: {output_with_ids}")
print(f"└─ JVNDBキー削除版出力: {output_no_ids}")
