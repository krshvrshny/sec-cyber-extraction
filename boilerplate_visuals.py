import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

PARQUET_PATH        = "boilerplate_results.parquet"
LENGTH_PARQUET_PATH = "length_results.parquet"
VISUALS_DIR         = "visuals"

os.makedirs(VISUALS_DIR, exist_ok=True)


def load_data(parquet_path=PARQUET_PATH, length_parquet_path=LENGTH_PARQUET_PATH):
    bp_df    = pd.read_parquet(parquet_path)
    len_df   = pd.read_parquet(length_parquet_path)[["ticker", "year", "size"]].drop_duplicates()

    # If size already in boilerplate parquet use it, otherwise merge from length
    if "size" not in bp_df.columns or bp_df["size"].isna().all():
        df = bp_df.merge(len_df, on=["ticker", "year"], how="left")
    else:
        df = bp_df.copy()

    df["boilerplate_ratio_scaled"] = df["boilerplate_ratio"] * 10000
    return df


def plot_by_size(df, output_dir=VISUALS_DIR):
    size_order  = ["Large", "Medium", "Small"]
    size_colors = {"Large": "#2196F3", "Medium": "#FF9800", "Small": "#4CAF50"}

    fig, ax = plt.subplots(figsize=(8, 5))

    sns.boxplot(
        data=df,
        x="size", y="boilerplate_ratio_scaled",
        order=size_order, hue="size", hue_order=size_order,
        palette=size_colors, legend=False, linewidth=1.2, width=0.5, ax=ax
    )
    sns.stripplot(
        data=df,
        x="size", y="boilerplate_ratio_scaled",
        order=size_order, color="black", alpha=0.35, size=4, jitter=True, ax=ax
    )

    for i, size in enumerate(size_order):
        mean_val = df[df["size"] == size]["boilerplate_ratio_scaled"].mean()
        ax.text(i, mean_val + 0.3, f"μ={mean_val:.2f}", ha="center",
                fontsize=8, color="black", fontweight="bold")

    ax.set_title("Boilerplate Density by Firm Size (2022–2025)", fontsize=12, fontweight="bold", pad=12)
    ax.set_xlabel("Firm Size", fontsize=10)
    ax.set_ylabel("Boilerplate Phrases per 10,000 Words", fontsize=10)
    ax.tick_params(labelsize=9)
    ax.grid(axis="y", linestyle="--", alpha=0.4)

    plt.tight_layout()
    path = os.path.join(output_dir, "boilerplate_by_size.png")
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"[INFO] Saved {path}")


def plot_by_sector(df, output_dir=VISUALS_DIR):
    sector_order = (
        df.groupby("sector")["boilerplate_ratio_scaled"]
        .median().sort_values(ascending=False).index.tolist()
    )

    fig, ax = plt.subplots(figsize=(13, 6))

    sns.boxplot(
        data=df,
        x="sector", y="boilerplate_ratio_scaled",
        order=sector_order, hue="sector", hue_order=sector_order,
        palette="RdYlGn_r", legend=False, linewidth=1.2, ax=ax
    )
    sns.stripplot(
        data=df,
        x="sector", y="boilerplate_ratio_scaled",
        order=sector_order, color="black", alpha=0.45, size=4, jitter=True, ax=ax
    )

    ax.set_title("Boilerplate Density by Sector (2022–2025)", fontsize=12, fontweight="bold", pad=12)
    ax.set_xlabel("Sector", fontsize=10)
    ax.set_ylabel("Boilerplate Phrases per 10,000 Words", fontsize=10)
    ax.tick_params(axis="x", labelsize=9, rotation=25)
    ax.tick_params(axis="y", labelsize=9)
    ax.grid(axis="y", linestyle="--", alpha=0.4)

    plt.tight_layout()
    path = os.path.join(output_dir, "boilerplate_by_sector.png")
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"[INFO] Saved {path}")


if __name__ == "__main__":
    df = load_data()
    plot_by_size(df)
    plot_by_sector(df)
    print("\n[INFO] Done. Visuals saved to:", VISUALS_DIR)