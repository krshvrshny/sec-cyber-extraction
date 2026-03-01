"""
10-K Cybersecurity Disclosure Length Analysis – Visualization Script v2
Produces 4 publication-quality figures + 1 descriptive statistics table.

Outputs:
  table1_descriptive_stats.csv  – mean, median, SD, min, max for 1A and 1C by year
  fig1_adoption.png             – Item 1C adoption rate by year
  fig2_1c_temporal.png          – Item 1C mean length over time with ±1 SD bands
  fig3_distribution.png         – Dual: distribution of 1A (all) and 1C (2024–2025)
  fig4_by_size.png              – Dual: boxplots of 1A and 1C by firm size

Requirements: pandas, matplotlib, seaborn, numpy
Usage:        python visualizations_v2.py
Input:        length_results.csv (must be in the same directory)
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
import numpy as np
import os

# ── PATHS ─────────────────────────────────────────────────────────────────────
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(SCRIPT_DIR, "..", "visuals", "length")
os.makedirs(OUTPUT_DIR, exist_ok=True)

def out(filename):
    return os.path.join(OUTPUT_DIR, filename)

# ── LOAD DATA ─────────────────────────────────────────────────────────────────
df    = pd.read_csv(os.path.join(SCRIPT_DIR, "..", "results", "length_results.csv"))
df_1c = df[df["has_1c"] == True].copy()
mature = df_1c[df_1c["year"].isin([2024, 2025])]

# ── STYLE ─────────────────────────────────────────────────────────────────────
sns.set_theme(style="whitegrid", font_scale=1.15)
BLUE   = "#2E75B6"
ORANGE = "#ED7D31"
GRAY   = "#7F7F7F"

def fmt_thousands(x, _):
    return f"{int(x):,}"


# ═════════════════════════════════════════════════════════════════════════════
# TABLE 1 – Descriptive statistics for Item 1A and Item 1C by year
# ═════════════════════════════════════════════════════════════════════════════
rows = []

for col, label, source in [("len_1a", "Item 1A", df), ("len_1c", "Item 1C", df_1c)]:
    d = source[col].dropna()
    rows.append({"Section": label, "Year": "All years", "N": len(d),
                 "Mean": round(d.mean()), "Median": round(d.median()),
                 "SD": round(d.std()), "Min": int(d.min()), "Max": int(d.max())})

for year in sorted(df["year"].unique()):
    for col, label, source in [
        ("len_1a", "Item 1A", df[df["year"] == year]),
        ("len_1c", "Item 1C", df_1c[df_1c["year"] == year]),
    ]:
        d = source[col].dropna()
        if len(d) == 0:
            rows.append({"Section": label, "Year": year, "N": 0,
                         "Mean": "—", "Median": "—", "SD": "—", "Min": "—", "Max": "—"})
        else:
            rows.append({"Section": label, "Year": year, "N": len(d),
                         "Mean": round(d.mean()), "Median": round(d.median()),
                         "SD": round(d.std()) if len(d) > 1 else "—",
                         "Min": int(d.min()), "Max": int(d.max())})

table = pd.DataFrame(rows)
table.to_csv(out("table_length_stats.csv"), index=False)
print("Saved table_length_stats.csv")
print(table.to_string(index=False))
print()


# ═════════════════════════════════════════════════════════════════════════════
# FIG 1 – Item 1C adoption rate by year
# ═════════════════════════════════════════════════════════════════════════════
adoption = df.groupby("year")["has_1c"].mean() * 100
counts   = df.groupby("year").size()

fig, ax = plt.subplots(figsize=(8, 5))
bars = ax.bar(adoption.index, adoption.values,
              color=ORANGE, alpha=0.85, edgecolor="white", width=0.5)

for bar, (yr, pct) in zip(bars, adoption.items()):
    n = counts[yr]
    ax.text(bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 1.5,
            f"{pct:.0f}%\n(n={n})",
            ha="center", va="bottom", fontsize=10)

ax.set_ylim(0, 115)
ax.set_ylabel("Share of Filings with Item 1C (%)")
ax.set_xlabel("Fiscal Year")
ax.set_xticks([2022, 2023, 2024, 2025])
ax.axhline(100, color=GRAY, ls="--", lw=1, alpha=0.5)
ax.set_title("Adoption Rate of Item 1C by Year", fontweight="bold")
plt.tight_layout()
plt.savefig(out("adoption.png"), dpi=150, bbox_inches="tight")
plt.close()
print("Saved adoption.png")


# ═════════════════════════════════════════════════════════════════════════════
# FIG 2 – Item 1C mean length over time with ±1 SD bands (2023–2025)
# ═════════════════════════════════════════════════════════════════════════════
temporal = (df_1c.groupby("year")["len_1c"]
            .agg(["mean", "std", "count"])
            .reset_index())
temporal = temporal[temporal["year"] >= 2023]

fig, ax = plt.subplots(figsize=(9, 5))
ax.fill_between(
    temporal["year"],
    (temporal["mean"] - temporal["std"]).clip(lower=0),
    temporal["mean"] + temporal["std"],
    color=ORANGE, alpha=0.18, label="±1 SD"
)
ax.plot(temporal["year"], temporal["mean"],
        marker="o", color=ORANGE, lw=2.4, label="Mean word count")

for _, row in temporal.iterrows():
    ax.annotate(f'{row["mean"]:.0f}',
                xy=(row["year"], row["mean"]),
                xytext=(0, 12), textcoords="offset points",
                ha="center", fontsize=10)

ax.set_xticks([2023, 2024, 2025])
ax.set_xlabel("Fiscal Year")
ax.set_ylabel("Item 1C Word Count")
ax.yaxis.set_major_formatter(mticker.FuncFormatter(fmt_thousands))
ax.legend(fontsize=10)
ax.set_title("Item 1C Mean Length Over Time with ±1 SD (2023–2025)",
             fontweight="bold")
plt.tight_layout()
plt.savefig(out("length_1c.png"), dpi=150, bbox_inches="tight")
plt.close()
print("Saved length_1c.png")


# ═════════════════════════════════════════════════════════════════════════════
# FIG 3 – Dual distribution: Item 1A (all years) and Item 1C (2024–2025)
# ═════════════════════════════════════════════════════════════════════════════
fig, axes = plt.subplots(1, 2, figsize=(13, 5))

panels = [
    (axes[0], df["len_1a"].dropna(), BLUE,
     f"Item 1A – Risk Factors\n(all filings, n={len(df)})"),
    (axes[1], mature["len_1c"].dropna(), ORANGE,
     f"Item 1C – Cybersecurity\n(2024–2025 filings, n={len(mature)})"),
]

for ax, vals, color, title in panels:
    ax.hist(vals, bins=28, color=color, alpha=0.5,
            edgecolor="white", linewidth=0.5, density=True)
    try:
        vals.plot.kde(ax=ax, color=color, lw=2)
    except Exception:
        pass
    ax.axvline(vals.mean(),   color="black", ls="--", lw=1.5,
               label=f"Mean   = {vals.mean():,.0f}")
    ax.axvline(vals.median(), color=GRAY,   ls=":",  lw=1.5,
               label=f"Median = {vals.median():,.0f}")
    ax.set_title(f"Distribution of Word Count\n{title}", fontsize=12)
    ax.set_xlabel("Word Count")
    ax.set_ylabel("Density")
    ax.legend(fontsize=10)
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(fmt_thousands))

plt.suptitle("Length Distributions of Items 1A and 1C",
             fontweight="bold", y=1.02)
plt.tight_layout()
plt.savefig(out("length_distribution.png"), dpi=150, bbox_inches="tight")
plt.close()
print("Saved length_distribution.png")


# ═════════════════════════════════════════════════════════════════════════════
# FIG 4 – Dual boxplot: 1A and 1C by firm size
# ═════════════════════════════════════════════════════════════════════════════
SIZE_ORDER = ["Small", "Medium", "Large"]

fig, axes = plt.subplots(1, 2, figsize=(13, 5))

for ax, col, label, color, source in zip(
    axes,
    ["len_1a", "len_1c"],
    ["Item 1A – Risk Factors", "Item 1C – Cybersecurity"],
    [BLUE, ORANGE],
    [df, df_1c],
):
    sns.boxplot(data=source, x="size", y=col, order=SIZE_ORDER,
                color=color, ax=ax,
                flierprops=dict(marker=".", markersize=4, alpha=0.5))

    size_means = source.groupby("size")[col].mean()
    ymax = source[col].quantile(0.98)
    for i, sz in enumerate(SIZE_ORDER):
        if sz in size_means.index:
            ax.text(i, size_means[sz] + ymax * 0.03,
                    f"Mean\n{size_means[sz]:,.0f}",
                    ha="center", va="bottom", fontsize=9)

    ax.set_title(f"{label}\nby Firm Size", fontweight="bold")
    ax.set_xlabel("Firm Size")
    ax.set_ylabel("Word Count")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(fmt_thousands))

plt.suptitle("Section Length Heterogeneity by Firm Size",
             fontweight="bold", y=1.02)
plt.tight_layout()
plt.savefig(out("length_by_size.png"), dpi=150, bbox_inches="tight")
plt.close()
print("Saved length_by_size.png")

# ═════════════════════════════════════════════════════════════════════════════
# FIG 2 – Mean section length over time: Item 1A (left) and 1C (right axis)
# ═════════════════════════════════════════════════════════════════════════════
mean_1a = df.groupby("year")["len_1a"].mean()
mean_1c = df_1c.groupby("year")["len_1c"].mean()

fig, ax1 = plt.subplots(figsize=(10, 5))
ax2 = ax1.twinx()

ax1.plot(mean_1a.index, mean_1a.values,
         marker="o", color=BLUE, lw=2.4, label="Item 1A (all filings)")
ax2.plot(mean_1c.index, mean_1c.values,
         marker="s", color=ORANGE, lw=2.4, ls="--", label="Item 1C (filings with 1C only)")

# SEC Rule effective annotation
ax1.axvline(2023.25, color=GRAY, ls=":", lw=1.3)
ax1.text(2023.3, ax1.get_ylim()[0] if ax1.get_ylim()[0] > 0 else mean_1a.min() * 0.9995,
         "SEC Rule\neffective", color=GRAY, fontsize=9, va="bottom")

ax1.set_xlabel("Fiscal Year")
ax1.set_ylabel("Item 1A Mean Word Count", color=BLUE)
ax1.tick_params(axis="y", labelcolor=BLUE)
ax1.yaxis.set_major_formatter(mticker.FuncFormatter(fmt_thousands))
ax1.set_xticks([2022, 2023, 2024, 2025])

ax2.set_ylabel("Item 1C Mean Word Count", color=ORANGE)
ax2.tick_params(axis="y", labelcolor=ORANGE)
ax2.yaxis.set_major_formatter(mticker.FuncFormatter(fmt_thousands))

lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, fontsize=10, loc="upper left")

ax1.set_title("Mean Section Length Over Time (2022–2025)",
              fontweight="bold")
plt.tight_layout()
plt.savefig(out("length_temporal_trends.png"), dpi=150, bbox_inches="tight")
plt.close()
print("Saved length_temporal_trends.png")

# ═════════════════════════════════════════════════════════════════════════════
# FIG 4 – Mean section length by sector: Item 1A and 1C (grouped horizontal bars)
# ═════════════════════════════════════════════════════════════════════════════
SECTOR_ORDER_LEN = [
    "Healthcare", "Consumer Goods", "Semiconductors",
    "Technology", "Retail & E-Commerce", "Cybersecurity", "Finance"
]

mean_1a_sec = df.groupby("sector")["len_1a"].mean().reindex(SECTOR_ORDER_LEN)
mean_1c_sec = df_1c.groupby("sector")["len_1c"].mean().reindex(SECTOR_ORDER_LEN)

y      = np.arange(len(SECTOR_ORDER_LEN))
height = 0.35

fig, ax = plt.subplots(figsize=(11, 6))
ax.barh(y + height / 2, mean_1a_sec.values, height,
        color=BLUE,   alpha=0.85, edgecolor="white", label="Item 1A")
ax.barh(y - height / 2, mean_1c_sec.values, height,
        color=ORANGE, alpha=0.85, edgecolor="white", label="Item 1C")

ax.set_yticks(y)
ax.set_yticklabels(SECTOR_ORDER_LEN)
ax.set_xlabel("Mean Word Count")
ax.xaxis.set_major_formatter(mticker.FuncFormatter(fmt_thousands))
ax.legend(fontsize=10, loc="lower right")
ax.set_title("Mean Section Length by Sector", fontweight="bold")
plt.tight_layout()
plt.savefig(out("length_by_sector.png"), dpi=150, bbox_inches="tight")
plt.close()
print("Saved length_by_sector.png")

print("\nAll outputs saved successfully.")