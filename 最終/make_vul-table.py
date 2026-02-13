# Required libraries
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# Data
data = {
    "Model": ["base", "ft", "rag"],
    "recall": [0.824, 0.882, 0.824],
    "precision": [0.875, 0.938, 0.824],
    "auc": [0.84, 0.92, 0.86],
}

df = pd.DataFrame(data)

# Color definitions
ORANGE = "#F79428"
LIGHT_ORANGE = "#FDE3C3"
BLUE = "#5DADE2"
LIGHT_BLUE = "#D6EAF8"
BLACK = "black"

# Normalize numeric columns
numeric_cols = ["recall", "precision", "auc"]
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

# Create figure
fig, ax = plt.subplots(figsize=(7, 3))
ax.axis("off")

table = ax.table(
    cellText=display_df.values,
    colLabels=display_df.columns,
    cellColours=cell_colors,
    loc="center",
    cellLoc="center",
)

table.auto_set_font_size(False)
table.set_fontsize(13)
table.scale(1.2, 1.6)

# Explicitly bold AUC values for FT and RAG
celld = table.get_celld()

for i, model in enumerate(df["Model"]):
    if model in ["ft", "rag"]:
        row_position = i + 1  # +1 because row 0 is header
        col_position = 3  # AUC column index
        celld[(row_position, col_position)].get_text().set_weight("bold")
        celld[(row_position, col_position)].get_text().set_color(BLACK)

# Save image
output_path = "./vul-table.png"
plt.savefig(output_path, dpi=300, bbox_inches="tight", pad_inches=0.5)
plt.close(fig)

output_path
