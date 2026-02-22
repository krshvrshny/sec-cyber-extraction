import pandas as pd
import nltk

nltk.download("punkt", quiet=True)

PARQUET_PATH = "length_results.parquet"
OUTPUT_PATH  = "boilerplate_results"

BOILERPLATE_PHRASES = [
    # Hedging & uncertainty
    "we cannot guarantee",
    "we cannot assure",
    "we may be subject to",
    "we may experience",
    "there can be no assurance",
    "we cannot predict",
    "from time to time",
    "could adversely affect",
    "may adversely affect",
    "might adversely affect",
    "could have a material adverse effect",
    "may not be sufficient",
    # Generic threat acknowledgment
    "evolving threat landscape",
    "sophisticated cyberattacks",
    "continue to evolve",
    "growing number of cyber",
    "threat actors",
    "malicious actors",
    "unauthorized access to our systems",
    "risks from cyber",
    # Vague controls
    "reasonable security measures",
    "industry standard",
    "security measures in place",
    "we have implemented controls",
    "may not be effective",
    "regularly assess",
    # Regulatory boilerplate
    "applicable laws and regulations",
    "evolving regulatory landscape",
    "monitor and assess",
    "subject to various laws",
    # Effort without specificity
    "take security seriously",
    "cybersecurity is a priority",
    "committed to protecting",
    "we devote significant resources",
    "continue to invest in cyber",
    "dedicated to cybersecurity",
]


def normalize(text):
    return " ".join(text.lower().split())


def compute_boilerplate(text, word_count, phrases=BOILERPLATE_PHRASES):
    if not text or word_count == 0:
        return 0, 0.0, []
    normalized_text = normalize(text)
    matched         = [p for p in phrases if normalize(p) in normalized_text]
    B               = len(matched)
    ratio           = B / word_count
    return B, round(ratio, 6), matched


def run_boilerplate_detection(parquet_path=PARQUET_PATH, output_path=OUTPUT_PATH):
    df = pd.read_parquet(parquet_path)

    results = df.apply(
        lambda row: compute_boilerplate(row["combined_text"], row["len_combined"]),
        axis=1
    )

    df["boilerplate_count"] = results.apply(lambda x: x[0])
    df["boilerplate_ratio"] = results.apply(lambda x: x[1])
    df["matched_phrases"]   = results.apply(lambda x: x[2])

    # Parquet keeps combined_text and size for downstream steps
    df.to_parquet(f"{output_path}.parquet", index=False)
    print(f"[INFO] Saved {output_path}.parquet")

    return df


if __name__ == "__main__":
    df = run_boilerplate_detection()
    print("\n[INFO] Done.")
    print(df[["ticker", "sector", "year", "boilerplate_count", "boilerplate_ratio"]].to_string())