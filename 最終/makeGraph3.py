import matplotlib.pyplot as plt
import numpy as np

# ======================
# データ
# ======================
models = ["Base", "FT", "RAG"]
auc = [0.84, 0.92, 0.86]

x = np.arange(len(models))

# 最小値をデータに応じて設定（少し余裕を持たせる）
min_value = min(auc) - 0.04
min_value = max(0, min_value)

plt.figure(figsize=(12, 8))

bars = plt.bar(x, auc)

# ======================
# Y軸設定（0.05刻み）
# ======================
plt.ylim(min_value, 1.0)
plt.yticks(np.arange(min_value, 1.01, 0.05), fontsize=18)

plt.xticks(x, models, fontsize=18)
plt.ylabel("", fontsize=22)
plt.title("AUC", fontsize=26, pad=20)

plt.grid(axis="y", linestyle="--", alpha=0.6)

plt.tight_layout()
plt.show()
