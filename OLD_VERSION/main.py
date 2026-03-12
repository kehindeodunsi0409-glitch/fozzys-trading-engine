from data_loader import fetch_data
from regime_classifier import MarketRegimeHMM
from strategies import apply_regime_strategies
from backtester import vectorized_backtest, calculate_metrics
import pandas as pd
import os

def run_pipeline(symbol):
    print(f"\n{'='*40}")
    print(f"ANALYZING: {symbol}")
    print(f"{'='*40}")
    
    # 1. Fetch Data
    df = fetch_data(symbol)
    if df is None or len(df) < 100:
        print(f"Insufficient data for {symbol}")
        return None
        
    # 2. Machine Learning (HMM)
    hmm_model = MarketRegimeHMM(n_regimes=3)
    features, idx = hmm_model.prepare_features(df)
    hmm_model.fit(features)
    states = hmm_model.predict(features)
    mapped_states = hmm_model.sort_regimes(features, states)
    
    # 3. Apply Strategies
    signals = apply_regime_strategies(df, mapped_states)
    
    # 4. Backtest
    results = vectorized_backtest(df, signals)
    metrics = calculate_metrics(results)
    
    # 5. Visualize
    if not os.path.exists("plots"):
        os.makedirs("plots")
    from backtester import plot_results
    plot_results(results, symbol, save_path=f"plots/{symbol.replace('=', '').replace('-', '')}.png")
    
    # Print Metrics
    for k, v in metrics.items():
        print(f"{k}: {v}")
        
    return metrics

if __name__ == "__main__":
    symbols = [
        "BTC-USD", "GC=F", "GBPUSD=X", "EURUSD=X", 
        "AUDCAD=X", "USDCAD=X", "AUDUSD=X",
        "NZDUSD=X", "USDJPY=X", "USDCHF=X"
    ]
    
    all_results = {}
    for sym in symbols:
        try:
            m = run_pipeline(sym)
            if m:
                all_results[sym] = m
        except Exception as e:
            print(f"Failed to process {sym}: {e}")
            
    # Final Report
    report_df = pd.DataFrame(all_results).T
    print("\n--- FINAL SUMMARY REPORT ---")
    print(report_df)
    report_df.to_csv("strategy_summary.csv")
