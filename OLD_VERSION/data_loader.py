import yfinance as yf
import pandas as pd
import os

def fetch_data(symbol, start_date="2020-01-01", end_date=None):
    """
    Fetches historical data for a given symbol from Yahoo Finance.
    """
    print(f"Fetching data for {symbol}...")
    try:
        data = yf.download(symbol, start=start_date, end=end_date, progress=False)
        if data.empty:
            print(f"No data found for {symbol}")
            return None
        
        # In recent yfinance, columns can be MultiIndex (Field, Symbol)
        # We flatten them if needed and remove index names.
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)
        data.columns.name = None
        data.index.name = "Date"
        return data
    except Exception as e:
        print(f"Error fetching data for {symbol}: {e}")
        return None

def save_data(data, symbol, folder="data"):
    """
    Saves the fetched data to a CSV file.
    """
    if not os.path.exists(folder):
        os.makedirs(folder)
    
    filename = os.path.join(folder, f"{symbol.replace('=', '').replace('-', '')}.csv")
    data.to_csv(filename)
    print(f"Saved {symbol} data to {filename}")

if __name__ == "__main__":
    symbols = [
        "BTC-USD", "GC=F", "GBPUSD=X", "EURUSD=X", 
        "AUDCAD=X", "USDCAD=X", "AUDUSD=X",
        "NZDUSD=X", "USDJPY=X", "USDCHF=X"
    ]
    
    for sym in symbols:
        df = fetch_data(sym)
        if df is not None:
            save_data(df, sym)
