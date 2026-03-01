import pandas as pd
import numpy as np

def calculate_delta():
    # 1. Load the data
    comp_df = pd.read_csv('composite_scores.csv')
    sim_df = pd.read_csv('similarity_results.csv')

    # 2. Merge on ticker and year
    # We only need the yoy_similarity column from sim_df to avoid duplicating columns
    df = pd.merge(comp_df, sim_df[['ticker', 'year', 'yoy_similarity']], 
                  on=['ticker', 'year'], how='left')

    # ==========================================
    # INPUT REQUIRED: Fill in your table values
    # ==========================================
    DELTA_MAP = {
        ('Low', 'Low'): 0.0,   # Replace with actual multiplier from your image
        ('Low', 'High'): 0.5,  # Replace with actual multiplier from your image
        ('High', 'Low'): 1.0,  # Replace with actual multiplier from your image
        ('High', 'High'): 1.0  # Replace with actual multiplier from your image
    }

    def assign_delta(row):
        # Handle cases with no similarity score (e.g., the first year of a report)
        if pd.isna(row['yoy_similarity']):
            return np.nan
            
        # Specificity threshold (S is out of 100 in your dataset)
        spec_cat = 'High' if row['S'] >= 60 else 'Low'
        
        # Similarity threshold 
        # (Assuming yoy_similarity is a decimal 0-1. If it's 0-100, change 0.75 to 75)
        sim_val = row['yoy_similarity']
        sim_cat = 'High' if sim_val >= 0.75 else 'Low'
        
        return DELTA_MAP.get((spec_cat, sim_cat), np.nan)

    # 3. Apply the logic
    df['delta'] = df.apply(assign_delta, axis=1)

    # 4. Save the main results to CSV
    df.to_csv('delta_results.csv', index=False)
    print("Successfully saved main results to delta_results.csv")

    # 5. Export Descriptive Statistics to CSV
    # Convert the describe output to a DataFrame and transpose for better readability
    desc_stats = df['delta'].describe().to_frame().T
    desc_stats.to_csv('delta_descriptive_stats.csv', index=False)
    print("Successfully saved descriptive stats to delta_descriptive_stats.csv")

    # Export Value Counts to CSV
    # Reset index to make the table clean with column names
    val_counts = df['delta'].value_counts(dropna=False).reset_index()
    val_counts.columns = ['delta_value', 'count']
    val_counts.to_csv('delta_value_counts.csv', index=False)
    print("Successfully saved value counts to delta_value_counts.csv")

if __name__ == "__main__":
    calculate_delta()