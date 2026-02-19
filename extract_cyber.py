import os
from edgar import Company, set_identity
import time

# 1. Identifikation
set_identity("Krish Varshney krish.varshney@tum.de")

def format_company_name(name):
    """Wandelt Firmennamen in Standard-Schreibweise um."""
    if not name:
        return "Unknown_Company"
    
    formatted = name.title()
    
    # Korrektur gaengiger Suffixe
    replacements = {
        " Inc": " Inc",
        " Corp": " Corp",
        " Llc": " LLC",
        " Ltd": " Ltd",
        " Plc": " PLC"
    }
    
    for old, new in replacements.items():
        if formatted.endswith(old):
            formatted = formatted[:-len(old)] + new
            
    return formatted

def save_to_file(sector, ticker, full_name, section_name, content_obj):
    """Speichert Sektionen in strukturierter Ordnerhierarchie."""
    if content_obj is None:
        return
    
    pretty_name = format_company_name(full_name)
    clean_name = pretty_name.replace(".", "").replace(",", "").replace("/", "-")
    folder_name = f"{ticker} ({clean_name})"
    
    directory = f"extractions/{sector}/{folder_name}"
    if not os.path.exists(directory):
        os.makedirs(directory)
    
    filename = f"{directory}/{ticker}_{section_name}.txt"
    
    try:
        final_text = content_obj.text 
    except:
        final_text = str(content_obj)

    with open(filename, "w", encoding="utf-8") as f:
        f.write(final_text)
    print(f"      [SUCCESS] {section_name} saved.")

def run_extraction(sectors_dict):
    for sector, tickers in sectors_dict.items():
        print(f"\n[SECTOR] {sector.upper()}")
        print("-" * 40)
        for ticker in tickers:
            print(f"   [PROCESSING] {ticker}")
            try:
                company = Company(ticker)
                full_name = company.name
                
                filing = company.get_filings(form="10-K").latest()
                
                if not filing:
                    print(f"      [WARNING] No 10-K filing found for {ticker}.")
                    continue
                    
                doc = filing.obj()
                
                # Sektionen extrahieren
                try:
                    item_1a = doc['Item 1A']
                    item_1c = doc['Item 1C']
                except:
                    item_1a = next((s for s in doc.sections if "1A" in s.id), None)
                    item_1c = next((s for s in doc.sections if "1C" in s.id), None)

                save_to_file(sector, ticker, full_name, "Item_1A_RiskFactors", item_1a)
                save_to_file(sector, ticker, full_name, "Item_1C_Cybersecurity", item_1c)
                
                time.sleep(0.3)
                
            except Exception as e:
                print(f"      [ERROR] {ticker}: {e}")

# Markt-Konfiguration
markets = {
    "Tech_Giants": ["AAPL", "GOOGL", "MSFT", "META", "NVDA"],
    "Semiconductors": ["AMD", "INTC", "AVGO", "ASML", "MU", "TXN"],
    "Finance": ["JPM", "GS", "BAC", "V", "MA", "MS"],
    "Automotive": ["TSLA", "F", "GM", "RIVN", "LCID"],
    "Healthcare": ["LLY", "JNJ", "PFE", "MRK", "ABBV"],
    "Retail_ECom": ["AMZN", "WMT", "COST", "EBAY", "TGT"]
}

print("[INFO] Starting SEC data extraction...")
run_extraction(markets)
print("\n[INFO] Extraction process completed.")