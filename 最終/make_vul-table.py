# Required libraries
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# Data
data = {
    "Model": ["Base", "FT", "RAG"],
    "Recall": [0.824, 0.882, 0.824],
    "Precision": [0.875, 0.938, 0.824],
    "AUC": [0.84, 0.92, 0.86],
}

df = pd.DataFrame(data)

# Color definitions
BLUE = "#5DADE2"
LIGHT_BLUE = "#D6EAF8"
BLACK = "black"

# Normalize numeric columns
numeric_cols = ["Recall", "Precision", "AUC"]
norm_df = (df[numeric_cols] - df[numeric_cols].min()) / (
    df[numeric_cols].max() - df[numeric_cols].min()
)

# Create color matrix
cell_colors = []

for i in range(len(df)):
    row_colors = ["white"]
    for col in numeric_cols:
        value = norm_df.loc[i, col]
        color = LIGHT_BLUE if value < 0.5 else BLUE
        row_colors.append(color)
    cell_colors.append(row_colors)

# Round numeric values for display
display_df = df.copy()
for col in numeric_cols:
    display_df[col] = display_df[col].round(3)

# ===== Create figure (larger & no margins) =====
fig, ax = plt.subplots(figsize=(8, 1.5))
ax.axis("off")

# Remove ALL padding around axes
plt.subplots_adjust(left=0, right=1, top=1, bottom=0)

table = ax.table(
    cellText=display_df.values,
    colLabels=display_df.columns,
    cellColours=cell_colors,
    loc="center",
    cellLoc="center",
)

# ===== Bigger text =====
table.auto_set_font_size(False)
table.set_fontsize(24)      # ← 文字サイズ大幅アップ
table.scale(1.4, 2.5)       # ← 行・列も拡大

# Bold AUC values for FT and RAG
celld = table.get_celld()

celld[(2, 3)].get_text().set_weight("bold")
celld[(3, 3)].get_text().set_weight("bold")

# Save image (NO padding)
output_path = "./vul-table2.png"
plt.savefig(output_path, dpi=300, bbox_inches="tight", pad_inches=0)
plt.close(fig)

output_path
