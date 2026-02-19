import os
from edgar import Company, set_identity
import time

# 1. Identifikation
set_identity("Krish Varshney krish.varshney@tum.de")

def format_company_name(name):
    if not name:
        return "Unknown_Company"
    formatted = name.title()
    replacements = {" Inc": " Inc", 
                    " Corp": " Corp", " Llc": " LLC", " Ltd": " Ltd", " Plc": " PLC"}
    for old, new in replacements.items():
        if formatted.endswith(old):
            formatted = formatted[:-len(old)] + new
    return formatted

def save_to_file(base_folder, sector, ticker, full_name, section_name, content_obj):
    if content_obj is None:
        return
    
    pretty_name = format_company_name(full_name)
    clean_name = pretty_name.replace(".", "").replace(",", "").replace("/", "-")
    folder_name = f"{ticker} ({clean_name})"
    
    # Pfad erstellen
    directory = f"{base_folder}/{sector}/{folder_name}"
    if not os.path.exists(directory):
        os.makedirs(directory)
    
    filename = f"{directory}/{ticker}_{section_name}.txt"
    
    try:
        final_text = content_obj.text 
    except:
        final_text = str(content_obj)

    with open(filename, "w", encoding="utf-8") as f:
        f.write(final_text)

def run_extraction_by_year(sectors_dict, year_index):
    """
    year_index 0 = neuestes Filing
    year_index 1 = t-1
    year_index 2 = t-2
    """
    for sector, tickers in sectors_dict.items():
        print(f"\n[SECTOR] {sector.upper()}")
        for ticker in tickers:
            try:
                company = Company(ticker)
                full_name = company.name
                
                # Holen aller 10-Ks
                filings = company.get_filings(form="10-K")
                
                if len(filings) <= year_index:
                    print(f"   [SKIP] {ticker}: No filing at index {year_index}")
                    continue
                
                filing = filings[year_index]
                
                # Jahr direkt aus dem date-objekt ziehen
                f_year = filing.filing_date.year 
                
                base_folder = f"extractions{f_year}"
                print(f"   [PROCESSING] {ticker} for Year {f_year}")
                
                # DEINE LOGIK
                doc = filing.obj()
                
                try:
                    item_1a = doc['Item 1A']
                    item_1c = doc['Item 1C']
                except:
                    item_1a = next((s for s in doc.sections if "1A" in s.id), None)
                    item_1c = next((s for s in doc.sections if "1C" in s.id), None)

                save_to_file(base_folder, sector, ticker, full_name, "Item_1A_RiskFactors", item_1a)
                save_to_file(base_folder, sector, ticker, full_name, "Item_1C_Cybersecurity", item_1c)
                
                time.sleep(0.4)
                
            except Exception as e:
                print(f"      [ERROR] {ticker}: {e}")

markets = {
    "Tech_Giants": ["AAPL", "GOOGL", "MSFT", "META", "NVDA"],
    "Semiconductors": ["AMD", "INTC", "AVGO", "ASML", "MU", "TXN"],
    "Cybersecurity_Mid": ["PANW", "FTNT", "CRWD", "OKTA", "ZS", "NET"],
    "Finance": ["JPM", "GS", "BAC", "V", "MA", "MS"],
    "Automotive": ["TSLA", "F", "GM", "RIVN", "LCID"],
    "Healthcare": ["LLY", "JNJ", "PFE", "MRK", "ABBV"],
    "Retail_ECom": ["AMZN", "WMT", "COST", "EBAY", "TGT"],
    "Small_Caps_Consumer": ["CROX", "OLPX", "YETI", "DECK", "ELF"],
    "Small_Caps_Tech": ["HLIT", "BJDX", "DJCO", "HSON", "MOD", "SCSC"]
}

for i in range(3):
    print(f"\n=== STARTING ROUND {i+1} (Offset {i}) ===")
    run_extraction_by_year(markets, i)

print("\n[INFO] Done. Separate folders for each year created.")