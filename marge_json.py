import json
from pathlib import Path

def merge_json_files(input_files, output_file):
    merged = []

    for file in input_files:
        with open(file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            merged.extend(data)

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(merged, f, ensure_ascii=False, indent=4)

    print(f"完了: {output_file} に {len(merged)} 件を書き込みました")


if __name__ == "__main__":
    # 結合したいファイルのパスを指定
    input_files = [
        "jvn_results_php_randConv.json",
        "jvn_results_wordpress202303_randConv.json",
        "jvn_results_wordpress202304_randConv.json"
    ]

    output_file = "jvn_results_merged.json"
    merge_json_files(input_files, output_file)
