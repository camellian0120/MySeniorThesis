import json
import random

# 入出力ファイル名
input_file = "jvn_results_wordpress202304.json"        # 変換前の元データ
output_with_ids = "jvn_results_wordpress202304_randConv_.json"       # JVNDBキー付きの変換結果
output_no_ids =  "jvn_results_wordpress202304_randConv.json"   # JVNDBキーを削除したリスト形式


# === Step 1. JSON読み込み ===
with open(input_file, "r", encoding="utf-8") as f:
    data = json.load(f)

converted = {}

# === Step 2. 出力テンプレートの定義 ===
templates = [
    "{title}等があります。{description} この問題の対象となるバージョンは{technologies}です。",
    "{title}があります。{description} 脆弱性を受けるアプリケーションは{technologies}です。",
    "{title}がある。{description} 問題になるソフトは{technologies}だ。",
    "{title}が存在する。{description} この問題を受けるアプリのバージョンは{technologies}である。"
]

# === Step 3. 各要素を human/gpt 形式に変換 ===
for jvn_id, info in data.items():
    title = info.get("title", "")
    description = info.get("description", "")
    technologies = info.get("technologies", "")

    # --- title_split抽出 ---
    # 「における」が含まれていれば、その後の部分を抽出
    if "における" in title:
        title_split = title.split("における", 1)[1].strip()
    else:
        # 念のためfallback（"における"がない場合）
        title_split = title.strip()

    # --- ランダムテンプレートを選択 ---
    template = random.choice(templates)

    new_value = {
        "instruction": f"{title_split}の例を教えて",
        "output": template.format(
            title_split=title_split,
            title=title,
            description=description,
            technologies=technologies
        )
    }

    converted[jvn_id] = new_value

# === Step 4. JVNDBキー付き形式を保存 ===
no_id_list = list(converted.values())

with open(output_no_ids, "w", encoding="utf-8") as f:
    json.dump(no_id_list, f, ensure_ascii=False, indent=4)

print("✔ 変換が完了しました！")
print(f"└─ 出力: {output_no_ids}")
