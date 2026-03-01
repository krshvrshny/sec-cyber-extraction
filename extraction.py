import os
import time
import logging
import warnings
import requests
import pandas as pd
from bs4 import BeautifulSoup
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
# MANUAL OVERRIDES
# -----------------------------------------------------------------------------
# Use this when a filing fails automatic extraction but you know it exists.
#
# HOW TO FIND THE URL:
#   1. Go to https://efts.sec.gov/LATEST/search-index?q=%22TICKER%22&dateRange=custom&startdt=YEAR-01-01&enddt=YEAR-12-31&forms=10-K
#      (or just search on https://www.sec.gov/cgi-bin/browse-edgar)
#   2. Open the filing index page
#   3. Find the primary .htm document (usually the largest one)
#   4. Copy that URL and paste below
#
# FORMAT:
#   ("TICKER", YEAR): ("url_to_full_10k_document", "url_to_1C_if_separate_or_None"),
#
# EXAMPLE:
#   ("NVEC", 2022): ("https://www.sec.gov/Archives/edgar/data/72971/000007297122000007/nvec10k2022.htm", None),
# =============================================================================

MANUAL_OVERRIDES = {
    ("ELMD", 2022): ("https://www.sec.gov/ix?doc=/Archives/edgar/data/0001488917/000089710122000805/elmd221010_10k.htm",    None),
    ("ELMD", 2023): ("https://www.sec.gov/ix?doc=/Archives/edgar/data/0001488917/000089710123000380/elmd230887_10k.htm",    None),
    ("ELMD", 2024): ("https://www.sec.gov/ix?doc=/Archives/edgar/data/0001488917/000089710124000422/elmd240883_10k.htm",    None),
    ("ELMD", 2025): ("https://www.sec.gov/ix?doc=/Archives/edgar/data/0001488917/000143774925027761/elmd20250630_10k.htm",  None),
    ("NVEC", 2022): ("https://www.sec.gov/ix?doc=/Archives/edgar/data/0000724910/000143774922010855/nvec20220331_10k.htm",  None),
    ("NVEC", 2024): ("https://www.sec.gov/ix?doc=/Archives/edgar/data/0000724910/000137647424000214/nvec-20240331.htm",     None),
    ("NVEC", 2025): ("https://www.sec.gov/ix?doc=/Archives/edgar/data/0000724910/000137647425000437/nvec-20250331.htm",     None),
}

# =============================================================================
# HELPERS
# =============================================================================

SEC_HEADERS = {"User-Agent": "Krish Varshney krish.varshney@tum.de"}


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
    """Fallback: search the raw filing text by section header keyword."""
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


def fetch_from_url(url, section_headers):
    """
    Fetch a document directly from SEC EDGAR and extract the relevant section.
    Automatically strips the inline XBRL viewer prefix (/ix?doc=...) if present.
    """
    # Strip inline XBRL viewer wrapper — the real document is after /ix?doc=
    if "/ix?doc=" in url:
        url = "https://www.sec.gov" + url.split("/ix?doc=")[1]

    try:
        resp = requests.get(url, headers=SEC_HEADERS, timeout=30)
        resp.raise_for_status()

        # Strip HTML
        soup = BeautifulSoup(resp.text, "html.parser")
        text = soup.get_text(separator=" ")
        text = " ".join(text.split())  # normalize whitespace

        if not section_headers:
            # No specific section wanted — return the whole cleaned text
            return text if len(text.split()) >= 100 else None

        # Search for specific section
        text_lower = text.lower()
        for header in section_headers:
            idx = text_lower.find(header.lower())
            if idx == -1:
                continue
            chunk = text[idx:idx + 15000].strip()
            if len(chunk.split()) >= 100:
                return chunk

    except Exception as e:
        print(f"        [URL FETCH ERROR] {url}: {e}")
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

                # ── Item 1A ────────────────────────────────────────────────
                item_1a_text = None

                # Check manual override first
                override = MANUAL_OVERRIDES.get((ticker, year))
                if override and override[0]:
                    item_1a_text = fetch_from_url(override[0], [
                        "item 1a", "item 1a.", "risk factors", "1a. risk factors",
                    ])
                    if item_1a_text:
                        print(f"        {ticker} {year} Item 1A: manual override OK")

                # Structured parse
                if not is_valid_text(item_1a_text):
                    item_1a = doc.risk_factors
                    item_1a_text = str(item_1a) if is_valid_text(item_1a) else None

                # Raw fallback
                if not is_valid_text(item_1a_text):
                    item_1a_text = raw_search(filing, [
                        "item 1a", "item 1a.", "risk factors", "1a. risk factors",
                    ])
                    status = "raw fallback OK" if item_1a_text else "FAILED — add to MANUAL_OVERRIDES"
                    print(f"        {ticker} {year} Item 1A: {status}")

                # ── Item 1C (2023+ only) ───────────────────────────────────
                item_1c_text = None
                if year >= 2023:
                    # Check manual override
                    if override and override[1]:
                        item_1c_text = fetch_from_url(override[1], [
                            "item 1c", "item 1c.", "cybersecurity", "1c. cybersecurity",
                        ])
                        if item_1c_text:
                            print(f"        {ticker} {year} Item 1C: manual override OK")

                    # Structured parse
                    if not is_valid_text(item_1c_text):
                        try:
                            item_1c      = doc["Item 1C"]
                            item_1c_text = str(item_1c) if is_valid_text(item_1c) else None
                        except Exception:
                            pass

                    # Raw fallback
                    if not is_valid_text(item_1c_text):
                        item_1c_text = raw_search(filing, [
                            "item 1c", "item 1c.", "cybersecurity risk management", "1c. cybersecurity",
                        ])
                        status = "raw fallback OK" if item_1c_text else "not found"
                        print(f"        {ticker} {year} Item 1C: {status}")

                # ── Combine ────────────────────────────────────────────────
                parts = [p for p in [item_1a_text, item_1c_text] if is_valid_text(p)]
                if len(parts) == 2:
                    combined = parts[0] + "\n\n--- ITEM 1C ---\n\n" + parts[1]
                elif len(parts) == 1:
                    combined = parts[0]
                else:
                    combined = None
                    print(f"[WARN]  {ticker} {year}: no text extracted — add URL to MANUAL_OVERRIDES")

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

    df = pd.DataFrame(records)
    df = df.sort_values(["sector", "ticker", "year"]).reset_index(drop=True)
    df.to_parquet(PARQUET_PATH, index=False)

    print(f"\n[DONE] {saved_txt} txt files saved to '{OUTPUT_DIR}/'")
    print(f"[DONE] {len(df)} records saved to '{PARQUET_PATH}'")

    summary = df.copy()
    summary["chars"] = summary["combined_text"].fillna("").str.len()
    print(f"\n{summary[['ticker', 'sector', 'year', 'has_1c', 'chars']].to_string()}")

    # Flag empty extractions
    empty = summary[summary["chars"] == 0]
    if not empty.empty:
        print(f"\n[ACTION REQUIRED] {len(empty)} filings with no text — add their URLs to MANUAL_OVERRIDES:")
        for _, row in empty.iterrows():
            print(f"  ({row['ticker']!r}, {row['year']}): search https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&type=10-K&dateb=&owner=include&count=40&search_text=&company={row['ticker']}")

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