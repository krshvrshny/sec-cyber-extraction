"""
10-K Quality Score Analysis – Quality Score Visualization Script
Produces 3 main text figures + 2 appendix figures.

MAIN TEXT:
fig_quality_by_year.png     – mean quality score over time with jittered dots
fig_quality_by_sector.png   – mean quality score by sector (bar + SD)
fig_quality_by_1c.png       – quality score: Item 1C adopters vs non-adopters

APPENDIX:
figA_quality_by_size.png    – quality score boxplot by firm size
figA_quality_heatmap.png    – heatmap: all firms × all years

Requirements: pandas, matplotlib, seaborn, numpy
Usage: python quality_visuals.py
Input: quality_results.csv (same directory)
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import os

# ── PATHS ─────────────────────────────────────────────────────────────────────
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(SCRIPT_DIR, "..", "visuals", "quality")
os.makedirs(OUTPUT_DIR, exist_ok=True)

def out(filename):
    return os.path.join(OUTPUT_DIR, filename)

# ── LOAD DATA ─────────────────────────────────────────────────────────────────
df = pd.read_csv(os.path.join(SCRIPT_DIR, "..", "results", "quality_results.csv"))
df_scored = df.dropna(subset=["quality_score"])

SECTOR_ORDER = [
    "Semiconductors", "Healthcare", "Consumer Goods",
    "Retail & E-Commerce", "Finance", "Technology", "Cybersecurity"
]
SIZE_ORDER = ["Small", "Medium", "Large"]

# ── STYLE ─────────────────────────────────────────────────────────────────────
sns.set_theme(style="whitegrid", font_scale=1.15)
BLUE   = "#2E75B6"
ORANGE = "#ED7D31"
GRAY   = "#7F7F7F"
GREEN  = "#70AD47"

np.random.seed(42)

# ═════════════════════════════════════════════════════════════════════════════
# FIG – Mean Quality Score by Year with Jittered Firm Dots [MAIN TEXT]
# ═════════════════════════════════════════════════════════════════════════════
yearly = df_scored.groupby("year")["quality_score"].agg(["mean", "std"]).reset_index()

fig, ax = plt.subplots(figsize=(9, 5))

for year in sorted(df_scored["year"].unique()):
    vals = df_scored[df_scored["year"] == year]["quality_score"].values
    jitter = np.random.uniform(-0.08, 0.08, size=len(vals))
    ax.scatter(np.full(len(vals), year) + jitter, vals,
               color=BLUE, alpha=0.25, s=22, zorder=2)

ax.fill_between(
    yearly["year"],
    (yearly["mean"] - yearly["std"]).clip(lower=0),
    (yearly["mean"] + yearly["std"]).clip(upper=100),
    color=BLUE, alpha=0.15, label="±1 SD"
)

ax.plot(yearly["year"], yearly["mean"],
        marker="o", color=BLUE, lw=2.5, zorder=3, label="Mean score")

for _, row in yearly.iterrows():
    ax.annotate(f'{row["mean"]:.1f}',
                xy=(row["year"], row["mean"]),
                xytext=(0, 12), textcoords="offset points",
                ha="center", fontsize=10)

ax.set_xticks([2023, 2024, 2025])
ax.set_xlabel("Fiscal Year")
ax.set_ylabel("Quality Score (0–100)")
ax.set_ylim(-5, 110)
ax.legend(fontsize=10)
ax.set_title(
    "Mean Quality Score Over Time (2023–2025)",
    fontweight="bold"
)
plt.tight_layout()
plt.savefig(out("quality_by_year.png"), dpi=150, bbox_inches="tight")
plt.close()
print("Saved quality_by_year.png")

# ═════════════════════════════════════════════════════════════════════════════
# FIG – Mean Quality Score by Sector (Horizontal Bar + SD) [MAIN TEXT]
# ═════════════════════════════════════════════════════════════════════════════
sec = df_scored.groupby("sector")["quality_score"].agg(["mean", "std"]).reindex(SECTOR_ORDER)

fig, ax = plt.subplots(figsize=(10, 5))
ax.barh(sec.index, sec["mean"],
        xerr=sec["std"], color=BLUE, alpha=0.82,
        edgecolor="white", height=0.55,
        error_kw=dict(ecolor=GRAY, capsize=4, lw=1.3))

for i, (idx, row) in enumerate(sec.iterrows()):
    ax.text(row["mean"] + row["std"] + 1.5, i,
            f'{row["mean"]:.1f}', va="center", fontsize=9.5)

ax.set_xlabel("Mean Quality Score (0–100)")
ax.set_xlim(0, 105)
ax.axvline(df_scored["quality_score"].mean(), color=ORANGE, ls="--", lw=1.5,
           label=f'Overall mean = {df_scored["quality_score"].mean():.1f}')
ax.legend(fontsize=10)
ax.set_title(
    "Mean Quality Score by Sector",
    fontweight="bold"
)
plt.tight_layout()
plt.savefig(out("quality_by_sector.png"), dpi=150, bbox_inches="tight")
plt.close()
print("Saved quality_by_sector.png")

# ═════════════════════════════════════════════════════════════════════════════
# FIG – Quality Score: Item 1C Adopters vs Non-Adopters [MAIN TEXT]
# ═════════════════════════════════════════════════════════════════════════════
q_1c = df_scored.groupby("has_1c")["quality_score"].agg(["mean", "std"]).reset_index()
q_1c["label"] = q_1c["has_1c"].map({True: "With Item 1C", False: "Without Item 1C"})

x = np.arange(len(q_1c))
width = 0.4
colors = [GRAY, BLUE]

fig, ax = plt.subplots(figsize=(7, 5))
bars = ax.bar(x, q_1c["mean"], width,
              yerr=q_1c["std"], color=colors, alpha=0.85,
              edgecolor="white",
              error_kw=dict(ecolor=GRAY, capsize=5, lw=1.3))

for bar, val in zip(bars, q_1c["mean"]):
    ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 3,
            f'{val:.1f}', ha="center", va="bottom", fontsize=11, fontweight="bold")

ax.set_xticks(x)
ax.set_xticklabels(q_1c["label"])
ax.set_ylabel("Mean Quality Score (0–100)")
ax.set_ylim(0, 85)
ax.set_title(
    "Quality Score: Item 1C Adopters vs Non-Adopters\n"
    "(error bars = ±1 SD)",
    fontweight="bold"
)
plt.tight_layout()
plt.savefig(out("quality_by_1c.png"), dpi=150, bbox_inches="tight")
plt.close()
print("Saved quality_by_1c.png")

# ═════════════════════════════════════════════════════════════════════════════
# FIG A – Quality Score Boxplot by Firm Size [APPENDIX]
# ═════════════════════════════════════════════════════════════════════════════
size_means = df_scored.groupby("size")["quality_score"].mean()

fig, ax = plt.subplots(figsize=(8, 5))
sns.boxplot(data=df_scored, x="size", y="quality_score", order=SIZE_ORDER,
            color=BLUE, ax=ax,
            flierprops=dict(marker=".", markersize=5, alpha=0.5))

for i, sz in enumerate(SIZE_ORDER):
    ax.text(i, size_means[sz] + 3,
            f'Mean\n{size_means[sz]:.1f}',
            ha="center", va="bottom", fontsize=9)

ax.set_xlabel("Firm Size")
ax.set_ylabel("Quality Score (0–100)")
ax.set_ylim(-5, 120)
ax.set_title(
    "Quality Score by Firm Size [Appendix]",
    fontweight="bold"
)
plt.tight_layout()
plt.savefig(out("quality_by_size.png"), dpi=150, bbox_inches="tight")
plt.close()
print("Saved quality_by_size.png")

# ═════════════════════════════════════════════════════════════════════════════
# FIG A – Heatmap: All Firms × All Years [APPENDIX]
# ═════════════════════════════════════════════════════════════════════════════
pivot = df_scored.pivot_table(index="ticker", columns="year", values="quality_score")
pivot = pivot.sort_values(by=sorted(pivot.columns))

fig, ax = plt.subplots(figsize=(7, 13))
sns.heatmap(pivot, ax=ax, annot=True, fmt=".0f", cmap="Blues",
            linewidths=0.4, linecolor="#e0e0e0",
            cbar_kws={"label": "Quality Score (0–100)", "shrink": 0.6},
            vmin=0, vmax=100,
            annot_kws={"size": 8})

ax.set_xlabel("Fiscal Year")
ax.set_ylabel("")
ax.set_title(
    "Quality Score by Firm and Year",
    fontweight="bold"
)
plt.tight_layout()
plt.savefig(out("quality_heatmap.png"), dpi=150, bbox_inches="tight")
plt.close()
print("Saved quality_heatmap.png")

print("\nAll quality score outputs saved successfully.")