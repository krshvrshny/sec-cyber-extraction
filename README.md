# 10-K Cybersecurity Disclosure Quality Scorer

This project measures the quality of cybersecurity and risk disclosures in 10-K filings by analyzing Item 1A (Risk Factors) and Item 1C (Cybersecurity, 2023+) sections across a sample of 43 publicly listed companies from 2022 to 2025.

---

## Project Structure

```
├── extraction.py   # Pulls sections from EDGAR and saves to parquet
├── boilerplate_detector.py     # Scores boilerplate ratio per filing
├── data_sample.xlsx             # Company list with sector, size, market cap
├── requirements.txt             # Python dependencies
└── extractions/                 # Raw txt backups (created on first run)
    └── sector/
        └── ticker (company)/
            └── year/
                ├── ticker_Item_1A_RiskFactors.txt
                └── ticker_Item_1C_Cybersecurity.txt
```

---

## Setup

**1. Clone the repository and navigate into it**

```bash
git clone <your-repo-url>
cd <your-repo-folder>
```

**2. Create and activate a virtual environment (recommended)**

```bash
python -m venv venv
source venv/bin/activate        # Mac/Linux
venv\Scripts\activate           # Windows
```

**3. Install dependencies**

```bash
pip install -r requirements.txt
```

---

## Usage

**Step 1 — Extract filings from EDGAR and consolidate to parquet**

```bash
python extraction.py
```

This pulls Item 1A and Item 1C sections for each company and year, saves raw txt backups under `extractions/`, and writes a single `filings.parquet` file where each row is one company-year.

**Step 2 — Run boilerplate detection**

```bash
python boilerplate_detector.py
```

This reads `filings.parquet`, counts boilerplate phrase matches against a predefined dictionary, and outputs `boilerplate_results.parquet` with the following added columns:

| Column | Description |
|---|---|
| `boilerplate_count` | Number of boilerplate phrases matched (B) |
| `word_count` | Total word count after preprocessing (N) |
| `boilerplate_ratio` | B / N |
| `matched_phrases` | List of matched phrases for audit trail |

---

## Notes

- Item 1C was introduced by the SEC in 2023, so 2022 filings contain Item 1A only. The `has_1c` column in the parquet flags this.
- The `extractions/` folder serves as a raw backup. If the parquet ever needs to be rebuilt it can be done from these files without re-hitting the EDGAR API.
- The boilerplate dictionary can be extended in `boilerplate_detection.py` under `BOILERPLATE_PHRASES`.
