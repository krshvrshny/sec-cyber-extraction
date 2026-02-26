import os
import time
import json
import pandas as pd
from dotenv import load_dotenv
from google import genai

# ── Load Environment Variables ────────────────────────────────────────────────
load_dotenv()
API_KEY = os.environ.get("GEMINI_API_KEY")

# ── Config ────────────────────────────────────────────────────────────────────
DATA_DIR            = "data"       # folder containing ticker_year.txt files
OUTPUT_PATH         = "content_scores"
MODEL_NAME          = "gemini-2.5-flash"
SLEEP_BETWEEN_CALLS = 60 / 15     # 4 seconds — 15 RPM free tier

client = genai.Client(api_key=API_KEY)

SPECIFICITY_CATEGORIES = [
    "frameworks",
    "specific_controls",
    "named_individuals",
    "quantitative_data",
    "product_names",
    "technical_details",
]
ALL_CATEGORIES = SPECIFICITY_CATEGORIES + ["llm_boilerplate"]
TOTAL_MARKERS  = len(SPECIFICITY_CATEGORIES)  # 6, llm_boilerplate excluded


# ── Prompt ────────────────────────────────────────────────────────────────────
PROMPT = """You are a senior Cybersecurity Disclosure Analyst specialized in financial regulatory filings (SEC 10-K and ESRS Integrated Reports). Objective: Analyze the provided corporate report to calculate a Content Score based on six categories of technical disclosure. Scoring Instructions: • For each category, assign a binary score (1 if present, 0 if absent). • The keywords provided in the descriptions below are illustrative examples only. You must use your expert judgment to evaluate the text and determine if other technical terms, processes, or disclosures fit into these categories. • The final Content Score is calculated as: (Sum of assigned points / 6). Category Definitions:
 
Frameworks: Mention of specific industry-standard cybersecurity frameworks used by the firm (e.g., NIST CSF, ISO/IEC 27001, TISAX, SOC 2, PCI DSS).
Specific Controls: Identification of specific technical security tools, defensive layers, or rigorous processes (e.g., Multi-Factor Authentication (MFA), EDR, SIEM, Zero Trust Architecture, regular penetration testing, or encryption protocols).
Named Individuals / Committees: Identification of specific roles with named expertise, specific individuals, or specialized oversight bodies (e.g., naming the CISO, a Board member with cyber credentials, or a dedicated "Cybersecurity Governance Council").
Quantitative Data: Disclosure of specific cyber-related numbers or metrics (e.g., daily threat signal counts, number of threat actors tracked, dollar amounts for cyber litigation/insurance, or training completion percentages).
Product Names: Mention of specific internal or third-party security product brands or proprietary technology platforms (e.g., Microsoft Copilot for Security, Palo Alto Prisma, Cortex XSIAM, or specialized tools like the "Modular Control Centre System").
Technical Details: Granular descriptions of specific cyber vulnerabilities, incident remediation, or architectural setups (e.g., detailing a "command injection" vulnerability, a "nation-state password spray attack," or describing specific "IT/OT segmentation" protocols). Validation Logic (CRITICAL): A category only receives a "1" if the disclosure is Firm-Specific and Active. You must evaluate the context of every mention. Do NOT award points if the disclosure is: • Negated: (e.g., "The company does not currently utilize MFA"). • Conditional or Hypothetical: (e.g., "If we were to adopt the NIST framework..." or "Future events could include ransomware"). • Generic or Vague: (e.g., "We follow industry-standard practices" without naming them).

Additionally, assess overall boilerplate level as a seventh judgment:
LLM_BOILERPLATE: count the number of phrases in the disclosure that are generic and boilerplate — language that could apply to any company regardless of its actual security posture. State the count of such phrases for the sections 1A and if 1C exists, then for that as well. Score 0 if the disclosure contains sufficient specific, operational content that distinguishes it from a template. 
Respond ONLY with a valid JSON object in exactly this format, with no additional text before or after:
{
  "frameworks":        {"score": 0, "rationale": "exact quote or specific evidence from text"},
  "specific_controls": {"score": 0, "rationale": "exact quote or specific evidence from text"},
  "named_individuals": {"score": 0, "rationale": "exact quote or specific evidence from text"},
  "quantitative_data": {"score": 0, "rationale": "exact quote or specific evidence from text"},
  "product_names":     {"score": 0, "rationale": "exact quote or specific evidence from text"},
  "technical_details": {"score": 0, "rationale": "exact quote or specific evidence from text"},
  "llm_boilerplate":   {"score": 0, "rationale": "boilerplate phrases in section 1A and 1C"}
}

FILING TEXT:
"""


# ── Score a single filing ─────────────────────────────────────────────────────
def score_filing(text):
    if not text or len(text.strip()) < 100:
        return None

    full_prompt = PROMPT + text[:60000]

    try:
        response = client.models.generate_content(model=MODEL_NAME, contents=full_prompt)
        raw      = response.text.strip()

        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        raw = raw.strip()

        return json.loads(raw)

    except json.JSONDecodeError as e:
        print(f"  [WARN] JSON parse error: {e}")
        return None
    except Exception as e:
        print(f"  [WARN] API error: {e}")
        return None


# ── Save helper ───────────────────────────────────────────────────────────────
def _save(existing, new_results, output_path):
    new_df   = pd.DataFrame(new_results)
    combined = pd.concat([existing, new_df], ignore_index=True) if not existing.empty else new_df
    combined["specificity_score"] = combined[SPECIFICITY_CATEGORIES].sum(axis=1) / TOTAL_MARKERS
    combined.to_parquet(f"{output_path}.parquet", index=False)


# ── Load filings from data/ directory ────────────────────────────────────────
def load_filings_from_dir(data_dir):
    """
    Reads all ticker_year.txt files from data_dir.
    Returns a list of dicts with ticker, year, and text.
    """
    filings = []
    for filename in sorted(os.listdir(data_dir)):
        if not filename.endswith(".txt"):
            continue
        name = filename[:-4]  # strip .txt
        parts = name.rsplit("_", 1)
        if len(parts) != 2:
            print(f"[WARN] Skipping unrecognised filename: {filename}")
            continue
        ticker, year_str = parts
        try:
            year = int(year_str)
        except ValueError:
            print(f"[WARN] Skipping unrecognised filename: {filename}")
            continue

        filepath = os.path.join(data_dir, filename)
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read()

        filings.append({"ticker": ticker, "year": year, "text": text})

    print(f"[INFO] Found {len(filings)} txt files in {data_dir}/")
    return filings


# ── Main ──────────────────────────────────────────────────────────────────────
def run_content_scoring(data_dir=DATA_DIR, output_path=OUTPUT_PATH):
    filings = load_filings_from_dir(data_dir)

    if not filings:
        print(f"[ERROR] No txt files found in {data_dir}/")
        return

    if os.path.exists(f"{output_path}.parquet"):
        existing = pd.read_parquet(f"{output_path}.parquet")
        done     = set(zip(existing["ticker"], existing["year"]))
        print(f"[INFO] Resuming — {len(done)} already scored, {len(filings) - len(done)} remaining")
    else:
        existing = pd.DataFrame()
        done     = set()

    results = []
    total   = len(filings)

    for idx, filing in enumerate(filings):
        ticker = filing["ticker"]
        year   = filing["year"]
        text   = filing["text"]

        if (ticker, year) in done:
            continue

        print(f"[{idx+1}/{total}] Scoring {ticker} {year}...")
        scores = score_filing(text)

        result = {"ticker": ticker, "year": year}

        if scores is None:
            print(f"  [SKIP] Failed — {ticker} {year}")
            for cat in ALL_CATEGORIES:
                result[cat]                = None
                result[f"{cat}_rationale"] = None
        else:
            for cat in ALL_CATEGORIES:
                result[cat]                = scores.get(cat, {}).get("score",     None)
                result[f"{cat}_rationale"] = scores.get(cat, {}).get("rationale", None)

        results.append(result)

        if len(results) % 10 == 0:
            _save(existing, results, output_path)
            print(f"  [INFO] Progress saved ({len(results)} new filings scored)")

        time.sleep(SLEEP_BETWEEN_CALLS)

    _save(existing, results, output_path)

    out = pd.read_parquet(f"{output_path}.parquet")
    print(f"\n[INFO] Done. {len(out)} filings scored.")
    print("\n[SUMMARY] Mean scores:")
    print(out[ALL_CATEGORIES + ["specificity_score"]].mean().round(3).to_string())
    return out


if __name__ == "__main__":
    run_content_scoring()