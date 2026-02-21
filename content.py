import os
import json
import pandas as pd
import time
from pathlib import Path
from google import genai
from google.genai import types

# ==========================================
# 1. SETUP (100% FREE TIER OPTIMIZED)
# ==========================================
API_KEY = "AIzaSyAuN7FNqrjK6LX0GDqT99dnkYTVVQulf9M" # BITTE NEUEN KEY NUTZEN!
client = genai.Client(api_key=API_KEY)

BASE_PATH = Path("extractions")
OUTPUT_FILE = "Pillar1_AI_Results_Final.csv"
TARGET_ITEMS = ["Item_1A_RiskFactors", "Item_1C_Cybersecurity"]

def get_ai_score_v3(text):
    """Semantische Analyse mit Schutz vor Rate-Limits."""
    if not text or len(text) < 100:
        return 0.0, {f"x{i}": 0 for i in range(1, 7)}

    prompt = """Analysiere diesen SEC-Text. Antworte NUR mit JSON {{"x1":..,"x6":..}}. 
    Bewerte 1 (nachgewiesen/explizit) oder 0 (vage/fehlt/Zukunftsmusik).
    x1:Standards(NIST/ISO), x2:Tech(MFA/ZeroTrust), x3:Governance(CISO/Board), 
    x4:Metrics(Zahlen/Budget), x5:Ecosystem(AWS/Azure/Vendors), x6:Threats(Spezifisch)."""

    # Wir kürzen auf 10k Zeichen um Token-Limits im Free Tier zu schonen
    clean_text = text[:10000].replace("\n", " ")

    for attempt in range(4): # 4 Versuche bei Fehlern
        try:
            response = client.models.generate_content(
                model="gemini-2.0-flash-lite", # Beste Performance für Free Tier
                contents=[prompt, clean_text],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.0 # Macht die KI konsistenter/strenger
                )
            )
            
            data = json.loads(response.text)
            sc_score = sum([data.get(f"x{i}", 0) for i in range(1, 7)]) / 6
            return round(sc_score, 4), data
            
        except Exception as e:
            if "429" in str(e):
                wait_time = 60 # Bei Limit volle Minute warten
                print(f"!!! Rate Limit !!! Warte {wait_time}s...")
                time.sleep(wait_time)
            else:
                print(f"Fehler: {e}")
                time.sleep(5)
                
    return 0.0, {f"x{i}": 0 for i in range(1, 7)}

# ==========================================
# 2. VERARBEITUNG MIT SPEICHER-SCHUTZ
# ==========================================
results = []
files_to_process = [f for f in BASE_PATH.rglob("*.txt") if any(item in f.name for item in TARGET_ITEMS)]

print(f"Starte Analyse ({len(files_to_process)} Docs). Kostenlos-Modus aktiv.")

for i, file in enumerate(files_to_process):
    try:
        parts = file.parts
        base_idx = parts.index("extractions")
        ticker = parts[base_idx + 2]
        year = parts[base_idx + 3]
        item_type = "1A" if "Item_1A" in file.name else "1C"

        print(f"[{i+1}/{len(files_to_process)}] {ticker} {year} ({item_type})...", end=" ", flush=True)

        content = file.read_text(encoding="utf-8").strip()
        score, x_details = get_ai_score_v3(content)
        
        results.append({
            'Ticker': ticker, 'Year': year, 'Item': item_type,
            'SC_Score': score, **x_details
        })
        print(f"Score: {score}")

        # Zwischenspeichern alle 10 Dokumente (Backup)
        if (i + 1) % 10 == 0:
            pd.DataFrame(results).to_csv(OUTPUT_FILE, index=False)
            print("--- Backup gespeichert ---")

    except Exception as e:
        print(f"Überspringe {file.name} wegen Fehler: {e}")
    
    # Wichtig: 5 Sek Pause für stabile 12 Anfragen/Minute (Sicherheitsmarge)
    time.sleep(5)

# Finales Speichern
df = pd.DataFrame(results)
df.to_csv(OUTPUT_FILE, index=False)
print(f"\nERFOLG! Alle Daten in {OUTPUT_FILE}")