import pandas as pd
import nltk

nltk.download("punkt", quiet=True)

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


# ── Text Normalization ────────────────────────────────────────────────────────
def normalize(text):
    """Lowercase and collapse whitespace for consistent matching."""
    return " ".join(text.lower().split())


def preprocess(text):
    """Lowercase, remove punctuation, collapse whitespace for word counting."""
    text = text.lower()
    text = "".join(c if c.isalnum() or c.isspace() else " " for c in text)
    return " ".join(text.split())


# ── Boilerplate Detection ─────────────────────────────────────────────────────
def compute_boilerplate_ratio(text, phrases=BOILERPLATE_PHRASES):
    """
    Counts boilerplate phrase matches (B) and divides by total word count (N)
    after preprocessing.

    Returns:
        B     - number of boilerplate phrases matched
        N     - word count after preprocessing
        ratio - B / N
        matched_phrases - list of matched phrases for audit trail
    """
    if not text:
        return 0, 0, 0.0, []

    normalized_text  = normalize(text)
    preprocessed_text = preprocess(text)

    matched = [p for p in phrases if normalize(p) in normalized_text]
    B = len(matched)
    N = len(preprocessed_text.split())

    ratio = B / N if N > 0 else 0.0

    return B, N, ratio, matched


# ── Apply to Parquet ──────────────────────────────────────────────────────────
def run_boilerplate_detection(parquet_path="filings.parquet", output_path="boilerplate_results"):
    df = pd.read_parquet(parquet_path)

    results = df["combined_text"].apply(
        lambda text: compute_boilerplate_ratio(text)
    )

    df["boilerplate_count"] = results.apply(lambda x: x[0])
    df["word_count"]        = results.apply(lambda x: x[1])
    df["boilerplate_ratio"] = results.apply(lambda x: x[2])
    df["matched_phrases"]   = results.apply(lambda x: x[3])

    # Save parquet (for further pipeline steps)
    df.to_parquet(f"{output_path}.parquet", index=False)
    print(f"[INFO] Saved {output_path}.parquet")

    # Save CSV for inspection — drop combined_text to keep it readable,
    # and convert matched_phrases list to a semicolon-separated string
    csv_df = df.drop(columns=["combined_text"])
    csv_df["matched_phrases"] = csv_df["matched_phrases"].apply(lambda x: " ; ".join(x) if x else "")
    csv_df.to_csv(f"{output_path}.csv", index=False)
    print(f"[INFO] Saved {output_path}.csv")

    return df


# ── Main ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    df = run_boilerplate_detection()
    print(df[["ticker", "sector", "year", "boilerplate_count", "word_count", "boilerplate_ratio"]].to_string())