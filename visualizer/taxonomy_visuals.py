"""
NIST CSF 2.0 Disclosure Scoring — Visualizations
=================================================
Reads nist_csf_scores.csv and produces publication-ready figures.

Dependencies: pip install pandas matplotlib seaborn numpy
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import seaborn as sns
from pathlib import Path

# =============================================================================
# CONFIG
# =============================================================================

INPUT_FILE  = "nist_csf_scores.csv"
OUTPUT_DIR  = "figures"
THRESHOLD   = 0.6

FUNCTIONS   = ["GV", "ID", "PR", "DE", "RS", "RC"]
FUNC_LABELS = {
    "GV": "Govern",
    "ID": "Identify",
    "PR": "Protect",
    "DE": "Detect",
    "RS": "Respond",
    "RC": "Recover",
}
FUNC_COLORS = {
    "GV": "#2C5F8A",
    "ID": "#4A90C4",
    "PR": "#5BB56E",
    "DE": "#E8A838",
    "RS": "#D95F3B",
    "RC": "#8B5EA6",
}

# Style
plt.rcParams.update({
    "font.family":      "serif",
    "font.size":        11,
    "axes.titlesize":   13,
    "axes.titleweight": "bold",
    "axes.spines.top":  False,
    "axes.spines.right":False,
    "figure.dpi":       150,
})

Path(OUTPUT_DIR).mkdir(exist_ok=True)

# =============================================================================
# LOAD
# =============================================================================

df = pd.read_csv(INPUT_FILE)
w_cols = [f"w_{f}" for f in FUNCTIONS]
print(f"Loaded {len(df)} filings | Columns: {df.columns.tolist()}")

# =============================================================================
# FIGURE 1 — Balance Score Distribution
# Answers: How many filings meet the threshold? Where does the mass sit?
# =============================================================================

fig, ax = plt.subplots(figsize=(8, 4.5))

ax.hist(df["balance_score"], bins=20, color="#2C5F8A", edgecolor="white",
        linewidth=0.6, alpha=0.85)
ax.axvline(THRESHOLD, color="#D95F3B", linewidth=2, linestyle="--",
           label=f"Threshold = {THRESHOLD}")

n_pass = (df["balance_score"] >= THRESHOLD).sum()
n_fail = len(df) - n_pass
ax.text(THRESHOLD + 0.005, ax.get_ylim()[1] * 0.9,
        f"Pass: {n_pass}  Fail: {n_fail}",
        color="#D95F3B", fontsize=10)

ax.set_xlabel("Balance Score")
ax.set_ylabel("Number of Filings")
ax.set_title("Figure 1 — Distribution of Balance Scores Across All Filings")
ax.legend(frameon=False)
plt.tight_layout()
plt.savefig(f"{OUTPUT_DIR}/fig1_balance_distribution.pdf", bbox_inches="tight")
plt.savefig(f"{OUTPUT_DIR}/fig1_balance_distribution.png", bbox_inches="tight")
plt.close()
print("Saved fig1_balance_distribution")

# =============================================================================
# FIGURE 2 — Average NIST Function Weights Across Corpus
# Answers: Which functions dominate disclosure overall?
# =============================================================================

mean_weights = df[w_cols].mean().values
labels       = [FUNC_LABELS[f] for f in FUNCTIONS]
colors       = [FUNC_COLORS[f] for f in FUNCTIONS]

fig, ax = plt.subplots(figsize=(8, 4.5))
bars = ax.bar(labels, mean_weights, color=colors, edgecolor="white", linewidth=0.5)
ax.axhline(1/6, color="grey", linewidth=1.2, linestyle="--", alpha=0.7,
           label="Uniform benchmark (1/6)")

for bar, val in zip(bars, mean_weights):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.005,
            f"{val:.2%}", ha="center", va="bottom", fontsize=9)

ax.yaxis.set_major_formatter(mtick.PercentFormatter(xmax=1))
ax.set_ylabel("Mean Keyword Weight $w_f$")
ax.set_title("Figure 2 — Average Disclosure Weight per NIST CSF Function")
ax.legend(frameon=False)
plt.tight_layout()
plt.savefig(f"{OUTPUT_DIR}/fig2_mean_weights.pdf", bbox_inches="tight")
plt.savefig(f"{OUTPUT_DIR}/fig2_mean_weights.png", bbox_inches="tight")
plt.close()
print("Saved fig2_mean_weights")

# =============================================================================
# FIGURE 3 — Heatmap of Focus Vectors (firm × function)
# Answers: Which firms concentrate on which functions?
# =============================================================================

# Use company_name + year as row label
if "year" in df.columns:
    df["label"] = df["company_name"].astype(str) + " (" + df["year"].astype(str) + ")"
else:
    df["label"] = df["company_name"].astype(str)

heatmap_data = df.set_index("label")[w_cols].rename(
    columns={f"w_{f}": FUNC_LABELS[f] for f in FUNCTIONS}
)

fig_h = max(6, len(df) * 0.28)
fig, ax = plt.subplots(figsize=(9, fig_h))
sns.heatmap(
    heatmap_data,
    ax=ax,
    cmap="YlOrRd",
    annot=True,
    fmt=".2f",
    linewidths=0.4,
    linecolor="white",
    cbar_kws={"label": "Weight $w_f$", "shrink": 0.6},
    vmin=0, vmax=heatmap_data.values.max(),
)
ax.set_title("Figure 3 — Focus Vector Heatmap: Disclosure Weight by Firm and NIST Function")
ax.set_xlabel("")
ax.set_ylabel("")
ax.tick_params(axis="x", rotation=0)
ax.tick_params(axis="y", rotation=0, labelsize=8)
plt.tight_layout()
plt.savefig(f"{OUTPUT_DIR}/fig3_heatmap.pdf", bbox_inches="tight")
plt.savefig(f"{OUTPUT_DIR}/fig3_heatmap.png", bbox_inches="tight")
plt.close()
print("Saved fig3_heatmap")

# =============================================================================
# FIGURE 4 — Balance Score Over Time (if multiple years)
# Answers: Is disclosure quality improving year-over-year?
# =============================================================================

if "year" in df.columns and df["year"].nunique() > 1:
    yearly = df.groupby("year")["balance_score"].agg(["mean", "std"]).reset_index()

    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.plot(yearly["year"], yearly["mean"], marker="o", color="#2C5F8A",
            linewidth=2, markersize=6, label="Mean balance score")
    ax.fill_between(
        yearly["year"],
        yearly["mean"] - yearly["std"],
        yearly["mean"] + yearly["std"],
        alpha=0.15, color="#2C5F8A", label="±1 std dev"
    )
    ax.axhline(THRESHOLD, color="#D95F3B", linewidth=1.5, linestyle="--",
               label=f"Threshold = {THRESHOLD}")
    ax.set_xlabel("Year")
    ax.set_ylabel("Balance Score")
    ax.set_title("Figure 4 — Balance Score Trend Over Time")
    ax.legend(frameon=False)
    ax.xaxis.set_major_locator(plt.MaxNLocator(integer=True))
    plt.tight_layout()
    plt.savefig(f"{OUTPUT_DIR}/fig4_balance_over_time.pdf", bbox_inches="tight")
    plt.savefig(f"{OUTPUT_DIR}/fig4_balance_over_time.png", bbox_inches="tight")
    plt.close()
    print("Saved fig4_balance_over_time")
else:
    print("Skipped fig4 (only one year in data)")

# =============================================================================
# FIGURE 5 — Function Weight Evolution Over Time (stacked area)
# Answers: Has the thematic focus of disclosures shifted?
# =============================================================================

if "year" in df.columns and df["year"].nunique() > 1:
    yearly_w = df.groupby("year")[w_cols].mean().reset_index()
    years    = yearly_w["year"].values
    bottom   = np.zeros(len(years))

    fig, ax = plt.subplots(figsize=(9, 5))
    for f in FUNCTIONS:
        vals = yearly_w[f"w_{f}"].values
        ax.fill_between(years, bottom, bottom + vals,
                        alpha=0.85, color=FUNC_COLORS[f],
                        label=FUNC_LABELS[f])
        bottom += vals

    ax.axhline(1.0, color="black", linewidth=0.5, linestyle=":")
    ax.set_xlim(years[0], years[-1])
    ax.set_ylim(0, 1)
    ax.yaxis.set_major_formatter(mtick.PercentFormatter(xmax=1))
    ax.set_xlabel("Year")
    ax.set_ylabel("Proportional Keyword Weight")
    ax.set_title("Figure 5 — Thematic Composition of Disclosures Over Time")
    ax.legend(loc="upper left", frameon=False, fontsize=9,
              ncol=2, bbox_to_anchor=(1.01, 1))
    ax.xaxis.set_major_locator(plt.MaxNLocator(integer=True))
    plt.tight_layout()
    plt.savefig(f"{OUTPUT_DIR}/fig5_stacked_area.pdf", bbox_inches="tight")
    plt.savefig(f"{OUTPUT_DIR}/fig5_stacked_area.png", bbox_inches="tight")
    plt.close()
    print("Saved fig5_stacked_area")
else:
    print("Skipped fig5 (only one year in data)")

# =============================================================================
# FIGURE 6 — Primary Function Frequency (bar chart)
# Answers: What is the most common dominant function across filings?
# =============================================================================

primary_counts = df["primary_function"].value_counts().reindex(FUNCTIONS, fill_value=0)

fig, ax = plt.subplots(figsize=(7, 4))
bars = ax.bar(
    [FUNC_LABELS[f] for f in FUNCTIONS],
    primary_counts.values,
    color=[FUNC_COLORS[f] for f in FUNCTIONS],
    edgecolor="white"
)
for bar, val in zip(bars, primary_counts.values):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.3,
            str(val), ha="center", va="bottom", fontsize=10)

ax.set_ylabel("Number of Filings")
ax.set_title("Figure 6 — Most Frequent Primary Disclosure Function")
plt.tight_layout()
plt.savefig(f"{OUTPUT_DIR}/fig6_primary_function.pdf", bbox_inches="tight")
plt.savefig(f"{OUTPUT_DIR}/fig6_primary_function.png", bbox_inches="tight")
plt.close()
print("Saved fig6_primary_function")

# =============================================================================
# FIGURE 7 — Radar / Spider Chart per firm (average across years)
# Answers: What is each firm's disclosure fingerprint?
# =============================================================================

from matplotlib.patches import FancyArrowPatch
from matplotlib.path import Path as MplPath

def radar_chart(ax, values, labels, color, title):
    N      = len(labels)
    angles = np.linspace(0, 2 * np.pi, N, endpoint=False).tolist()
    vals   = values + [values[0]]
    angs   = angles + [angles[0]]

    ax.plot(angs, vals, color=color, linewidth=2)
    ax.fill(angs, vals, color=color, alpha=0.15)
    ax.set_xticks(angles)
    ax.set_xticklabels(labels, fontsize=8)
    ax.set_ylim(0, max(0.6, max(values) + 0.05))
    ax.set_yticks([0.1, 0.2, 0.3, 0.4, 0.5])
    ax.set_yticklabels(["10%","20%","30%","40%","50%"], fontsize=6, color="grey")
    ax.axhline(1/6, color="grey", linewidth=0.8, linestyle="--", alpha=0.5)
    ax.set_title(title, size=9, pad=10, fontweight="bold")
    ax.spines["polar"].set_visible(False)

firms       = df["company_name"].unique()
n_firms     = len(firms)
ncols       = min(4, n_firms)
nrows       = int(np.ceil(n_firms / ncols))
fig, axes   = plt.subplots(nrows, ncols,
                            subplot_kw={"projection": "polar"},
                            figsize=(ncols * 3.2, nrows * 3.2))
axes = np.array(axes).flatten()

palette = sns.color_palette("tab10", n_firms)
for i, firm in enumerate(firms):
    firm_data = df[df["company_name"] == firm][w_cols].mean()
    vals      = [firm_data[f"w_{f}"] for f in FUNCTIONS]
    labels    = [FUNC_LABELS[f] for f in FUNCTIONS]
    radar_chart(axes[i], vals, labels, color=palette[i], title=firm)

# Hide unused subplots
for j in range(n_firms, len(axes)):
    axes[j].set_visible(False)

fig.suptitle("Figure 7 — Disclosure Fingerprint per Firm (avg. across years)",
             fontsize=13, fontweight="bold", y=1.01)
plt.tight_layout()
plt.savefig(f"{OUTPUT_DIR}/fig7_radar_charts.pdf", bbox_inches="tight")
plt.savefig(f"{OUTPUT_DIR}/fig7_radar_charts.png", bbox_inches="tight")
plt.close()
print("Saved fig7_radar_charts")

# =============================================================================
# PRINT SUMMARY STATS FOR FINDINGS SECTION
# =============================================================================

print("\n" + "=" * 60)
print("SUMMARY STATISTICS FOR FINDINGS")
print("=" * 60)

print(f"\nBalance Score:")
print(f"  Mean  : {df['balance_score'].mean():.4f}")
print(f"  Median: {df['balance_score'].median():.4f}")
print(f"  Std   : {df['balance_score'].std():.4f}")
print(f"  Min   : {df['balance_score'].min():.4f}")
print(f"  Max   : {df['balance_score'].max():.4f}")
print(f"  Pass (>={THRESHOLD}): {(df['balance_score'] >= THRESHOLD).sum()}/{len(df)}")

print(f"\nMean weights per function:")
for f in FUNCTIONS:
    m = df[f"w_{f}"].mean()
    print(f"  {FUNC_LABELS[f]:<10}: {m:.4f}  ({m:.1%})")

print(f"\nPrimary function frequency:")
for f, cnt in df["primary_function"].value_counts().items():
    print(f"  {FUNC_LABELS.get(f, f):<10}: {cnt} filings ({cnt/len(df):.1%})")

if "year" in df.columns and df["year"].nunique() > 1:
    print(f"\nBalance score by year:")
    print(df.groupby("year")["balance_score"].mean().round(4).to_string())

print(f"\nAll figures saved to ./{OUTPUT_DIR}/")