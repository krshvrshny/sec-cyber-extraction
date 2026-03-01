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

# ── LOAD DATA ─────────────────────────────────────────────────────────────────
df    = pd.read_csv("length_results.csv")
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
table.to_csv("table1_descriptive_stats.csv", index=False)
print("Saved table1_descriptive_stats.csv")
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
ax.set_title("Figure 1 – Adoption Rate of Item 1C by Year", fontweight="bold")
plt.tight_layout()
plt.savefig("fig1_adoption.png", dpi=150, bbox_inches="tight")
plt.close()
print("Saved fig1_adoption.png")


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
ax.set_title("Figure 2 – Item 1C Mean Length Over Time with ±1 SD (2023–2025)",
             fontweight="bold")
plt.tight_layout()
plt.savefig("fig2_1c_temporal.png", dpi=150, bbox_inches="tight")
plt.close()
print("Saved fig2_1c_temporal.png")


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

plt.suptitle("Figure 3 – Length Distributions of Items 1A and 1C",
             fontweight="bold", y=1.02)
plt.tight_layout()
plt.savefig("fig3_distribution.png", dpi=150, bbox_inches="tight")
plt.close()
print("Saved fig3_distribution.png")


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

plt.suptitle("Figure 4 – Section Length Heterogeneity by Firm Size",
             fontweight="bold", y=1.02)
plt.tight_layout()
plt.savefig("fig4_by_size.png", dpi=150, bbox_inches="tight")
plt.close()
print("Saved fig4_by_size.png")

print("\nAll outputs saved successfully.")