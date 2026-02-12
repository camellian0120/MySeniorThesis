import matplotlib.pyplot as plt
import numpy as np

# ======================
# データ
# ======================
models = ["Base", "FT", "RAG"]
recall = [0.824, 0.882, 0.824]
precision = [0.875, 0.938, 0.824]

# ======================
# グラフ設定
# ======================
x = np.arange(len(models))
width = 0.35

# 最小値をデータに応じて設定（少し余裕を持たせる）
min_value = min(recall + precision) - 0.05
min_value = max(0, min_value)  # 0未満にしない

plt.figure(figsize=(12, 8))

# 棒グラフ
bars1 = plt.bar(x - width/2, recall, width, label="Recall")
bars2 = plt.bar(x + width/2, precision, width, label="Precision")

# ======================
# 見やすさ向上設定
# ======================
plt.ylim(min_value, 1.0)
plt.xticks(x, models, fontsize=18)
plt.yticks(fontsize=18)
plt.ylabel("", fontsize=22)
plt.title("Recall / Precision", fontsize=26, pad=20)

plt.grid(axis="y", linestyle="--", alpha=0.6)
plt.legend(fontsize=18)

plt.tight_layout()
plt.show()
