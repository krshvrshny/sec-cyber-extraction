import os
from edgar import Company, set_identity
import time

# 1. Identifikation
set_identity("Krish Varshney krish.varshney@tum.de")

def save_to_file(sector, ticker, full_name, section_name, content_obj):
    """Speichert den Text in Ordnern mit dem Format: TICKER (Vollständiger Name)."""
    if content_obj is None:
        return
    
    # Ordnername säubern (Sonderzeichen wie '.' oder ',' entfernen, falls nötig)
    clean_name = full_name.replace(".", "").replace(",", "")
    folder_name = f"{ticker} ({clean_name})"
    
    # Pfad-Struktur: extractions/Sektor/TICKER (Name)/...
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
    print(f"      ✅ {section_name} gespeichert.")

def run_extraction(sectors_dict):
    for sector, tickers in sectors_dict.items():
        print(f"\n📂 Sektor: {sector.upper()} " + "="*30)
        for ticker in tickers:
            print(f"   📡 Verarbeite {ticker}...")
            try:
                # Firma initialisieren
                company = Company(ticker)
                # Den offiziellen Namen der Firma ziehen
                full_name = company.name
                
                filing = company.get_filings(form="10-K").latest()
                
                if not filing:
                    print(f"      ⚠️ Kein 10-K für {ticker} gefunden.")
                    continue
                    
                doc = filing.obj()
                
                # Sektionen ziehen
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
                print(f"      ❌ Fehler bei {ticker}: {e}")

# Deine Markt-Einteilung
markets = {
    "Tech_Giants": ["AAPL", "GOOGL", "MSFT", "META", "NVDA"],
    "Semiconductors": ["AMD", "INTC", "AVGO", "ASML", "MU"],
    "Finance": ["JPM", "GS", "BAC", "V", "MA"],
    "Automotive": ["TSLA", "F", "GM", "RIVN"],
    "Healthcare": ["LLY", "JNJ", "PFE", "MRK"],
    "Retail_ECom": ["AMZN", "WMT", "COST", "EBAY"]
}

print("🚀 Starte Extraktion mit Klarnamen-Ordnern...")
run_extraction(markets)
print("\n🔥 Fertig! Schau mal in den 'extractions/' Ordner.")