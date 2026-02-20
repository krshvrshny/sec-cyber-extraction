import os
from edgar import Company, set_identity
import warnings
import time
import logging

# 1. Identifikation
set_identity("Krish Varshney krish.varshney@tum.de")

warnings.filterwarnings("ignore")
logging.disable(logging.WARNING)

#deleted format company name since edgar library already formats it well

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
        if filing.filing_date.year == target_year:
            return filing
    return None

def run_extraction(sectors_dict, target_years):
    base_folder = "extractions"

    for sector, tickers in sectors_dict.items():
        print(f"\n[SECTOR] {sector.upper()}")
        for ticker in tickers:
            try:
                company = Company(ticker)
                full_name = company.name
                
                #get 10-k
                filings = company.get_filings(form="10-K")

                for year in target_years:
                    filing = get_filing_for_year(filings, year)
                    if filing is None:
                        print(f"[SKIP] {ticker} {year}: No filing found")
                        continue
                    
                    print(f"[PROCESSING] {ticker} {year}")

                    try:
                        doc = filing.obj()
                        
                        # Item 1A - available for all years
                        item_1a = doc.risk_factors
                        save_to_file(base_folder, sector, ticker, full_name, year, "Item_1A_RiskFactors", item_1a)
                        
                        # Item 1C - only available 2023+ (and not always 2023)
                        if year >= 2023:
                            try:
                                item_1c = doc['Item 1C']
                                save_to_file(base_folder, sector, ticker, full_name, year, "Item_1C_Cybersecurity", item_1c)
                            except:
                                print(f"   [INFO] {ticker} {year}: No Item 1C found, skipping")
                        
                        time.sleep(0.4)
                    
                    except Exception as e:
                        print(f"      [ERROR] {ticker} {year}: {e}")
            
            except Exception as e:
                print(f"      [ERROR] {ticker}: {e}")

data_sample = {
    "Automotive": ["F", "TSLA"],
    "Consumer Goods": ["CROX", "ELF", "MCFT", "NKE", "PEP", "WGO"],
    "Cybersecurity": ["CRWD", "PANW", "PRGS", "RPD", "S", "VRNS"],
    "Finance": ["HLI", "LC", "PSEC", "UPST", "V"],
    "Healthcare": ["ELMD", "JNJ", "LLY", "MODD", "MOH", "VKTX"],
    "Retail & E-Commerce": ["AMZN", "BOOT", "ETSY", "TDUP", "UPWK"],
    "Semiconductors": ["AMD", "CRUS", "INTC", "MXL", "NVEC", "POWI"],
    "Technology": ["AAPL", "AMPL", "GOOGL", "GTLB", "MSFT", "SCSC", "U"]
}

target_years = [2022, 2023, 2024, 2025]

run_extraction(data_sample, target_years)

print("\n[INFO] Done.")