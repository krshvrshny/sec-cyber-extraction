import os
from edgar import Company, set_identity
import warnings
import time
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

# 1. Identifikation
set_identity("Krish Varshney krish.varshney@tum.de")

warnings.filterwarnings("ignore")
logging.disable(logging.WARNING)


def save_to_file(base_folder, sector, ticker, full_name, year, section_name, content_obj):
    if content_obj is None:
        return
    
    clean_name = full_name.replace(".", "").replace(",", "").replace("/", "-")
    company_name = f"{ticker} ({clean_name})"
    
    # Pfad erstellen
    directory = f"{base_folder}/{sector}/{company_name}/{year}"
    if not os.path.exists(directory):
        os.makedirs(directory)
    
    filename = f"{directory}/{ticker}_{section_name}.txt"
    
    with open(filename, "w", encoding="utf-8") as f:
        f.write(str(content_obj))

def get_filing_for_year(filings, target_year):
    for filing in filings:
        if int(filing.period_of_report[:4]) == target_year and filing.form == "10-K":
            return filing
    return None

def process_ticker(sector, ticker, target_years):
    base_folder = "extractions"
    try:
        company = Company(ticker)
        full_name = company.name
        filings = company.get_filings(form="10-K")
        
        for year in target_years:
            filing = get_filing_for_year(filings, year)
            
            if filing is None:
                print(f"[SKIP] {ticker} {year}: No filing found")
                continue
            
            print(f"[PROCESSING] {ticker} {year}")
            
            try:
                doc = filing.obj()
                
                item_1a = doc.risk_factors
                save_to_file(base_folder, sector, ticker, full_name, year, "Item_1A_RiskFactors", item_1a)
                
                if year >= 2023:
                    try:
                        item_1c = doc['Item 1C']
                        save_to_file(base_folder, sector, ticker, full_name, year, "Item_1C_Cybersecurity", item_1c)
                    except:
                        print(f"[INFO] {ticker} {year}: No Item 1C found, skipping")
                
                time.sleep(0.4)
            
            except Exception as e:
                print(f"[ERROR] {ticker} {year}: {e}")
    
    except Exception as e:
        print(f"[ERROR] {ticker}: {e}")

def run_extraction(sectors_dict, target_years):
    # Build flat list of (sector, ticker) pairs
    tasks = [(sector, ticker) for sector, tickers in sectors_dict.items() for ticker in tickers]
    
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(process_ticker, sector, ticker, target_years): (sector, ticker) 
                  for sector, ticker in tasks}
        
        for future in as_completed(futures):
            sector, ticker = futures[future]
            try:
                future.result()
            except Exception as e:
                print(f"[ERROR] {ticker}: {e}")

data_sample = {
    "Automotive": ["F", "TSLA"],
    "Consumer Goods": ["CROX", "ELF", "MCFT", "NKE", "PEP", "WGO"],
    "Cybersecurity": ["CRWD", "PANW", "PRGS", "RPD", "S", "VRNS"],
    "Finance": ["HLI", "LC", "PSEC", "UPST", "V"],
    "Healthcare": ["ELMD", "JNJ", "LLY", "MODD", "MOH", "VKTX"],
    "Retail & E-Commerce": ["AMZN", "BOOT", "ETSY", "SFIX", "UPWK"],
    "Semiconductors": ["AMD", "CRUS", "INTC", "MXL", "NVEC", "POWI"],
    "Technology": ["AAPL", "AMPL", "GOOGL", "GTLB", "MSFT", "SCSC", "U"]
}

target_years = [2022, 2023, 2024, 2025]

run_extraction(data_sample, target_years)

print("\n[INFO] Done.")