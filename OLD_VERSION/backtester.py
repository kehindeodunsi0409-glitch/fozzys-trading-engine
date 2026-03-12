import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def vectorized_backtest(df, signals):
    """
    Calculates returns for a strategy based on signals.
    """
    data = df.copy()
    data['signal'] = signals.shift(1).fillna(0) # Execute on next bar's open
    data['market_returns'] = np.log(data['Close'] / data['Close'].shift(1))
    data['strategy_returns'] = data['signal'] * data['market_returns']
    
    # Performance metrics
    cum_returns = data['strategy_returns'].cumsum().apply(np.exp)
    data['cum_returns'] = cum_returns
    
    return data

def calculate_metrics(data):
    """
    Calculates key performance indicators.
    """
    returns = data['strategy_returns'].dropna()
    if returns.empty:
        return {}
        
    total_return = np.exp(returns.sum()) - 1
    annualized_return = (1 + total_return) ** (252 / len(returns)) - 1
    annualized_vol = returns.std() * np.sqrt(252)
    sharpe_ratio = annualized_return / annualized_vol if annualized_vol != 0 else 0
    
    # Drawdown
    cum_returns = data['cum_returns']
    peak = cum_returns.expanding(min_periods=1).max()
    drawdown = (cum_returns - peak) / peak
    max_drawdown = drawdown.min()
    
    return {
        "Total Return": f"{total_return:.2%}",
        "Annualized Return": f"{annualized_return:.2%}",
        "Annualized Vol": f"{annualized_vol:.2%}",
        "Sharpe Ratio": f"{sharpe_ratio:.2f}",
        "Max Drawdown": f"{max_drawdown:.2%}"
    }

def plot_results(data, symbol, save_path=None):
    """
    Visualizes the equity curve.
    """
    plt.figure(figsize=(12, 6))
    plt.plot(data['cum_returns'], label='Strategy')
    # Benchmark (Buy and Hold)
    benchmark = data['market_returns'].cumsum().apply(np.exp)
    plt.plot(benchmark, label='Benchmark (B&H)', alpha=0.5)
    
    plt.title(f"HMM Strategy Results: {symbol}")
    plt.legend()
    plt.grid(True)
    
    if save_path:
        plt.savefig(save_path)
        print(f"Saved plot to {save_path}")
    else:
        plt.show()
    plt.close()
