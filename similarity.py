import os
import pandas as pd
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import re

# ==========================================
# 1. OPTIMIERTE KONFIGURATION
# ==========================================
BASE_FOLDER = Path("extractions")
TARGET_ITEMS = ["Item_1A_RiskFactors", "Item_1C_Cybersecurity"]
OUTPUT_FILE = "Pillar3_Enhanced_Analysis.csv"

def get_top_new_words(text_old, text_new, top_n=5):
    """Findet Wörter, die im neuen Text signifikant häufiger vorkommen."""
    try:
        vec = TfidfVectorizer(stop_words='english', ngram_range=(1,2))
        tfidf = vec.fit_transform([text_old, text_new])
        feature_names = vec.get_feature_names_out()
        
        # Differenz der TF-IDF Werte zwischen Jahr 2 und Jahr 1
        diff = tfidf.toarray()[1] - tfidf.toarray()[0]
        top_indices = diff.argsort()[-top_n:][::-1]
        
        return ", ".join([feature_names[i] for i in top_indices if diff[i] > 0])
    except:
        return "N/A"

results = []
vectorizer = TfidfVectorizer(stop_words='english')

# Check ob Ordner existiert
if not BASE_FOLDER.exists():
    print(f"Fehler: {BASE_FOLDER} nicht gefunden!")
else:
    # Wir nutzen Pathlib für saubereres Iterieren
    for sector_path in BASE_FOLDER.iterdir():
        if not sector_path.is_dir(): continue

        for company_path in sector_path.iterdir():
            if not company_path.is_dir(): continue
            
            # Daten sammeln
            store = {}
            for year_path in company_path.iterdir():
                if not year_path.is_dir(): continue
                year = int(year_path.name)
                
                for f in year_path.glob("*.txt"):
                    for item_key in TARGET_ITEMS:
                        if item_key in f.name:
                            text = f.read_text(encoding="utf-8").strip()
                            if text:
                                store[(year, item_key)] = text

            # Vergleichs-Logik
            years_sorted = sorted(list(set([y for y, it in store.keys()])))
            
            for item_key in TARGET_ITEMS:
                for i in range(1, len(years_sorted)):
                    y1, y2 = years_sorted[i-1], years_sorted[i]
                    
                    if (y1, item_key) in store and (y2, item_key) in store:
                        t1, t2 = store[(y1, item_key)], store[(y2, item_key)]
                        
                        # Metriken berechnen
                        tfidf_matrix = vectorizer.fit_transform([t1, t2])
                        sim = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
                        
                        # NEU: Was sind die neuen Themen?
                        new_topics = get_top_new_words(t1, t2)
                        
                        label = "1A" if "1A" in item_key else "1C"
                        
                        # Kategorisierung (Deine bewährte Logik)
                        if sim > 0.98: cat = "1. Boilerplate"
                        elif sim > 0.90: cat = "2. Adaptive"
                        else: cat = "3. Dynamic"
                        
                        results.append({
                            'Sector': sector_path.name,
                            'Ticker': company_path.name.split(' ')[0],
                            'Item': label,
                            'Window': f"{y1}-{y2}",
                            'Sim_Score': round(sim, 4),
                            'Top_New_Terms': new_topics,
                            'Category': cat
                        })

# Finaler DataFrame
df = pd.DataFrame(results)
if not df.empty:
    df.to_csv(OUTPUT_FILE, index=False)
    print(f"Analyse abgeschlossen! Datei: {OUTPUT_FILE}")