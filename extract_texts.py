import pandas as pd
import os

def main():
    parquet_path = "filings.parquet"
    output_dir = "data"
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    else:
        # Clear existing txt files to avoid mixing old filename formats with new ones
        for f in os.listdir(output_dir):
            if f.endswith(".txt"):
                os.remove(os.path.join(output_dir, f))
        
    df = pd.read_parquet(parquet_path)
    
    # Identify the column containing the full text
    text_col = next((col for col in df.columns if col.lower() in ['text', 'full_text', 'filing_text', 'document_text', 'content', 'raw_text']), None)
    
    if not text_col:
        print("Could not identify a column containing the full text. Available columns:", df.columns)
        # Fallback to combined_text if it exists, otherwise just return
        if "combined_text" in df.columns:
            print("Falling back to 'combined_text' column.")
            text_col = "combined_text"
        else:
            return

    # Let's try to identify ticker and year columns
    ticker_col = next((col for col in df.columns if col.lower() in ['ticker', 'symbol', 'company']), None)
    
    # Check for direct year column or date columns
    year_col = next((col for col in df.columns if col.lower() in ['year', 'fy', 'fiscal_year', 'fiscalyear']), None)
    date_col = next((col for col in df.columns if col.lower() in ['date', 'filingdate', 'periodofreport', 'reportdate', 'report_date']), None)

    for idx, row in df.iterrows():
        text = str(row[text_col])
        
        # Determine ticker
        if ticker_col and pd.notna(row[ticker_col]):
            ticker = str(row[ticker_col])
        else:
            ticker = f"UNKNOWN_TICKER_{idx}"
            
        # Determine year
        year = "UNKNOWN_YEAR"
        if year_col and pd.notna(row[year_col]):
            year = str(row[year_col])
        elif date_col and pd.notna(row[date_col]):
            date_val = str(row[date_col])
            # Assuming format might be YYYY-MM-DD or similar
            if len(date_val) >= 4:
                year = date_val[:4]
                
        # Base filename
        filename = f"{ticker}_{year}.txt"
        filepath = os.path.join(output_dir, filename)
        
        # Handle index just in case there are duplicates for the same ticker and year
        if os.path.exists(filepath):
            filename = f"{ticker}_{year}_{idx}.txt"
            filepath = os.path.join(output_dir, filename)
            
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(text)

    print(f"Successfully extracted {len(df)} texts to '{output_dir}' directory.")

if __name__ == "__main__":
    main()
