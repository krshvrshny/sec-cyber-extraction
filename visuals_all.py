import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# ── Config ────────────────────────────────────────────────────────────────────
BOILERPLATE_PARQUET = "boilerplate_results.parquet"
SIMILARITY_PARQUET  = "similarity_results.parquet"
LENGTH_PARQUET      = "length_results.parquet"
VISUALS_DIR         = "visuals"
MANDATE_COLOR       = "#333333"

os.makedirs(VISUALS_DIR, exist_ok=True)


# ── Load & merge ──────────────────────────────────────────────────────────────
def load_data():
    bp  = pd.read_parquet(BOILERPLATE_PARQUET)
    sim = pd.read_parquet(SIMILARITY_PARQUET)[["ticker", "year", "yoy_similarity"]]
    ln  = pd.read_parquet(LENGTH_PARQUET)[["ticker", "year", "size",
                                           "len_1a", "len_1c", "len_combined"]]

    bp["boilerplate_ratio_scaled"] = bp["boilerplate_ratio"] * 10000

    # Drop any columns from bp that also exist in ln to avoid _x/_y suffixes
    overlap = [c for c in ln.columns if c in bp.columns and c not in ["ticker", "year"]]
    bp = bp.drop(columns=overlap, errors="ignore")

    df = bp.merge(sim, on=["ticker", "year"], how="left")
    df = df.merge(ln,  on=["ticker", "year"], how="left")
    return df


# ── 1. Boilerplate trend over time ────────────────────────────────────────────
def plot_boilerplate_trend(df):
    fig, ax = plt.subplots(figsize=(9, 5))
    yearly  = df.groupby("year")["boilerplate_ratio_scaled"].agg(["mean", "std"]).reset_index()

    ax.plot(yearly["year"], yearly["mean"], color="#C62828", linewidth=2.5,
            marker="o", markersize=6, zorder=3)
    ax.fill_between(yearly["year"], yearly["mean"] - yearly["std"],
                    yearly["mean"] + yearly["std"], alpha=0.15, color="#C62828")
    ax.axvline(x=2022.5, color=MANDATE_COLOR, linewidth=1.8, linestyle="--")
    ax.text(2022.55, ax.get_ylim()[1] * 0.97, "SEC Mandate", fontsize=8,
            fontstyle="italic", color=MANDATE_COLOR, va="top")

    ax.set_title("Boilerplate Density Over Time (Sample Mean ± SD)", fontsize=12, fontweight="bold", pad=12)
    ax.set_xlabel("Year", fontsize=10)
    ax.set_ylabel("Boilerplate Phrases per 10,000 Words", fontsize=10)
    ax.set_xticks([2022, 2023, 2024, 2025])
    ax.tick_params(labelsize=9)
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    plt.tight_layout()
    _save(fig, "boilerplate_trend.png")


# ── 2. Boilerplate by firm size ───────────────────────────────────────────────
def plot_boilerplate_by_size(df):
    size_order  = ["Large", "Medium", "Small"]
    size_colors = {"Large": "#D84315", "Medium": "#1565C0", "Small": "#2E7D32"}

    fig, ax = plt.subplots(figsize=(8, 5))
    sns.boxplot(data=df, x="size", y="boilerplate_ratio_scaled",
                order=size_order, hue="size", hue_order=size_order,
                palette=size_colors, legend=False, linewidth=1.2, width=0.5, ax=ax)
    sns.stripplot(data=df, x="size", y="boilerplate_ratio_scaled",
                  order=size_order, color="black", alpha=0.35, size=4, jitter=True, ax=ax)

    for i, size in enumerate(size_order):
        mv = df[df["size"] == size]["boilerplate_ratio_scaled"].mean()
        ax.text(i, mv + 0.3, f"μ={mv:.2f}", ha="center", fontsize=8,
                color="white", fontweight="bold",
                bbox=dict(boxstyle="round,pad=0.2", facecolor=size_colors[size],
                          alpha=0.85, edgecolor="none"))

    ax.set_title("Boilerplate Density by Firm Size (2022–2025)", fontsize=12, fontweight="bold", pad=12)
    ax.set_xlabel("Firm Size", fontsize=10)
    ax.set_ylabel("Boilerplate Phrases per 10,000 Words", fontsize=10)
    ax.tick_params(labelsize=9)
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    plt.tight_layout()
    _save(fig, "boilerplate_by_size.png")


# ── 3. Boilerplate by sector ──────────────────────────────────────────────────
def plot_boilerplate_by_sector(df):
    sector_order = (df.groupby("sector")["boilerplate_ratio_scaled"]
                    .median().sort_values(ascending=False).index.tolist())

    fig, ax = plt.subplots(figsize=(13, 6))
    sns.boxplot(data=df, x="sector", y="boilerplate_ratio_scaled",
                order=sector_order, hue="sector", hue_order=sector_order,
                palette="RdYlGn_r", legend=False, linewidth=1.2, ax=ax)
    sns.stripplot(data=df, x="sector", y="boilerplate_ratio_scaled",
                  order=sector_order, color="black", alpha=0.45, size=4, jitter=True, ax=ax)

    ax.set_title("Boilerplate Density by Sector (2022–2025)", fontsize=12, fontweight="bold", pad=12)
    ax.set_xlabel("Sector", fontsize=10)
    ax.set_ylabel("Boilerplate Phrases per 10,000 Words", fontsize=10)
    ax.tick_params(axis="x", labelsize=9, rotation=25)
    ax.tick_params(axis="y", labelsize=9)
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    plt.tight_layout()
    _save(fig, "boilerplate_by_sector.png")


# ── 4. Length: 1A vs 1C by year ──────────────────────────────────────────────
def plot_length_by_year(df):
    yearly = df.groupby("year")[["len_1a", "len_1c"]].mean().reset_index()
    x, width = np.arange(len(yearly)), 0.35

    fig, ax = plt.subplots(figsize=(9, 5))
    ax.bar(x - width/2, yearly["len_1a"], width, label="Item 1A", color="#1565C0", alpha=0.85)
    ax.bar(x + width/2, yearly["len_1c"], width, label="Item 1C", color="#F57F17", alpha=0.85)

    ax.set_title("Average Report Length by Section and Year", fontsize=12, fontweight="bold", pad=12)
    ax.set_xlabel("Year", fontsize=10)
    ax.set_ylabel("Average Word Count", fontsize=10)
    ax.set_xticks(x)
    ax.set_xticklabels(yearly["year"].astype(int))
    ax.tick_params(labelsize=9)
    ax.legend(fontsize=9)
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    plt.tight_layout()
    _save(fig, "length_by_year.png")


# ── 5. Length by size over time ───────────────────────────────────────────────
def plot_length_by_size_trend(df):
    size_colors = {"Large": "#D84315", "Medium": "#1565C0", "Small": "#2E7D32"}

    fig, ax = plt.subplots(figsize=(9, 5))
    for size, color in size_colors.items():
        subset = df[df["size"] == size].groupby("year")["len_combined"].mean().reset_index()
        ax.plot(subset["year"], subset["len_combined"], color=color, linewidth=2.2,
                marker="o", markersize=6, label=size, zorder=3)

    ax.axvline(x=2022.5, color=MANDATE_COLOR, linewidth=1.8, linestyle="--")
    ax.text(2022.55, ax.get_ylim()[1] * 0.97, "SEC Mandate", fontsize=8,
            fontstyle="italic", color=MANDATE_COLOR, va="top")

    ax.set_title("Average Combined Report Length by Firm Size Over Time", fontsize=12, fontweight="bold", pad=12)
    ax.set_xlabel("Year", fontsize=10)
    ax.set_ylabel("Average Word Count", fontsize=10)
    ax.set_xticks([2022, 2023, 2024, 2025])
    ax.tick_params(labelsize=9)
    ax.legend(title="Firm Size", fontsize=9, title_fontsize=9)
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    plt.tight_layout()
    _save(fig, "length_by_size_trend.png")


# ── 6. Length by sector over time ─────────────────────────────────────────────
def plot_length_by_sector_trend(df):
    sectors       = sorted(df["sector"].unique())
    sector_colors = {s: plt.cm.tab10.colors[i] for i, s in enumerate(sectors)}

    fig, ax = plt.subplots(figsize=(11, 6))
    for sector in sectors:
        subset = df[df["sector"] == sector].groupby("year")["len_combined"].mean().reset_index()
        ax.plot(subset["year"], subset["len_combined"], color=sector_colors[sector],
                linewidth=2, marker="o", markersize=5, label=sector, zorder=3)

    ax.axvline(x=2022.5, color=MANDATE_COLOR, linewidth=1.8, linestyle="--")
    ax.text(2022.55, ax.get_ylim()[1] * 0.97, "SEC Mandate", fontsize=8,
            fontstyle="italic", color=MANDATE_COLOR, va="top")

    ax.set_title("Average Combined Report Length by Sector Over Time", fontsize=12, fontweight="bold", pad=12)
    ax.set_xlabel("Year", fontsize=10)
    ax.set_ylabel("Average Word Count", fontsize=10)
    ax.set_xticks([2022, 2023, 2024, 2025])
    ax.tick_params(labelsize=9)
    ax.legend(title="Sector", fontsize=8, title_fontsize=8,
              loc="upper left", bbox_to_anchor=(1.01, 1), borderaxespad=0)
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    plt.tight_layout()
    _save(fig, "length_by_sector_trend.png")


# ── 7. Similarity histogram ───────────────────────────────────────────────────
def plot_similarity_histogram(df):
    sim_data = df["yoy_similarity"].dropna()

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.hist(sim_data, bins=20, color="#5C6BC0", edgecolor="white", linewidth=0.6, alpha=0.85)
    ax.axvline(sim_data.mean(),   color="#E53935", linewidth=2, linestyle="--",
               label=f"Mean ({sim_data.mean():.3f})")
    ax.axvline(sim_data.median(), color="#FF9800", linewidth=2, linestyle="-.",
               label=f"Median ({sim_data.median():.3f})")

    ax.set_title("Distribution of Year-over-Year Cosine Similarity Scores", fontsize=12, fontweight="bold", pad=12)
    ax.set_xlabel("Cosine Similarity", fontsize=10)
    ax.set_ylabel("Number of Filing Pairs", fontsize=10)
    ax.tick_params(labelsize=9)
    ax.legend(fontsize=9)
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    plt.tight_layout()
    _save(fig, "similarity_histogram.png")


# ── Helper ────────────────────────────────────────────────────────────────────
def _save(fig, filename):
    path = os.path.join(VISUALS_DIR, filename)
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"[INFO] Saved {path}")


# ── Main ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    df = load_data()
    plot_boilerplate_trend(df)
    plot_boilerplate_by_size(df)
    plot_boilerplate_by_sector(df)
    plot_length_by_year(df)
    plot_length_by_size_trend(df)
    plot_length_by_sector_trend(df)
    plot_similarity_histogram(df)
    print("\n[INFO] All visuals saved to:", VISUALS_DIR)