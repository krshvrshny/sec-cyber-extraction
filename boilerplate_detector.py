import pandas as pd
import nltk

nltk.download("punkt", quiet=True)

# ── Config ────────────────────────────────────────────────────────────────────
PARQUET_PATH = "length_results.parquet"
OUTPUT_PATH  = "boilerplate_results"

# ── Boilerplate Dictionary ────────────────────────────────────────────────────
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
    "increasingly sophisticated attacks",
    "cybersecurity threats continue to evolve",
    "growing number of cyber threats",
    "threat actors",
    "malicious actors",
    "unauthorized access to our systems",
    "we face risks from cyberattacks",
    "cybersecurity incidents could affect",
    # Vague controls
    "appropriate technical measures",
    "reasonable security measures",
    "industry standard practices",
    "security measures in place",
    "we have implemented controls",
    "we maintain security policies",
    "security measures may not be effective",
    "we regularly review our security",
    # Regulatory boilerplate
    "applicable laws and regulations",
    "evolving regulatory landscape",
    "we monitor regulatory developments",
    "compliance with applicable requirements",
    "subject to various laws and regulations",
    "regulatory requirements continue to evolve",
    # Effort without specificity
    "we take cybersecurity seriously",
    "cybersecurity is a priority",
    "we are committed to protecting",
    "we devote significant resources",
    "we continue to invest in cybersecurity",
    "we have a dedicated team",
]


# ── Normalization ─────────────────────────────────────────────────────────────
def normalize(text):
    """Lowercase and collapse whitespace for consistent matching."""
    return " ".join(text.lower().split())


# ── Boilerplate Detection ─────────────────────────────────────────────────────
def compute_boilerplate(text, word_count, phrases=BOILERPLATE_PHRASES):
    """
    Counts boilerplate phrase matches (B) and divides by len_combined (N)
    from the length analysis step.

    Returns:
        B               - number of boilerplate phrases matched
        boilerplate_ratio - B / N
        matched_phrases - list of matched phrases for audit trail
    """
    if not text or word_count == 0:
        return 0, 0.0, []

    normalized_text = normalize(text)
    matched         = [p for p in phrases if normalize(p) in normalized_text]
    B               = len(matched)
    ratio           = B / word_count

    return B, round(ratio, 6), matched


# ── Main ──────────────────────────────────────────────────────────────────────
def run_boilerplate_detection(parquet_path=PARQUET_PATH, output_path=OUTPUT_PATH):
    df = pd.read_parquet(parquet_path)

    results = df.apply(
        lambda row: compute_boilerplate(row["combined_text"], row["len_combined"]),
        axis=1
    )

    df["boilerplate_count"] = results.apply(lambda x: x[0])
    df["boilerplate_ratio"] = results.apply(lambda x: x[1])
    df["matched_phrases"]   = results.apply(lambda x: x[2])

    # ── Parquet: keep combined_text for downstream pipeline steps ─────────────
    df.to_parquet(f"{output_path}.parquet", index=False)
    print(f"[INFO] Saved {output_path}.parquet")

    # ── CSV: only boilerplate-relevant columns, no combined_text ─────────────
    csv_df = df[["ticker", "company_name", "sector", "year", "has_1c",
                 "boilerplate_count", "boilerplate_ratio", "matched_phrases"]]
    csv_df["matched_phrases"] = csv_df["matched_phrases"].apply(
        lambda x: " ; ".join(x) if x else ""
    )
    csv_df.to_csv(f"{output_path}.csv", index=False)
    print(f"[INFO] Saved {output_path}.csv")

    return df


if __name__ == "__main__":
    df = run_boilerplate_detection()
    print("\n[INFO] Done.")
    print(df[["ticker", "sector", "year", "boilerplate_count", "boilerplate_ratio"]].to_string())