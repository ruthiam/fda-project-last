import pandas as pd
import numpy as np
import os

def clean_market_data(input_file, output_file):
    if not os.path.exists(input_file):
        print(f"Error: {input_file} not found.")
        return

    # Load data
    df = pd.read_csv(input_file)
    
    # Ensure Date is datetime object
    df['Date'] = pd.to_datetime(df['Date'])
    
    # Sort by Asset and Date to ensure correct return calculation
    df = df.sort_values(['Asset', 'Date'])
    
    # Clean Prices: Oil had a negative price in 2020. 
    # For log returns, we must have positive values.
    # We will clip prices to a small positive number for return calculation purposes.
    # But we'll keep the actual price column as is for the price chart, 
    # unless it's strictly for the math stability.
    
    df['Clean_Price'] = df['Price'].clip(lower=1e-8)
    
    # Recalculate Log Returns for consistency
    # Group by Asset and compute log(Pt / Pt-1)
    df['Log_Return'] = df.groupby('Asset')['Clean_Price'].transform(lambda x: np.log(x / x.shift(1)))
    
    # Drop the temporary column and any rows that might have become corrupted (though shouldn't happen here)
    df = df.drop(columns=['Clean_Price'])
    
    # Fill NaN Log_Returns (first row of each asset) with 0 or drop them
    # The HTML dashboard handles nulls, but 0 is safer for some JS libraries.
    # Actually, keeping them as empty is fine as per user requirement.
    
    # Rounding for cleanliness
    df['Price'] = df['Price'].round(4)
    df['Log_Return'] = df['Log_Return'].round(6)
    
    # Save back
    df.to_csv(output_file, index=False)
    print(f"Successfully cleaned data and saved to {output_file}")

if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(current_dir, "data", "market_data.csv")
    clean_market_data(data_path, data_path)
