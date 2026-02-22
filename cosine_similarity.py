import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

PARQUET_PATH = "boilerplate_results.parquet"
OUTPUT_PATH  = "similarity_results"


def compute_yoy_similarity(current_text, previous_text):
    if not current_text or not previous_text:
        return None
    vectorizer = TfidfVectorizer(ngram_range=(4, 6))
    tfidf      = vectorizer.fit_transform([current_text, previous_text])
    score      = cosine_similarity(tfidf[0:1], tfidf[1:2])[0][0]
    return round(float(score), 4)


def run_similarity(parquet_path=PARQUET_PATH, output_path=OUTPUT_PATH):
    df = pd.read_parquet(parquet_path)
    df = df.sort_values(["ticker", "year"]).reset_index(drop=True)

    similarity_scores = []
    for idx, row in df.iterrows():
        ticker        = row["ticker"]
        current_year  = row["year"]
        current_text  = row["combined_text"]
        previous_rows = df[(df["ticker"] == ticker) & (df["year"] == current_year - 1)]

        if previous_rows.empty:
            similarity_scores.append(None)
        else:
            previous_text = previous_rows.iloc[0]["combined_text"]
            similarity_scores.append(compute_yoy_similarity(current_text, previous_text))

    df["yoy_similarity"] = similarity_scores

    # Parquet keeps combined_text for downstream steps
    df[["ticker", "company_name", "sector", "year", "has_1c",
        "yoy_similarity", "combined_text"]].to_parquet(f"{output_path}.parquet", index=False)
    print(f"[INFO] Saved {output_path}.parquet")

    return df


if __name__ == "__main__":
    df = run_similarity()
    print("\n[INFO] Done.")
    print(df[["ticker", "sector", "year", "yoy_similarity"]].to_string())