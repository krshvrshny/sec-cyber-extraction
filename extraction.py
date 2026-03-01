import os
import time
import logging
import warnings
import pandas as pd
from edgar import Company, set_identity
from concurrent.futures import ThreadPoolExecutor, as_completed

set_identity("Krish Varshney krish.varshney@tum.de")
warnings.filterwarnings("ignore")
logging.disable(logging.WARNING)

# =============================================================================
# CONFIG
# =============================================================================

OUTPUT_DIR   = "data"
PARQUET_PATH = "filings.parquet"
TARGET_YEARS = [2022, 2023, 2024, 2025]

SECTORS_DICT = {
    "Consumer Goods":      ["CROX", "ELF", "MCFT", "NKE", "PEP", "WGO"],
    "Cybersecurity":       ["CRWD", "PANW", "PRGS", "RPD", "S", "VRNS"],
    "Finance":             ["HLI", "LC", "PSEC", "UPST", "V"],
    "Healthcare":          ["ELMD", "JNJ", "LLY", "MODD", "MOH", "VKTX"],
    "Retail & E-Commerce": ["AMZN", "BOOT", "ETSY", "SFIX", "UPWK"],
    "Semiconductors":      ["AMD", "CRUS", "INTC", "MXL", "NVEC", "POWI"],
    "Technology":          ["AAPL", "AMPL", "GOOGL", "GTLB", "MSFT", "SCSC", "U"],
}

# =============================================================================
# HELPERS
# =============================================================================

def is_valid_text(text):
    """Reject None, 'None', empty strings, and extractions under 100 words."""
    if text is None:
        return False
    s = str(text).strip()
    if s.lower() in ("none", "nan", "", "n/a"):
        return False
    return len(s.split()) >= 100


def get_filing_for_year(filings, target_year):
    for filing in filings:
        if int(filing.period_of_report[:4]) == target_year and filing.form == "10-K":
            return filing
    return None


def raw_search(filing, headers):
    """
    Fallback for when the edgar structured parser returns nothing.
    Searches the raw filing text for the section by header keyword.
    """
    try:
        raw       = str(filing.document)
        raw_lower = raw.lower()
        for header in headers:
            idx = raw_lower.find(header.lower())
            if idx == -1:
                continue
            chunk = raw[idx:idx + 15000].strip()
            if len(chunk.split()) >= 100:
                return chunk
    except Exception:
        pass
    return None


# =============================================================================
# PER-TICKER EXTRACTION
# =============================================================================

def process_ticker(sector, ticker, target_years):
    records = []
    try:
        company   = Company(ticker)
        full_name = company.name
        filings   = company.get_filings(form="10-K")

        for year in target_years:
            filing = get_filing_for_year(filings, year)
            if filing is None:
                print(f"[SKIP]  {ticker} {year}: no 10-K found")
                continue

            print(f"[START] {ticker} {year}")
            try:
                doc = filing.obj()

                # Item 1A
                item_1a      = doc.risk_factors
                item_1a_text = str(item_1a) if is_valid_text(item_1a) else None
                if not is_valid_text(item_1a_text):
                    item_1a_text = raw_search(filing, [
                        "item 1a", "item 1a.", "risk factors", "1a. risk factors",
                    ])
                    status = "raw fallback" if item_1a_text else "FAILED"
                    print(f"        {ticker} {year} Item 1A via {status}")

                # Item 1C (2023+ only)
                item_1c_text = None
                if year >= 2023:
                    try:
                        item_1c      = doc["Item 1C"]
                        item_1c_text = str(item_1c) if is_valid_text(item_1c) else None
                    except Exception:
                        pass
                    if not is_valid_text(item_1c_text):
                        item_1c_text = raw_search(filing, [
                            "item 1c", "item 1c.", "cybersecurity risk management", "1c. cybersecurity",
                        ])
                        status = "raw fallback" if item_1c_text else "not found"
                        print(f"        {ticker} {year} Item 1C via {status}")

                # Combine
                parts = [p for p in [item_1a_text, item_1c_text] if is_valid_text(p)]
                if len(parts) == 2:
                    combined = parts[0] + "\n\n--- ITEM 1C ---\n\n" + parts[1]
                elif len(parts) == 1:
                    combined = parts[0]
                else:
                    combined = None
                    print(f"[WARN]  {ticker} {year}: no text extracted")

                records.append({
                    "ticker":        ticker,
                    "company_name":  full_name,
                    "sector":        sector,
                    "year":          year,
                    "has_1c":        is_valid_text(item_1c_text),
                    "combined_text": combined,
                })

                time.sleep(0.4)

            except Exception as e:
                print(f"[ERROR] {ticker} {year}: {e}")

    except Exception as e:
        print(f"[ERROR] {ticker}: {e}")

    return records


# =============================================================================
# SAVE OUTPUTS
# =============================================================================

def save_outputs(records):
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Clear old txt files
    for f in os.listdir(OUTPUT_DIR):
        if f.endswith(".txt"):
            os.remove(os.path.join(OUTPUT_DIR, f))

    saved_txt = 0
    for r in records:
        if not r["combined_text"]:
            continue
        filepath = os.path.join(OUTPUT_DIR, f"{r['ticker']}_{r['year']}.txt")
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(r["combined_text"])
        saved_txt += 1

    # Parquet
    df = pd.DataFrame(records)
    df = df.sort_values(["sector", "ticker", "year"]).reset_index(drop=True)
    df.to_parquet(PARQUET_PATH, index=False)

    print(f"\n[DONE] {saved_txt} txt files saved to '{OUTPUT_DIR}/'")
    print(f"[DONE] {len(df)} records saved to '{PARQUET_PATH}'")

    summary = df.copy()
    summary["chars"] = summary["combined_text"].fillna("").str.len()
    print(f"\n{summary[['ticker', 'sector', 'year', 'has_1c', 'chars']].to_string()}")

    return df


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    tasks = [
        (sector, ticker)
        for sector, tickers in SECTORS_DICT.items()
        for ticker in tickers
    ]

    all_records = []
    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = {
            executor.submit(process_ticker, sector, ticker, TARGET_YEARS): ticker
            for sector, ticker in tasks
        }
        for future in as_completed(futures):
            ticker = futures[future]
            try:
                all_records.extend(future.result())
            except Exception as e:
                print(f"[ERROR] {ticker}: {e}")

    save_outputs(all_records)