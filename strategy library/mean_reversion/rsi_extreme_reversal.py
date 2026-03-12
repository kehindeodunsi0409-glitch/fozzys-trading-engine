"""
RSI Extreme Reversal Strategy
Best TF: M15/H1
Signal: RSI exits oversold/overbought extreme zone
"""

import pandas as pd
import numpy as np


def calculate_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    gain  = delta.clip(lower=0).ewm(com=period - 1, adjust=False).mean()
    loss  = (-delta.clip(upper=0)).ewm(com=period - 1, adjust=False).mean()
    rs    = gain / loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


def calculate_signals(df: pd.DataFrame, rsi_period: int = 14,
                      oversold: float = 30.0, overbought: float = 70.0) -> pd.DataFrame:
    df = df.copy()
    df["rsi"] = calculate_rsi(df["close"], rsi_period)

    # Entry when RSI exits extreme zone
    exit_oversold   = (df["rsi"] > oversold)   & (df["rsi"].shift(1) <= oversold)
    exit_overbought = (df["rsi"] < overbought)  & (df["rsi"].shift(1) >= overbought)

    df["signal"] = 0
    df.loc[exit_oversold,   "signal"] = 1
    df.loc[exit_overbought, "signal"] = -1

    return df


def get_signal(df: pd.DataFrame) -> int:
    df = calculate_signals(df)
    return int(df["signal"].iloc[-1])
