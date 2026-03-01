import pandas as pd

def calculate_quality_score():
    # Load the delta results
    df = pd.read_csv('delta_results.csv')

    # Calculate Quality Score
    # Using 'specificity_score' (0-1 scale) so the final * 100 results in a 0-100 score.
    df['quality_score'] = (0.8 * df['specificity_score'] + 0.2 * df['delta']) * 100

    # Save to a new CSV
    df.to_csv('quality_results.csv', index=False)
    print("Quality scores successfully calculated and saved to quality_results.csv")

if __name__ == "__main__":
    calculate_quality_score()