"""
10-K Boilerplate Analysis – Visualization Script

MAIN TEXT:
  table3_boilerplate_stats.csv  – descriptive stats (count + ratio) by year
  fig13_boilerplate_by_year.png – mean boilerplate RATIO over time with jitter
  fig14_boilerplate_by_1c.png   – boilerplate count AND ratio: with vs without 1C

APPENDIX:
  figA6_boilerplate_by_sector.png – boilerplate count by sector

Requirements: pandas, matplotlib, seaborn, numpy
Usage:        python boilerplate_viz.py
Input:        boilerplate_results.csv (same directory)
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

# ── LOAD DATA ─────────────────────────────────────────────────────────────────
df = pd.read_csv("boilerplate_results.csv")

SECTOR_ORDER = [
    "Healthcare", "Semiconductors", "Consumer Goods",
    "Finance", "Technology", "Retail & E-Commerce", "Cybersecurity"
]

sns.set_theme(style="whitegrid", font_scale=1.15)
BLUE   = "#2E75B6"
ORANGE = "#ED7D31"
GRAY   = "#7F7F7F"

np.random.seed(42)


# ═════════════════════════════════════════════════════════════════════════════
# TABLE 3 – Descriptive statistics: overall + by year          [MAIN TEXT]
# ═════════════════════════════════════════════════════════════════════════════
rows = []
for label, subset in [("All years", df)] + [(yr, df[df["year"]==yr]) for yr in sorted(df["year"].unique())]:
    c = subset["boilerplate_count"]
    r = subset["boilerplate_ratio"]
    rows.append({
        "Year":          label,
        "N":             len(subset),
        "Mean count":    round(c.mean(), 2),
        "Median count":  round(c.median(), 2),
        "SD count":      round(c.std(), 2),
        "Mean ratio":    round(r.mean(), 6),
        "Max ratio":     round(r.max(), 6),
    })

table = pd.DataFrame(rows)
table.to_csv("table3_boilerplate_stats.csv", index=False)
print("Saved table3_boilerplate_stats.csv")
print(table.to_string(index=False))


# ═════════════════════════════════════════════════════════════════════════════
# FIG 13 – Boilerplate RATIO over time (primary finding: it's tiny)
#          Left axis = ratio; right axis = count for context   [MAIN TEXT]
# ═════════════════════════════════════════════════════════════════════════════
yearly_r = df.groupby("year")["boilerplate_ratio"].agg(["mean","std"]).reset_index()
yearly_c = df.groupby("year")["boilerplate_count"].agg(["mean"]).reset_index()

fig, ax1 = plt.subplots(figsize=(9, 5))
ax2 = ax1.twinx()

# Jitter for ratio (left axis)
for year in sorted(df["year"].unique()):
    vals = df[df["year"] == year]["boilerplate_ratio"].values
    jitter = np.random.uniform(-0.08, 0.08, size=len(vals))
    ax1.scatter(np.full(len(vals), year) + jitter, vals,
                color=BLUE, alpha=0.20, s=22, zorder=2)

# SD band + mean line for ratio
ax1.fill_between(
    yearly_r["year"],
    (yearly_r["mean"] - yearly_r["std"]).clip(lower=0),
    yearly_r["mean"] + yearly_r["std"],
    color=BLUE, alpha=0.15, label="Ratio ±1 SD"
)
ax1.plot(yearly_r["year"], yearly_r["mean"],
         marker="o", color=BLUE, lw=2.5, zorder=3, label="Mean ratio")

# Mean count line (right axis, dashed, secondary)
ax2.plot(yearly_c["year"], yearly_c["mean"],
         marker="s", color=ORANGE, lw=1.8, ls="--", zorder=3, label="Mean count (right axis)")

# Annotate ratio values
for _, row in yearly_r.iterrows():
    ax1.annotate(f'{row["mean"]:.5f}',
                 xy=(row["year"], row["mean"]),
                 xytext=(0, 12), textcoords="offset points",
                 ha="center", fontsize=9, color=BLUE)

ax1.set_xticks([2022, 2023, 2024, 2025])
ax1.set_xlabel("Fiscal Year")
ax1.set_ylabel("Boilerplate Ratio (phrases / words)", color=BLUE)
ax1.tick_params(axis="y", labelcolor=BLUE)
ax2.set_ylabel("Mean Phrase Count", color=ORANGE)
ax2.tick_params(axis="y", labelcolor=ORANGE)
ax1.set_ylim(0, 0.0025)
ax2.set_ylim(0, 18)

lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, fontsize=9, loc="upper left")

ax1.set_title("Figure 13 – Boilerplate Ratio Over Time\n"
              "(ratio < 0.002 in all years; dots = individual firm ratios)",
              fontweight="bold")
plt.tight_layout()
plt.savefig("fig13_boilerplate_by_year.png", dpi=150, bbox_inches="tight")
plt.close()
print("Saved fig13_boilerplate_by_year.png")


# ═════════════════════════════════════════════════════════════════════════════
# FIG 14 – Count AND ratio: with vs without Item 1C (side-by-side panels)
#          Shows count rises but ratio stays flat                [MAIN TEXT]
# ═════════════════════════════════════════════════════════════════════════════
ic = df.groupby("has_1c")[["boilerplate_count","boilerplate_ratio"]].agg(["mean","std"])
labels = ["Without\nItem 1C", "With\nItem 1C"]
counts = [ic["boilerplate_count"]["mean"][False], ic["boilerplate_count"]["mean"][True]]
count_sds = [ic["boilerplate_count"]["std"][False], ic["boilerplate_count"]["std"][True]]
ratios = [ic["boilerplate_ratio"]["mean"][False], ic["boilerplate_ratio"]["mean"][True]]
ratio_sds = [ic["boilerplate_ratio"]["std"][False], ic["boilerplate_ratio"]["std"][True]]

fig, (ax_c, ax_r) = plt.subplots(1, 2, figsize=(10, 5))

# Left: count
bars = ax_c.bar(labels, counts, yerr=count_sds,
                color=[GRAY, BLUE], alpha=0.85, edgecolor="white",
                width=0.4, capsize=6, error_kw=dict(ecolor=GRAY, lw=1.3))
for bar, val in zip(bars, counts):
    ax_c.text(bar.get_x() + bar.get_width()/2, val + 0.3,
              f'{val:.2f}', ha='center', va='bottom', fontsize=11)
ax_c.set_ylabel("Mean Boilerplate Phrase Count")
ax_c.set_ylim(0, 18)
ax_c.set_title("Phrase Count", fontweight="bold")

# Right: ratio
bars2 = ax_r.bar(labels, ratios, yerr=ratio_sds,
                 color=[GRAY, BLUE], alpha=0.85, edgecolor="white",
                 width=0.4, capsize=6, error_kw=dict(ecolor=GRAY, lw=1.3))
for bar, val in zip(bars2, ratios):
    ax_r.text(bar.get_x() + bar.get_width()/2, val + 0.00003,
              f'{val:.5f}', ha='center', va='bottom', fontsize=11)
ax_r.set_ylabel("Mean Boilerplate Ratio (phrases / words)")
ax_r.set_ylim(0, 0.0018)
ax_r.set_title("Phrase Ratio", fontweight="bold")

fig.suptitle("Figure 14 – Boilerplate Count vs Ratio: Filings With vs Without Item 1C\n"
             "(count rises with 1C; ratio stays flat — difference is driven by longer text)",
             fontweight="bold", fontsize=11)
plt.tight_layout()
plt.savefig("fig14_boilerplate_by_1c.png", dpi=150, bbox_inches="tight")
plt.close()
print("Saved fig14_boilerplate_by_1c.png")


# ═════════════════════════════════════════════════════════════════════════════
# FIG A6 – Boilerplate count by sector                          [APPENDIX]
# ═════════════════════════════════════════════════════════════════════════════
sec = df.groupby("sector")["boilerplate_count"].agg(["mean","std"]).reindex(SECTOR_ORDER)

fig, ax = plt.subplots(figsize=(10, 5))
ax.barh(sec.index, sec["mean"],
        xerr=sec["std"], color=BLUE, alpha=0.82,
        edgecolor="white", height=0.55,
        error_kw=dict(ecolor=GRAY, capsize=4, lw=1.3))

for i, (idx, row) in enumerate(sec.iterrows()):
    ax.text(row["mean"] + row["std"] + 0.2, i,
            f'{row["mean"]:.2f}', va='center', fontsize=9.5)

ax.axvline(df["boilerplate_count"].mean(), color=ORANGE, ls="--", lw=1.5,
           label=f'Overall mean = {df["boilerplate_count"].mean():.2f}')
ax.set_xlabel("Mean Boilerplate Phrase Count")
ax.set_xlim(0, 22)
ax.legend(fontsize=10)
ax.set_title("Figure A6 – Mean Boilerplate Count by Sector [Appendix]\n(error bars = ±1 SD)",
             fontweight="bold")
plt.tight_layout()
plt.savefig("figA6_boilerplate_by_sector.png", dpi=150, bbox_inches="tight")
plt.close()
print("Saved figA6_boilerplate_by_sector.png")

print("\nAll boilerplate outputs saved successfully.")


# ═════════════════════════════════════════════════════════════════════════════
# FIG A7 – Boilerplate count AND ratio by firm size (side-by-side panels)
#          Shows Medium highest on count; ratio differences are minimal
# ═════════════════════════════════════════════════════════════════════════════
SIZE_ORDER = ["Small", "Medium", "Large"]
size_count_means = df.groupby("size")["boilerplate_count"].mean()
size_ratio_means = df.groupby("size")["boilerplate_ratio"].mean()

fig, (ax_c, ax_r) = plt.subplots(1, 2, figsize=(12, 5))

# Left panel: count boxplot
sns.boxplot(data=df, x="size", y="boilerplate_count", order=SIZE_ORDER,
            color=BLUE, ax=ax_c,
            flierprops=dict(marker=".", markersize=5, alpha=0.5))
for i, sz in enumerate(SIZE_ORDER):
    ax_c.text(i, size_count_means[sz] + 0.4,
              f'Mean\n{size_count_means[sz]:.2f}',
              ha='center', va='bottom', fontsize=9)
ax_c.set_xlabel("Firm Size")
ax_c.set_ylabel("Boilerplate Phrase Count")
ax_c.set_ylim(0, 24)
ax_c.set_title("Phrase Count", fontweight="bold")

# Right panel: ratio boxplot
sns.boxplot(data=df, x="size", y="boilerplate_ratio", order=SIZE_ORDER,
            color=BLUE, ax=ax_r,
            flierprops=dict(marker=".", markersize=5, alpha=0.5))
for i, sz in enumerate(SIZE_ORDER):
    ax_r.text(i, size_ratio_means[sz] + 0.00003,
              f'Mean\n{size_ratio_means[sz]:.5f}',
              ha='center', va='bottom', fontsize=9)
ax_r.set_xlabel("Firm Size")
ax_r.set_ylabel("Boilerplate Ratio (phrases / words)")
ax_r.set_ylim(0, 0.0025)
ax_r.set_title("Phrase Ratio", fontweight="bold")

fig.suptitle("Figure A7 – Boilerplate Count and Ratio by Firm Size [Appendix]\n"
             "(Medium firms highest on count; ratios are low and similar across all size groups)",
             fontweight="bold", fontsize=11)
plt.tight_layout()
plt.savefig("figA7_boilerplate_by_size.png", dpi=150, bbox_inches="tight")
plt.close()
print("Saved figA7_boilerplate_by_size.png")