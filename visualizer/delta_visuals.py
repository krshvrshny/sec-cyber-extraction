"""
10-K Quality Score Analysis – Delta Visualization Script
Produces 3 figures (2 main text + 1 appendix).

MAIN TEXT:
fig_delta_distribution.png  – pie chart of Δ value distribution
fig_delta_by_year.png       – stacked bar: Δ composition per year

APPENDIX:
figA_delta_by_sector.png    – stacked % bar: Δ distribution by sector

Requirements: pandas, matplotlib, seaborn, numpy
Usage: python delta_visuals.py
Input: delta_results.csv (same directory)
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
import numpy as np

# ── LOAD DATA ─────────────────────────────────────────────────────────────────
df = pd.read_csv("delta_results.csv")
df_delta = df.dropna(subset=["delta"])

SECTOR_ORDER = [
    "Semiconductors", "Healthcare", "Consumer Goods",
    "Retail & E-Commerce", "Finance", "Technology", "Cybersecurity"
]

# ── STYLE ─────────────────────────────────────────────────────────────────────
sns.set_theme(style="whitegrid", font_scale=1.15)
BLUE   = "#2E75B6"
ORANGE = "#ED7D31"
GRAY   = "#7F7F7F"
GREEN  = "#70AD47"

DELTA_COLORS = {0.0: GRAY, 0.5: ORANGE, 1.0: BLUE}
DELTA_LABELS = {0.0: "Δ=0.0  Stagnant Boilerplate",
                0.5: "Δ=0.5  Vague Minimalism",
                1.0: "Δ=1.0  Stable / Active Evolution"}

# ═════════════════════════════════════════════════════════════════════════════
# FIG – Δ Distribution (Pie) [MAIN TEXT]
# ═════════════════════════════════════════════════════════════════════════════
counts = df_delta["delta"].value_counts().sort_index()
labels = [DELTA_LABELS[v] for v in counts.index]
colors = [DELTA_COLORS[v] for v in counts.index]

fig, ax = plt.subplots(figsize=(8, 6))
wedges, texts, autotexts = ax.pie(
    counts.values,
    labels=labels,
    colors=colors,
    autopct="%1.1f%%",
    startangle=140,
    pctdistance=0.75,
    wedgeprops=dict(edgecolor="white", linewidth=1.5)
)
for t in autotexts:
    t.set_fontsize(11)
    t.set_fontweight("bold")

ax.set_title(
    "Figure – Dynamics Multiplier (Δ) Distribution\n"
    "(n=123 scored firm-year observations)",
    fontweight="bold"
)
plt.tight_layout()
plt.savefig("fig_delta_distribution.png", dpi=150, bbox_inches="tight")
plt.close()
print("Saved fig_delta_distribution.png")

# ═════════════════════════════════════════════════════════════════════════════
# FIG – Δ Composition by Year (Stacked Bar) [MAIN TEXT]
# ═════════════════════════════════════════════════════════════════════════════
year_delta = df_delta.groupby(["year", "delta"]).size().unstack(fill_value=0)
year_delta = year_delta.reindex(columns=[0.0, 0.5, 1.0], fill_value=0)
years = year_delta.index.tolist()
x = np.arange(len(years))
width = 0.5

fig, ax = plt.subplots(figsize=(9, 5))
bottom = np.zeros(len(years))
for delta_val in [0.0, 0.5, 1.0]:
    vals = year_delta[delta_val].values
    bars = ax.bar(x, vals, width, bottom=bottom,
                  color=DELTA_COLORS[delta_val], alpha=0.88,
                  edgecolor="white", label=DELTA_LABELS[delta_val])
    for i, (b, v) in enumerate(zip(bottom, vals)):
        if v > 0:
            ax.text(x[i], b + v / 2, str(int(v)),
                    ha="center", va="center", fontsize=9,
                    color="white", fontweight="bold")
    bottom += vals

ax.set_xticks(x)
ax.set_xticklabels(years)
ax.set_xlabel("Fiscal Year")
ax.set_ylabel("Number of Firm-Years")
ax.set_ylim(0, max(year_delta.sum(axis=1)) * 1.15)
ax.legend(fontsize=9, loc="upper left")
ax.set_title(
    "Figure – Δ Composition by Year (2022–2025)\n"
    "(Δ=0.0 concentrated in 2023; Δ=1.0 expands post-mandate)",
    fontweight="bold"
)
plt.tight_layout()
plt.savefig("fig_delta_by_year.png", dpi=150, bbox_inches="tight")
plt.close()
print("Saved fig_delta_by_year.png")

# ═════════════════════════════════════════════════════════════════════════════
# FIG A – Δ Distribution by Sector (Stacked % Bar) [APPENDIX]
# ═════════════════════════════════════════════════════════════════════════════
sec_delta = (
    df_delta.groupby(["sector", "delta"]).size()
    .unstack(fill_value=0)
    .reindex(columns=[0.0, 0.5, 1.0], fill_value=0)
)
sec_delta_pct = sec_delta.div(sec_delta.sum(axis=1), axis=0) * 100
sec_delta_pct = sec_delta_pct.reindex(SECTOR_ORDER)

fig, ax = plt.subplots(figsize=(11, 5))
bottom = np.zeros(len(sec_delta_pct))
for delta_val in [0.0, 0.5, 1.0]:
    vals = sec_delta_pct[delta_val].values
    ax.bar(np.arange(len(sec_delta_pct)), vals, width=0.55,
           bottom=bottom, color=DELTA_COLORS[delta_val], alpha=0.88,
           edgecolor="white", label=DELTA_LABELS[delta_val])
    for i, (b, v) in enumerate(zip(bottom, vals)):
        if v > 5:
            ax.text(i, b + v / 2, f"{v:.0f}%",
                    ha="center", va="center", fontsize=8.5,
                    color="white", fontweight="bold")
    bottom += vals

ax.set_xticks(np.arange(len(sec_delta_pct)))
ax.set_xticklabels(SECTOR_ORDER, rotation=15, ha="right")
ax.set_ylabel("Share (%)")
ax.set_ylim(0, 115)
ax.legend(fontsize=9, loc="upper right")
ax.set_title(
    "Figure A – Δ Distribution by Sector (%) [Appendix]\n"
    "(Cybersecurity highest Δ=1.0 share; Semiconductors lowest)",
    fontweight="bold"
)
plt.tight_layout()
plt.savefig("figA_delta_by_sector.png", dpi=150, bbox_inches="tight")
plt.close()
print("Saved figA_delta_by_sector.png")

print("\nAll delta outputs saved successfully.")
