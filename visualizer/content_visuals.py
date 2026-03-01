"""
10-K Content Score Analysis – Visualization Script
Produces 4 main text figures + 2 appendix figures.

MAIN TEXT:
  fig9_score_by_year.png        – mean specificity score over time with jittered firm dots
  fig11_categories_by_1c.png    – category adoption with vs without Item 1C
  fig12_score_by_sector.png     – mean specificity score by sector (bar + SD)

APPENDIX:
  figA4_score_by_size.png       – specificity score boxplot by firm size
  figA5_score_heatmap.png       – heatmap: all firms × all years

Requirements: pandas, matplotlib, seaborn, numpy, openpyxl
Usage:        python content_score_viz.py
Input:        content_scores.xlsx + length_results.csv (same directory)
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
import numpy as np
import os

# ── PATHS ─────────────────────────────────────────────────────────────────────
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(SCRIPT_DIR, "..", "visuals", "content")
os.makedirs(OUTPUT_DIR, exist_ok=True)

def out(filename):
    return os.path.join(OUTPUT_DIR, filename)

# ── LOAD & MERGE DATA ─────────────────────────────────────────────────────────
df = pd.read_excel(os.path.join(SCRIPT_DIR, "..", "results", "content_scores.xlsx"))
length = pd.read_csv(os.path.join(SCRIPT_DIR, "..", "results", "length_results.csv"))[["ticker","year","sector","size","has_1c"]].drop_duplicates()
df = df.merge(length, on=["ticker","year"], how="left")

CATS = ["frameworks","specific_controls","named_individuals",
        "quantitative_data","product_names","technical_details"]

CAT_LABELS = {
    "frameworks":        "Frameworks",
    "specific_controls": "Specific Controls",
    "named_individuals": "Named Individuals",
    "quantitative_data": "Quantitative Data",
    "product_names":     "Product Names",
    "technical_details": "Technical Details",
}

SECTOR_ORDER = [
    "Semiconductors","Healthcare","Consumer Goods",
    "Retail & E-Commerce","Finance","Technology","Cybersecurity"
]
SIZE_ORDER = ["Small","Medium","Large"]

# ── STYLE ─────────────────────────────────────────────────────────────────────
sns.set_theme(style="whitegrid", font_scale=1.15)
BLUE   = "#2E75B6"
ORANGE = "#ED7D31"
GRAY   = "#7F7F7F"
GREEN  = "#70AD47"

np.random.seed(42)


# ═════════════════════════════════════════════════════════════════════════════
# FIG 9 – Mean specificity score by year with jittered firm dots  [MAIN TEXT]
# ═════════════════════════════════════════════════════════════════════════════
yearly = df.groupby("year")["content_score"].agg(["mean","std"]).reset_index()

fig, ax = plt.subplots(figsize=(9, 5))

# Jittered individual firm dots
for year in sorted(df["year"].unique()):
    vals = df[df["year"] == year]["content_score"].values
    jitter = np.random.uniform(-0.08, 0.08, size=len(vals))
    ax.scatter(np.full(len(vals), year) + jitter, vals,
               color=BLUE, alpha=0.25, s=22, zorder=2)

# SD band
ax.fill_between(
    yearly["year"],
    (yearly["mean"] - yearly["std"]).clip(lower=0),
    (yearly["mean"] + yearly["std"]).clip(upper=1),
    color=BLUE, alpha=0.15, label="±1 SD"
)

# Mean line
ax.plot(yearly["year"], yearly["mean"],
        marker="o", color=BLUE, lw=2.5, zorder=3, label="Mean score")

# Annotate mean values
for _, row in yearly.iterrows():
    ax.annotate(f'{row["mean"]:.3f}',
                xy=(row["year"], row["mean"]),
                xytext=(0, 12), textcoords="offset points",
                ha="center", fontsize=10)

ax.set_xticks([2022, 2023, 2024, 2025])
ax.set_xlabel("Fiscal Year")
ax.set_ylabel("Content Score (0–1)")
ax.set_ylim(-0.05, 1.1)
ax.legend(fontsize=10)
ax.set_title("Mean Content Score Over Time",
             fontweight="bold")
plt.tight_layout()
plt.savefig(out("content_by_year.png"), dpi=150, bbox_inches="tight")
plt.close()
print("Saved content_by_year.png")


# ═════════════════════════════════════════════════════════════════════════════
# FIG 11 – Category adoption: with vs without Item 1C             [MAIN TEXT]
# ═════════════════════════════════════════════════════════════════════════════
ic_cats = (df.groupby("has_1c")[CATS].mean() * 100).T
ic_cats.columns = ["Without Item 1C", "With Item 1C"]
ic_cats.index = [CAT_LABELS[c] for c in ic_cats.index]

x     = np.arange(len(ic_cats))
width = 0.35

fig, ax = plt.subplots(figsize=(11, 5))
bars1 = ax.bar(x - width/2, ic_cats["Without Item 1C"], width,
               color=GRAY,   alpha=0.85, edgecolor="white", label="Without Item 1C")
bars2 = ax.bar(x + width/2, ic_cats["With Item 1C"],    width,
               color=BLUE,   alpha=0.85, edgecolor="white", label="With Item 1C")

# Annotate bar values
for bar in bars1:
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1.5,
            f'{bar.get_height():.0f}%', ha='center', va='bottom', fontsize=8.5)
for bar in bars2:
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1.5,
            f'{bar.get_height():.0f}%', ha='center', va='bottom', fontsize=8.5)

ax.set_xticks(x)
ax.set_xticklabels(ic_cats.index, rotation=15, ha="right")
ax.set_ylabel("Share of Filings with Category Present (%)")
ax.set_ylim(0, 115)
ax.legend(fontsize=10)
ax.set_title("Category Adoption Rate: Filings With vs Without Item 1C",
             fontweight="bold")
plt.tight_layout()
plt.savefig(out("content_categories_by_1c.png"), dpi=150, bbox_inches="tight")
plt.close()
print("Saved content_categories_by_1c.png")


# ═════════════════════════════════════════════════════════════════════════════
# FIG 12 – Mean specificity score by sector (bar + error bars)    [MAIN TEXT]
# ═════════════════════════════════════════════════════════════════════════════
sec = df.groupby("sector")["content_score"].agg(["mean","std","count"]).reindex(SECTOR_ORDER)

fig, ax = plt.subplots(figsize=(10, 5))
bars = ax.barh(sec.index, sec["mean"],
               xerr=sec["std"], color=BLUE, alpha=0.82,
               edgecolor="white", height=0.55,
               error_kw=dict(ecolor=GRAY, capsize=4, lw=1.3))

# Annotate mean values
for i, (idx, row) in enumerate(sec.iterrows()):
    ax.text(row["mean"] + row["std"] + 0.015, i,
            f'{row["mean"]:.3f}', va='center', fontsize=9.5)

ax.set_xlabel("Mean Content Score (0–1)")
ax.set_xlim(0, 1.0)
ax.axvline(df["content_score"].mean(), color=ORANGE, ls="--", lw=1.5,
           label=f'Overall mean = {df["content_score"].mean():.3f}')
ax.legend(fontsize=10)
ax.set_title("Mean Content Content Score by Sector\n"
             "(error bars = ±1 SD)",
             fontweight="bold")
plt.tight_layout()
plt.savefig(out("content_by_sector.png"), dpi=150, bbox_inches="tight")
plt.close()
print("Saved content_by_sector.png")


# ═════════════════════════════════════════════════════════════════════════════
# FIG A4 – Specificity score boxplot by firm size                 [APPENDIX]
# ═════════════════════════════════════════════════════════════════════════════
size_means = df.groupby("size")["content_score"].mean()

fig, ax = plt.subplots(figsize=(8, 5))
sns.boxplot(data=df, x="size", y="content_score", order=SIZE_ORDER,
            color=BLUE, ax=ax,
            flierprops=dict(marker=".", markersize=5, alpha=0.5))

ymax = df["content_score"].quantile(0.98)
for i, sz in enumerate(SIZE_ORDER):
    ax.text(i, size_means[sz] + 0.04,
            f'Mean\n{size_means[sz]:.3f}',
            ha='center', va='bottom', fontsize=9)

ax.set_xlabel("Firm Size")
ax.set_ylabel("Content Score (0–1)")
ax.set_ylim(-0.05, 1.15)
ax.set_title("Content Score by Firm Size",
             fontweight="bold")
plt.tight_layout()
plt.savefig(out("content_by_size.png"), dpi=150, bbox_inches="tight")
plt.close()
print("Saved content_score_by_size.png")


# ═════════════════════════════════════════════════════════════════════════════
# FIG A5 – Heatmap: all firms × all years
# ═════════════════════════════════════════════════════════════════════════════
pivot = df.pivot_table(index="ticker", columns="year", values="content_score")
pivot = pivot.sort_values(by=[2022, 2023, 2024, 2025])

fig, ax = plt.subplots(figsize=(7, 13))
sns.heatmap(pivot, ax=ax, annot=True, fmt=".2f", cmap="Blues",
            linewidths=0.4, linecolor="#e0e0e0",
            cbar_kws={"label": "Content Score", "shrink": 0.6},
            vmin=0, vmax=1,
            annot_kws={"size": 8})

ax.set_xlabel("Fiscal Year")
ax.set_ylabel("")
ax.set_title("Figure A5 – Content Score by Firm and Year",
             fontweight="bold")
plt.tight_layout()
plt.savefig(out("content_heatmap.png"), dpi=150, bbox_inches="tight")
plt.close()
print("Saved content_heatmap.png")

print("\nAll content score outputs saved successfully.")