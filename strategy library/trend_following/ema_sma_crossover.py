"""
EMA/SMA Crossover Strategy
Best TF: H1/H4
Signal: Fast EMA crosses above/below Slow SMA
"""

import pandas as pd
import numpy as np


def calculate_signals(df: pd.DataFrame, fast: int = 20, slow: int = 50) -> pd.DataFrame:
    """
    df must have OHLCV columns: open, high, low, close, volume
    Returns df with signal column: 1=long, -1=short, 0=flat
    """
    df = df.copy()
    df["ema_fast"] = df["close"].ewm(span=fast, adjust=False).mean()
    df["sma_slow"] = df["close"].rolling(slow).mean()

    df["signal"] = 0
    df.loc[df["ema_fast"] > df["sma_slow"], "signal"] = 1
    df.loc[df["ema_fast"] < df["sma_slow"], "signal"] = -1

    # Entry on crossover only (edge trigger)
    df["entry"] = df["signal"].diff().fillna(0)
    df.loc[df["entry"] == 2,  "entry"] = 1   # crossed up
    df.loc[df["entry"] == -2, "entry"] = -1  # crossed down

    return df


def get_signal(df: pd.DataFrame, fast: int = 20, slow: int = 50) -> int:
    """Returns latest signal: 1=long, -1=short, 0=flat"""
    df = calculate_signals(df, fast, slow)
    return int(df["entry"].iloc[-1])
