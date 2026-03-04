import yfinance as yf
import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta

def compute_returns(price_df):
    """Computes daily log returns."""
    price_df = price_df.clip(lower=1e-8)
    log_returns = np.log(price_df / price_df.shift(1)).dropna()
    return log_returns

def main():
    tickers = {
        "SP500": "SPY",
        "WTI": "CL=F",
        "GOLD": "GC=F"
    }
    
    start_date = "2016-01-01"
    end_date = datetime.now().strftime("%Y-%m-%d")
    print(f"Downloading data from {start_date} to {end_date}...")
    
    ticker_list = list(tickers.values())
    df = yf.download(ticker_list, start=start_date, end=end_date, auto_adjust=False)
    
    if df.empty:
        print("Failed to download data.")
        return
        
    if isinstance(df.columns, pd.MultiIndex):
        if 'Adj Close' in df.columns.levels[0]:
            price_df = df['Adj Close']
        else:
            price_df = df['Close']
    else:
        if 'Adj Close' in df.columns:
            price_df = df[['Adj Close']]
        elif 'Close' in df.columns:
            price_df = df[['Close']]
        else:
            print("Could not find price columns.")
            return

    # Map tickers back to SP500, WTI, GOLD
    reverse_tickers = {v: k for k, v in tickers.items()}
    price_df = price_df.rename(columns=reverse_tickers)
    
    if isinstance(price_df, pd.Series):
        price_df = price_df.to_frame()
        
    price_df = price_df.ffill().dropna()
    
    # compute log returns
    log_returns = compute_returns(price_df)
    
    # reset index and melt
    price_long = price_df.reset_index().melt(id_vars='Date', var_name='Asset', value_name='Price')
    returns_long = log_returns.reset_index().melt(id_vars='Date', var_name='Asset', value_name='Log_Return')
    
    tidy_df = pd.merge(price_long, returns_long, on=['Date', 'Asset'], how='left')
    
    # Rounding for cleanliness (from clean_data.py)
    tidy_df['Price'] = tidy_df['Price'].round(4)
    tidy_df['Log_Return'] = tidy_df['Log_Return'].round(6)
    
    # Sort
    tidy_df = tidy_df.sort_values(['Asset', 'Date'])
    
    output_file = os.path.join("data", "market_data_cleaned.csv")
    os.makedirs("data", exist_ok=True)
    
    tidy_df.to_csv(output_file, index=False)
    print(f"Successfully updated data to {output_file}")

if __name__ == "__main__":
    main()
