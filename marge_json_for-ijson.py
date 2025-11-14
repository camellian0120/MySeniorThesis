import json
import ijson
from multiprocessing import Process, Queue
from pathlib import Path
import sys

def worker(file_path, queue):
    """JSONファイルをストリーミング読み込みし、レコードをキューに流す"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            for item in ijson.items(f, "item"):
                queue.put(item)
    finally:
        queue.put(None)  # 終了シグナル

def merge_large_json_multiprocess(input_files, output_file):
    queue = Queue(maxsize=1000)  # バックプレッシャー用
    processes = []

    # ファイルごとにプロセスを起動
    for file in input_files:
        p = Process(target=worker, args=(file, queue))
        p.start()
        processes.append(p)

    finished_processes = 0
    first_item = True

    with open(output_file, "w", encoding="utf-8") as out:
        out.write("[\n")

        while finished_processes < len(processes):
            item = queue.get()

            if item is None:
                finished_processes += 1
                continue

            if not first_item:
                out.write(",\n")

            json.dump(item, out, ensure_ascii=False)
            first_item = False

        out.write("\n]\n")

    # 後片付け
    for p in processes:
        p.join()

    print(f"完了: {output_file} に {len(input_files)} ファイルをマルチプロセスでストリーミング結合しました")


if __name__ == "__main__":
    input_files = [
        "input1.json",
        "input2.json",
        "input3.json"
    ]
    output_file = "merged_multiprocess.json"

    merge_large_json_multiprocess(input_files, output_file)
