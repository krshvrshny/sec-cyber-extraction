"""
Function Weights Visualizations
================================
Fig 1 : Average function weights across corpus (bar chart)
Fig 2 : Function weights over time (stacked area)
Fig 3 : Function weights by sector (heatmap)
Fig 4 : Function weights by firm size (grouped bar)
"""

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import seaborn as sns
from pathlib import Path

os.chdir(os.path.dirname(os.path.abspath(__file__)))

INPUT_FILE = os.path.join("..", "results", "nist_csf_scores.csv")
OUTPUT_DIR = os.path.join("..", "visuals", "function_weights")

FUNCTIONS   = ["GV", "ID", "PR", "DE", "RS", "RC"]
FUNC_LABELS = {"GV":"Govern","ID":"Identify","PR":"Protect",
               "DE":"Detect","RS":"Respond","RC":"Recover"}
FUNC_COLORS = {"GV":"#2C5F8A","ID":"#4A90C4","PR":"#5BB56E",
               "DE":"#E8A838","RS":"#D95F3B","RC":"#8B5EA6"}

SIZE_MAP = {
    "AAPL":"Large","MSFT":"Large","GOOGL":"Large","AMZN":"Large",
    "JNJ":"Large","LLY":"Large","NKE":"Large","PEP":"Large",
    "V":"Large","AMD":"Large","INTC":"Large","CRWD":"Large",
    "PANW":"Large","MOH":"Large",
    "CROX":"Mid","ELF":"Mid","WGO":"Mid","MCFT":"Mid",
    "PRGS":"Mid","RPD":"Mid","S":"Mid","VRNS":"Mid",
    "HLI":"Mid","LC":"Mid","UPST":"Mid","ELMD":"Mid",
    "MODD":"Mid","VKTX":"Mid","BOOT":"Mid","ETSY":"Mid",
    "SFIX":"Mid","UPWK":"Mid","CRUS":"Mid","MXL":"Mid",
    "POWI":"Mid","AMPL":"Mid","GTLB":"Mid","SCSC":"Mid","U":"Mid",
    "PSEC":"Small","NVEC":"Small",
}
SIZE_ORDER  = ["Large", "Mid", "Small"]
SIZE_COLORS = {"Large":"#2C5F8A","Mid":"#5BB56E","Small":"#E8A838"}

plt.rcParams.update({
    "font.family":"serif","font.size":11,
    "axes.titlesize":13,"axes.titleweight":"bold",
    "axes.spines.top":False,"axes.spines.right":False,
    "figure.dpi":150,
})

Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

# Load
df     = pd.read_csv(INPUT_FILE)
w_cols = [f"w_{f}" for f in FUNCTIONS]
df["size"]   = df["ticker"].map(SIZE_MAP).fillna("Mid")
df_valid     = df[df["total_keyword_hits"] > 0].copy()
print(f"Loaded {len(df)} filings | Valid: {len(df_valid)}")

def save(name):
    plt.savefig(os.path.join(OUTPUT_DIR, f"{name}.png"), bbox_inches="tight")
    plt.close()
    print(f"Saved {name}")

# =============================================================================
# FIGURE 1 — Average Function Weights (bar chart)
# =============================================================================
mean_weights = df_valid[w_cols].mean().values
fig, ax = plt.subplots(figsize=(8, 4.5))
bars = ax.bar([FUNC_LABELS[f] for f in FUNCTIONS], mean_weights,
              color=[FUNC_COLORS[f] for f in FUNCTIONS], edgecolor="white")
ax.axhline(1/6, color="grey", linewidth=1.2, linestyle="--", alpha=0.7,
           label="Uniform benchmark (1/6)")
for bar, val in zip(bars, mean_weights):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.005,
            f"{val:.2%}", ha="center", va="bottom", fontsize=9)
ax.yaxis.set_major_formatter(mtick.PercentFormatter(xmax=1))
ax.set_ylabel("Mean Keyword Weight $w_f$")
ax.set_title("Average Disclosure Weight per NIST CSF Function")
ax.legend(frameon=False)
plt.tight_layout()
save("fw_mean_weights")

# =============================================================================
# FIGURE 2 — Function Weights Over Time (stacked area)
# =============================================================================
if "year" in df.columns and df["year"].nunique() > 1:
    yearly_w = df_valid.groupby("year")[w_cols].mean().reset_index()
    years    = yearly_w["year"].values
    bottom   = np.zeros(len(years))
    fig, ax  = plt.subplots(figsize=(9, 5))
    for f in FUNCTIONS:
        vals = yearly_w[f"w_{f}"].values
        ax.fill_between(years, bottom, bottom + vals,
                        alpha=0.85, color=FUNC_COLORS[f], label=FUNC_LABELS[f])
        bottom += vals
    ax.set_xlim(years[0], years[-1])
    ax.set_ylim(0, 1)
    ax.yaxis.set_major_formatter(mtick.PercentFormatter(xmax=1))
    ax.set_xlabel("Year")
    ax.set_ylabel("Proportional Keyword Weight")
    ax.set_title("Thematic Composition of Disclosures Over Time")
    ax.legend(loc="upper left", frameon=False, fontsize=9,
              ncol=2, bbox_to_anchor=(1.01, 1))
    ax.xaxis.set_major_locator(plt.MaxNLocator(integer=True))
    plt.tight_layout()
    save("fw_over_time")

# =============================================================================
# FIGURE 3 — Function Weights by Sector (heatmap)
# =============================================================================
sectors        = sorted(df_valid["sector"].dropna().unique())
sector_weights = (df_valid.groupby("sector")[w_cols]
                          .mean()
                          .rename(columns={f"w_{f}": FUNC_LABELS[f] for f in FUNCTIONS}))
fig, ax = plt.subplots(figsize=(9, max(4, len(sectors) * 0.6 + 1)))
sns.heatmap(sector_weights, ax=ax, cmap="YlOrRd", annot=True, fmt=".2f",
            linewidths=0.5, linecolor="white",
            cbar_kws={"label":"Mean $w_f$","shrink":0.7},
            vmin=0, vmax=sector_weights.values.max())
ax.set_title("Mean Function Weights by Sector")
ax.set_xlabel(""); ax.set_ylabel("")
ax.tick_params(axis="x", rotation=0)
ax.tick_params(axis="y", rotation=0)
plt.tight_layout()
save("fw_by_sector")

# =============================================================================
# FIGURE 4 — Function Weights by Firm Size (grouped bar)
# =============================================================================
x     = np.arange(len(FUNCTIONS))
width = 0.25
fig, ax = plt.subplots(figsize=(10, 5))
for i, s in enumerate(SIZE_ORDER):
    vals   = df_valid[df_valid["size"] == s][w_cols].mean().values
    offset = (i - 1) * width
    bars   = ax.bar(x + offset, vals, width, label=f"{s} Cap",
                    color=SIZE_COLORS[s], alpha=0.85, edgecolor="white")
    for bar, val in zip(bars, vals):
        if val > 0.015:
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.004,
                    f"{val:.1%}", ha="center", va="bottom", fontsize=7)
ax.axhline(1/6, color="grey", linewidth=1.2, linestyle="--", alpha=0.6,
           label="Uniform benchmark (1/6)")
ax.set_xticks(x)
ax.set_xticklabels([FUNC_LABELS[f] for f in FUNCTIONS])
ax.yaxis.set_major_formatter(mtick.PercentFormatter(xmax=1))
ax.set_ylabel("Mean Keyword Weight $w_f$")
ax.set_title("Function Weights by Firm Size")
ax.legend(frameon=False)
plt.tight_layout()
save("fw_weights_by_size")

print("\nAll function weight figures saved.")