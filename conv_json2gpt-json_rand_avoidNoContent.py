import json
import random

# 入出力ファイル名
mode = 1
if mode == 0:
    input_file = "jvn_results_wordpress202303.json"
    output_with_ids = "jvn_results_wordpress202303_randConv_.json"
    output_no_ids = "jvn_results_wordpress202303_randConv.json"
elif mode == 1:
    input_file = "jvn_results_wordpress202304.json"
    output_with_ids = "jvn_results_wordpress202304_randConv_.json"
    output_no_ids = "jvn_results_wordpress202304_randConv.json"
else:
    input_file = "jvn_results_php.json"
    output_with_ids = "jvn_results_php_randConv_.json"
    output_no_ids = "jvn_results_php_randConv.json"

# === Step 1. JSON読み込み ===
with open(input_file, "r", encoding="utf-8") as f:
    data = json.load(f)

converted = {}

# === Step 2. 出力テンプレートの定義 ===
templates = [
    "{title}等があります。{description} この問題の対象となるバージョンは{technologies}です。",
    "{title}があります。{description} 脆弱性を受けるアプリケーションは{technologies}です。",
    "{title}がある。{description} 問題になるソフトは{technologies}だ。",
    "{title}が存在する。{description} この問題を受けるアプリのバージョンは{technologies}である。",
    "{title}が確認されています。{description} 影響を受けるバージョンは{technologies}となっています。",
    "{title}が報告されています。{description} この脆弱性の対象バージョンは{technologies}です。",
    "{title}が見つかっています。{description} 該当する製品は{technologies}になります。",
    "{title}が指摘されています。{description} この影響範囲は{technologies}です。",
    "{title}が発見されました。{description} この問題が影響するのは{technologies}です。",
    "{title}が確認された。{description} 脆弱なのは{technologies}である。",
    "{title}が報告された。{description} この問題は{technologies}に影響する。",
    "{title}が見つかっている。{description} 対象バージョンは{technologies}だ。",
    "{title}の存在が判明した。{description} この問題は{technologies}で発生する。",
    "{title}が特定された。{description} この脆弱性に影響を受けるのは{technologies}である。",
    "{title}が明らかになった。{description} 該当するのは{technologies}のバージョンだ。",
    "{title}が確認された事例がある。{description} 影響範囲は{technologies}とされている。",
    "{title}が公開された。{description} 本脆弱性が影響するバージョンは{technologies}である。",
    "{title}が検出された。{description} この問題は{technologies}において再現する。",
    "{title}が登録されている。{description} 対象は{technologies}に分類される。",
    "{title}が観測されている。{description} 影響するソフトウェアは{technologies}である。",
    "{title}が発表された。{description} この脆弱性は{technologies}に影響を及ぼす。",
    "{title}の発生が確認された。{description} この影響は{technologies}にまで及ぶ。",
    "{title}っていう問題が出てるみたいです。{description} 影響するのは{technologies}らしいです。",
    "{title}があるっぽいです。{description} この問題の対象は{technologies}ってことみたいです。",
    "{title}が見つかったよ。{description} この問題が起きるのは{technologies}だって。",
    "{title}が起きているようです。{description} 該当するのは{technologies}とのことです。",
    "{title}が発生しているみたい。{description} この影響を受けるのは{technologies}みたいだね。",
]


# === Step 3. 各要素を human/gpt 形式に変換 ===
for jvn_id, info in data.items():

    title = info.get("title", "")
    description = info.get("description", "")
    technologies = info.get("technologies", "")

    # ★ ここで description が空欄ならスキップ
    if not description or not description.strip():
        continue

    # title_split 抽出
    if "における" in title:
        title_split = title.split("における", 1)[1].strip()
    else:
        title_split = title.strip()

    # ランダムテンプレート
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

# === Step 4. 出力保存 ===
no_id_list = list(converted.values())

with open(output_no_ids, "w", encoding="utf-8") as f:
    json.dump(no_id_list, f, ensure_ascii=False, indent=4)

print("✔ 変換が完了しました！")
print(f"└─ 出力: {output_no_ids}")
