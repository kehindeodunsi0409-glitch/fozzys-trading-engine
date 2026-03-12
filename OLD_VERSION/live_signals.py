from data_loader import fetch_data
from regime_classifier import MarketRegimeHMM
from strategies import mean_reversion_strategy, trend_following_strategy, volatile_breakout_strategy
import pandas as pd
import datetime

def get_current_signal(symbol):
    """
    Fetches recent data and determines the signal for the current moment.
    """
    print(f"\n--- LIVE SIGNAL FOR {symbol} ---")
    
    # 1. Fetch recent data (last year for training context)
    df = fetch_data(symbol)
    if df is None or len(df) < 100:
        print("Error: Not enough data.")
        return
        
    # 2. Identify Regime
    hmm_model = MarketRegimeHMM(n_regimes=3)
    features, idx = hmm_model.prepare_features(df)
    hmm_model.fit(features)
    states = hmm_model.predict(features)
    mapped_states = hmm_model.sort_regimes(features, states)
    
    current_regime_id = mapped_states[-1]
    regime_names = {0: "Ranging (Calm)", 1: "Trending (Moving)", 2: "Volatile (Crazy)"}
    current_regime = regime_names[current_regime_id]
    
    # 3. Get Signal from relevant strategy
    if current_regime_id == 0:
        sigs = mean_reversion_strategy(df)
    elif current_regime_id == 1:
        sigs = trend_following_strategy(df)
    else:
        sigs = volatile_breakout_strategy(df)
        
    current_sig = sigs.iloc[-1]
    action = "WAIT"
    if current_sig == 1: action = "BUY"
    if current_sig == -1: action = "SELL"
    
    print(f"Current Time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"Market Regime: {current_regime}")
    print(f"Action: {action}")
    print("-" * 30)

if __name__ == "__main__":
    # Choose a pair to check
    pair = "BTC-USD" 
    get_current_signal(pair)
    
    # Check a few more
    fx_pairs = ["EURUSD=X", "AUDUSD=X"]
    for p in fx_pairs:
        get_current_signal(p)
