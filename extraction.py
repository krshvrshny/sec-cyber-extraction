import os
import time
import logging
import warnings
import pandas as pd
from edgar import Company, set_identity
from concurrent.futures import ThreadPoolExecutor, as_completed

# ── Identity ─────────────────────────────────────────────────────────────────
set_identity("Krish Varshney krish.varshney@tum.de")
warnings.filterwarnings("ignore")
logging.disable(logging.WARNING)

# ── Config ────────────────────────────────────────────────────────────────────
BASE_FOLDER  = "extractions"
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


# ── Helpers ───────────────────────────────────────────────────────────────────
def get_filing_for_year(filings, target_year):
    for filing in filings:
        if int(filing.period_of_report[:4]) == target_year and filing.form == "10-K":
            return filing
    return None


def save_to_file(base_folder, sector, ticker, full_name, year, section_name, content_obj):
    """Saves raw section text as a txt backup."""
    if content_obj is None:
        return
    clean_name     = full_name.replace(".", "").replace(",", "").replace("/", "-")
    company_folder = f"{ticker} ({clean_name})"
    directory      = os.path.join(base_folder, sector, company_folder, str(year))
    os.makedirs(directory, exist_ok=True)
    filepath = os.path.join(directory, f"{ticker}_{section_name}.txt")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(str(content_obj))


# ── Per-ticker extraction ─────────────────────────────────────────────────────
def process_ticker(sector, ticker, target_years):
    records = []
    try:
        company   = Company(ticker)
        full_name = company.name
        filings   = company.get_filings(form="10-K")

        for year in target_years:
            filing = get_filing_for_year(filings, year)
            if filing is None:
                print(f"[SKIP] {ticker} {year}: No filing found")
                continue

            print(f"[PROCESSING] {ticker} {year}")
            try:
                doc = filing.obj()

                # Section 1A
                item_1a      = doc.risk_factors
                item_1a_text = str(item_1a) if item_1a is not None else None
                save_to_file(BASE_FOLDER, sector, ticker, full_name, year, "Item_1A_RiskFactors", item_1a)

                # Section 1C (2023+ only)
                item_1c_text = None
                if year >= 2023:
                    try:
                        item_1c      = doc["Item 1C"]
                        item_1c_text = str(item_1c) if item_1c is not None else None
                        save_to_file(BASE_FOLDER, sector, ticker, full_name, year, "Item_1C_Cybersecurity", item_1c)
                    except Exception:
                        print(f"[INFO] {ticker} {year}: No Item 1C found, skipping")

                # Combine — delimiter makes it easy to split back apart if needed
                parts         = [p for p in [item_1a_text, item_1c_text] if p]
                combined_text = "\n\n--- ITEM 1C ---\n\n".join(parts) if len(parts) == 2 else (parts[0] if parts else None)

                records.append({
                    "ticker":        ticker,
                    "company_name":  full_name,
                    "sector":        sector,
                    "year":          year,
                    "has_1c":        item_1c_text is not None,
                    "combined_text": combined_text,
                })

                time.sleep(0.4)

            except Exception as e:
                print(f"[ERROR] {ticker} {year}: {e}")

    except Exception as e:
        print(f"[ERROR] {ticker}: {e}")

    return records


# ── Parallel extraction ───────────────────────────────────────────────────────
def run_extraction(sectors_dict, target_years):
    tasks = [
        (sector, ticker)
        for sector, tickers in sectors_dict.items()
        for ticker in tickers
    ]

    all_records = []
    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = {
            executor.submit(process_ticker, sector, ticker, target_years): (sector, ticker)
            for sector, ticker in tasks
        }
        for future in as_completed(futures):
            sector, ticker = futures[future]
            try:
                all_records.extend(future.result())
            except Exception as e:
                print(f"[ERROR] {ticker}: {e}")

    return all_records


# ── Save to parquet ───────────────────────────────────────────────────────────
def consolidate_to_parquet(records, output_path=PARQUET_PATH):
    df = pd.DataFrame(records)
    df = df.sort_values(["sector", "ticker", "year"]).reset_index(drop=True)
    df.to_parquet(output_path, index=False)
    print(f"\n[INFO] Saved {len(df)} records to {output_path}")
    return df


# ── Main ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    records = run_extraction(SECTORS_DICT, TARGET_YEARS)
    df      = consolidate_to_parquet(records)

    print("\n[INFO] Done.")
    print(df[["ticker", "sector", "year", "has_1c"]].to_string())