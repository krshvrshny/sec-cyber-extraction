"""
10-K Composite Specificity Score (S) – Script

Formula: S = 0.6 * (C * 100) + 0.4 * (1 - BP) * 100
  C  = content specificity score (0–1, scaled to 0–100)
  BP = boilerplate ratio (phrases / total words, ~0–0.002)

Note: the formula requires C on a 0–100 scale. Taking C literally as 0–1
collapses S to a range of 39.9–40.6 with near-zero variance because BP is
tiny (~0.00077). Scaling C * 100 first gives a proper 40–100 range.

Classification:
  High Specificity : S >= 60
  Low Specificity  : S <  60

OUTPUTS (main text):
  composite_scores.csv           – full dataset
  table4_composite_stats.csv     – stats + category split by year
  fig15_composite_by_year.png    – mean S over time + stacked category share
  fig16_composite_by_1c.png      – S distribution with vs without Item 1C

OUTPUTS (appendix):
  figA8_composite_by_sector.png  – mean S by sector
  figA9_composite_by_size.png    – S by firm size (boxplot)

Input files:  content_scores.xlsx + boilerplate_results.csv + length_results.csv
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

# ── LOAD & MERGE ──────────────────────────────────────────────────────────────
content = pd.read_excel("content_scores.xlsx")
boiler  = pd.read_csv("boilerplate_results.csv")
length  = pd.read_csv("length_results.csv")[
    ["ticker", "year", "sector", "size", "has_1c"]
].drop_duplicates()

df = (
    content[["ticker", "year", "specificity_score"]]
    .merge(boiler[["ticker", "year", "boilerplate_ratio"]], on=["ticker", "year"])
    .merge(length, on=["ticker", "year"])
)

# ── COMPUTE S & CLASSIFY ──────────────────────────────────────────────────────
df["S"] = 0.6 * df["specificity_score"] * 100 + 0.4 * (1 - df["boilerplate_ratio"]) * 100
df["category"] = df["S"].apply(lambda x: "High Specificity" if x >= 60 else "Low Specificity")

df.to_csv("composite_scores.csv", index=False)
print("Saved composite_scores.csv")

# ── STYLE ─────────────────────────────────────────────────────────────────────
sns.set_theme(style="whitegrid", font_scale=1.15)
BLUE   = "#2E75B6"
ORANGE = "#ED7D31"
GRAY   = "#7F7F7F"

SECTOR_ORDER = [
    "Semiconductors", "Healthcare", "Consumer Goods",
    "Retail & E-Commerce", "Finance", "Technology", "Cybersecurity",
]
SIZE_ORDER = ["Small", "Medium", "Large"]
np.random.seed(42)


# ═════════════════════════════════════════════════════════════════════════════
# TABLE 4 – Descriptive stats + category split by year         [MAIN TEXT]
# ═════════════════════════════════════════════════════════════════════════════
rows = []
for label, sub in [("All years", df)] + [
    (yr, df[df["year"] == yr]) for yr in sorted(df["year"].unique())
]:
    d  = sub["S"]
    hi = (sub["category"] == "High Specificity").sum()
    lo = (sub["category"] == "Low Specificity").sum()
    rows.append({
        "Year":                    label,
        "N":                       len(sub),
        "Mean S":                  round(d.mean(), 2),
        "Median S":                round(d.median(), 2),
        "SD":                      round(d.std(), 2),
        "Min":                     round(d.min(), 2),
        "Max":                     round(d.max(), 2),
        "High Specificity (≥60)":  f"{hi} ({hi/len(sub)*100:.0f}%)",
        "Low Specificity (<60)":   f"{lo} ({lo/len(sub)*100:.0f}%)",
    })

table = pd.DataFrame(rows)
table.to_csv("table4_composite_stats.csv", index=False)
print("Saved table4_composite_stats.csv")
print(table.to_string(index=False))


# ═════════════════════════════════════════════════════════════════════════════
# FIG 15 – Mean S over time (left) + stacked category share (right)
# ═════════════════════════════════════════════════════════════════════════════
yearly  = df.groupby("year")["S"].agg(["mean", "std"]).reset_index()
cat_pct = pd.crosstab(df["year"], df["category"], normalize="index") * 100
years   = sorted(df["year"].unique())

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

# Left – mean S with jitter and SD band
for year in years:
    vals   = df[df["year"] == year]["S"].values
    jitter = np.random.uniform(-0.08, 0.08, size=len(vals))
    ax1.scatter(np.full(len(vals), year) + jitter, vals,
                color=BLUE, alpha=0.22, s=22, zorder=2)

ax1.fill_between(
    yearly["year"],
    (yearly["mean"] - yearly["std"]).clip(lower=0),
    (yearly["mean"] + yearly["std"]).clip(upper=100),
    color=BLUE, alpha=0.15, label="±1 SD",
)
ax1.plot(yearly["year"], yearly["mean"],
         marker="o", color=BLUE, lw=2.5, zorder=3, label="Mean S")
ax1.axhline(60, color="red", lw=1.5, ls="--", label="Threshold (60)")

for _, row in yearly.iterrows():
    ax1.annotate(f'{row["mean"]:.1f}',
                 xy=(row["year"], row["mean"]),
                 xytext=(0, 12), textcoords="offset points",
                 ha="center", fontsize=10)

ax1.set_xticks(years)
ax1.set_xlabel("Fiscal Year")
ax1.set_ylabel("Composite Score S")
ax1.set_ylim(0, 110)
ax1.legend(fontsize=9)
ax1.set_title("Mean Composite Score Over Time\n(dots = individual firms)",
              fontweight="bold")

# Right – stacked bar: category share
bottom = np.zeros(len(years))
for cat, color in [("Low Specificity", ORANGE), ("High Specificity", BLUE)]:
    vals = [cat_pct.loc[yr, cat] if cat in cat_pct.columns else 0 for yr in years]
    bars = ax2.bar([str(yr) for yr in years], vals,
                   bottom=bottom, color=color, alpha=0.85,
                   edgecolor="white", width=0.5, label=cat)
    for bar, val, bot in zip(bars, vals, bottom):
        if val > 6:
            ax2.text(bar.get_x() + bar.get_width() / 2, bot + val / 2,
                     f'{val:.0f}%', ha="center", va="center",
                     fontsize=10, color="white", fontweight="bold")
    bottom += np.array(vals)

ax2.set_ylim(0, 110)
ax2.set_ylabel("Share of Filings (%)")
ax2.set_xlabel("Fiscal Year")
ax2.legend(fontsize=9)
ax2.set_title("High / Low Specificity Share by Year", fontweight="bold")

fig.suptitle("Figure 15 – Composite Specificity Score (S) Over Time",
             fontweight="bold", fontsize=13)
plt.tight_layout()
plt.savefig("fig15_composite_by_year.png", dpi=150, bbox_inches="tight")
plt.close()
print("Saved fig15_composite_by_year.png")


# ═════════════════════════════════════════════════════════════════════════════
# FIG 16 – S distribution: with vs without Item 1C (KDE + histogram)
# ═════════════════════════════════════════════════════════════════════════════
fig, ax = plt.subplots(figsize=(10, 5))

for has_1c, color, label in [
    (False, GRAY, "Without Item 1C"),
    (True,  BLUE, "With Item 1C"),
]:
    sub = df[df["has_1c"] == has_1c]["S"]
    sub.plot.kde(ax=ax, color=color, lw=2,
                 label=f'{label}  (mean = {sub.mean():.1f}, n = {len(sub)})')
    ax.hist(sub, bins=20, density=True, alpha=0.12, color=color)

ax.axvline(60, color="red", lw=1.8, ls="--", label="Threshold (60)")
ax.set_xlabel("Composite Score S")
ax.set_ylabel("Density")
ax.set_xlim(30, 105)
ax.legend(fontsize=10)
ax.set_title("Figure 16 – Composite Score Distribution:\nFilings With vs Without Item 1C",
             fontweight="bold")
plt.tight_layout()
plt.savefig("fig16_composite_by_1c.png", dpi=150, bbox_inches="tight")
plt.close()
print("Saved fig16_composite_by_1c.png")


# ═════════════════════════════════════════════════════════════════════════════
# FIG A8 – Mean S by sector                                    [APPENDIX]
# ═════════════════════════════════════════════════════════════════════════════
sec = df.groupby("sector")["S"].agg(["mean", "std"]).reindex(SECTOR_ORDER)

fig, ax = plt.subplots(figsize=(10, 5))
ax.barh(sec.index, sec["mean"],
        xerr=sec["std"], color=BLUE, alpha=0.82,
        edgecolor="white", height=0.55,
        error_kw=dict(ecolor=GRAY, capsize=4, lw=1.3))

for i, (idx, row) in enumerate(sec.iterrows()):
    ax.text(row["mean"] + row["std"] + 0.5, i,
            f'{row["mean"]:.1f}', va="center", fontsize=9.5)

ax.axvline(60, color="red", lw=1.5, ls="--", label="Threshold (60)")
ax.axvline(df["S"].mean(), color=ORANGE, lw=1.5, ls="--",
           label=f'Overall mean = {df["S"].mean():.1f}')
ax.set_xlabel("Mean Composite Score S")
ax.set_xlim(30, 115)
ax.legend(fontsize=9)
ax.set_title("Figure A8 – Mean Composite Score by Sector [Appendix]\n(error bars = ±1 SD)",
             fontweight="bold")
plt.tight_layout()
plt.savefig("figA8_composite_by_sector.png", dpi=150, bbox_inches="tight")
plt.close()
print("Saved figA8_composite_by_sector.png")


# ═════════════════════════════════════════════════════════════════════════════
# FIG A9 – S score by firm size (boxplot)                      [APPENDIX]
# ═════════════════════════════════════════════════════════════════════════════
size_means = df.groupby("size")["S"].mean()

fig, ax = plt.subplots(figsize=(8, 5))
sns.boxplot(data=df, x="size", y="S", order=SIZE_ORDER,
            color=BLUE, ax=ax,
            flierprops=dict(marker=".", markersize=5, alpha=0.5))
ax.axhline(60, color="red", lw=1.5, ls="--", label="Threshold (60)")
for i, sz in enumerate(SIZE_ORDER):
    ax.text(i, size_means[sz] + 1.5,
            f'Mean\n{size_means[sz]:.1f}',
            ha="center", va="bottom", fontsize=9)

ax.set_xlabel("Firm Size")
ax.set_ylabel("Composite Score S")
ax.set_ylim(30, 115)
ax.legend(fontsize=10)
ax.set_title("Figure A9 – Composite Score by Firm Size [Appendix]", fontweight="bold")
plt.tight_layout()
plt.savefig("figA9_composite_by_size.png", dpi=150, bbox_inches="tight")
plt.close()
print("Saved figA9_composite_by_size.png")

print("\nAll composite score outputs saved successfully.")