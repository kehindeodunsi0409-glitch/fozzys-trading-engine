"""
RSI Pullback in Trend Strategy
Best TF: M15/H1
Signal: RSI dips to oversold in uptrend, overbought in downtrend
Trend defined by EMA200
"""

import pandas as pd
import numpy as np


def calculate_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    gain  = delta.clip(lower=0).ewm(com=period - 1, adjust=False).mean()
    loss  = (-delta.clip(upper=0)).ewm(com=period - 1, adjust=False).mean()
    rs    = gain / loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


def calculate_signals(df: pd.DataFrame,
                      rsi_period: int = 14,
                      oversold: float = 40.0,
                      overbought: float = 60.0,
                      ema_period: int = 200) -> pd.DataFrame:
    df = df.copy()
    df["rsi"]    = calculate_rsi(df["close"], rsi_period)
    df["ema200"] = df["close"].ewm(span=ema_period, adjust=False).mean()

    uptrend   = df["close"] > df["ema200"]
    downtrend = df["close"] < df["ema200"]

    # Entry: RSI recovers from oversold in uptrend / overbought in downtrend
    rsi_recover_up   = (df["rsi"] > oversold)  & (df["rsi"].shift(1) <= oversold)
    rsi_recover_down = (df["rsi"] < overbought) & (df["rsi"].shift(1) >= overbought)

    df["signal"] = 0
    df.loc[uptrend   & rsi_recover_up,   "signal"] = 1
    df.loc[downtrend & rsi_recover_down, "signal"] = -1

    return df


def get_signal(df: pd.DataFrame) -> int:
    df = calculate_signals(df)
    return int(df["signal"].iloc[-1])
