import os
from edgar import Company, set_identity
import time

# 1. Identifikation
set_identity("Krish Varshney krish.varshney@tum.de")

def save_to_file(ticker, section_name, content_obj):
    """Speichert den Text gut lesbar mit Zeilenumbrüchen."""
    if content_obj is None:
        return
    
    directory = f"extractions/{ticker}"
    if not os.path.exists(directory):
        os.makedirs(directory)
    
    filename = f"{directory}/{ticker}_{section_name}.txt"
    
    # Wir nutzen die .text Eigenschaft des edgar-Objekts, 
    # falls vorhanden, da diese die Formatierung beibehält.
    try:
        # Versuch, den Text formatiert zu extrahieren
        final_text = content_obj.text 
    except:
        # Fallback: Einfach in String umwandeln (behält meist \n bei)
        final_text = str(content_obj)

    with open(filename, "w", encoding="utf-8") as f:
        f.write(final_text)
    print(f"   ✅ {section_name} gespeichert.")

def run_extraction(tickers):
    for ticker in tickers:
        print(f"📡 Verarbeite {ticker}...")
        try:
            company = Company(ticker)
            filing = company.get_filings(form="10-K").latest()
            
            if not filing:
                continue
                
            doc = filing.obj()
            
            # Sektionen ziehen
            try:
                item_1a = doc['Item 1A']
                item_1c = doc['Item 1C']
            except:
                item_1a = next((s for s in doc.sections if "1A" in s.id), None) # type: ignore
                item_1c = next((s for s in doc.sections if "1C" in s.id), None) # type: ignore

            save_to_file(ticker, "Item_1A_RiskFactors", item_1a)
            save_to_file(ticker, "Item_1C_Cybersecurity", item_1c)
            
            time.sleep(0.2)
            
        except Exception as e:
            print(f"   ❌ Fehler bei {ticker}: {e}")

# Deine Liste
my_list = ["AAPL", "GOOGL", "MSFT", "TSLA", "AMZN", "NVDA", "META"]

print("🚀 Starte Extraktion mit Zeilenumbrüchen...")
run_extraction(my_list)
print("\n🔥 Fertig! Die Dateien sind jetzt unter 'extractions/' lesbar.")