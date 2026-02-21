import os
import json
import pandas as pd
import time
from pathlib import Path
from google import genai
from google.genai import types
from dotenv import load_dotenv

# ==========================================
# 1. SETUP (Gemini Flash Stable)
# ==========================================
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("❌ FEHLER: Kein API_KEY in der .env gefunden!")
    exit()

client = genai.Client(api_key=api_key)

BASE_PATH = Path("extractions")
OUTPUT_FILE = "Pillar1_AI_Results.csv"
TARGET_ITEMS = ["Item_1A_RiskFactors", "Item_1C_Cybersecurity"]

def get_ai_score_v2(text):
    """Analysiert den Text mit dem stabilen Flash-Modell."""
    if not text or len(text) < 100:
        return 0.0, {f"x{i}": 0 for i in range(1, 7)}

    prompt = """Analysiere diesen SEC-Text als Cyber-Auditor. Antworte NUR im JSON-Format:
    {"x1":0/1, "x2":0/1, "x3":0/1, "x4":0/1, "x5":0/1, "x6":0/1}
    Kriterien: x1:Standards(NIST/ISO), x2:Tech-Controls, x3:Governance, x4:Metrics, x5:Partner, x6:Spezifische Threats."""

    for attempt in range(3):
        try:
            # Wir nutzen das Modell, das im Test funktioniert hat!
            response = client.models.generate_content(
                model="gemini-flash-latest",
                contents=[prompt, text[:1000]], 
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.1
                )
            )
            
            data = json.loads(response.text)
            sc_score = sum([data.get(f"x{i}", 0) for i in range(1, 7)]) / 6
            return round(sc_score, 4), data
            
        except Exception as e:
            if "429" in str(e):
                print(f" (Limit! Pause 60s...) ", end="", flush=True)
                time.sleep(60)
            else:
                print(f" (Fehler: {e}) ", end="", flush=True)
                time.sleep(5)
                
    return 0.0, {f"x{i}": 0 for i in range(1, 7)}

# ==========================================
# 2. VERARBEITUNG
# ==========================================
results = []
files_to_process = sorted([f for f in BASE_PATH.rglob("*.txt") if any(item in f.name for item in TARGET_ITEMS)])

print(f"🚀 Starte Analyse für {len(files_to_process)} Dokumente...")

for i, file in enumerate(files_to_process):
    try:
        # Pfad-Logik
        parts = file.parts
        base_idx = parts.index("extractions")
        ticker = parts[base_idx + 2]
        year = parts[base_idx + 3]
        item_type = "1A" if "Item_1A" in file.name else "1C"

        print(f"[{i+1}/{len(files_to_process)}] {ticker} ({year}) {item_type}...", end="", flush=True)

        content = file.read_text(encoding="utf-8").strip()
        score, x_details = get_ai_score_v2(content)
        
        results.append({
            'Ticker': ticker, 'Year': year, 'Item': item_type,
            'SC_Score': score, **x_details
        })
        print(f" ✅ Score: {score}")

        # Backup alle 10 Files (falls der Laptop ausgeht)
        if (i + 1) % 10 == 0:
            pd.DataFrame(results).to_csv(OUTPUT_FILE, index=False)

    except Exception as e:
        print(f" ❌ Fehler bei {file.name}: {e}")
    
    # WICHTIG: Im Free Tier brauchen wir eine kleine Pause
    time.sleep(6) 

# Finales Speichern
df = pd.DataFrame(results)
df.to_csv(OUTPUT_FILE, index=False)
print(f"\n🎉 FERTIG! Ergebnisse in {OUTPUT_FILE}")