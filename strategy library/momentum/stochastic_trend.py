"""
Stochastic with Trend Filter Strategy
Best TF: M15/H1
Signal: Stochastic crosses in oversold/overbought zone, EMA trend filter
"""

import pandas as pd
import numpy as np


def calculate_stochastic(df: pd.DataFrame,
                         k_period: int = 14, d_period: int = 3,
                         oversold: float = 20.0, overbought: float = 80.0,
                         ema_period: int = 50) -> pd.DataFrame:
    df = df.copy()
    df["lowest_low"]   = df["low"].rolling(k_period).min()
    df["highest_high"] = df["high"].rolling(k_period).max()

    denom     = (df["highest_high"] - df["lowest_low"]).replace(0, np.nan)
    df["k"]   = 100 * (df["close"] - df["lowest_low"]) / denom
    df["d"]   = df["k"].rolling(d_period).mean()
    df["ema"] = df["close"].ewm(span=ema_period, adjust=False).mean()

    uptrend   = df["close"] > df["ema"]
    downtrend = df["close"] < df["ema"]

    k_cross_up   = (df["k"] > df["d"]) & (df["k"].shift(1) <= df["d"].shift(1))
    k_cross_down = (df["k"] < df["d"]) & (df["k"].shift(1) >= df["d"].shift(1))

    df["signal"] = 0
    df.loc[uptrend   & k_cross_up   & (df["k"] < oversold  + 10), "signal"] = 1
    df.loc[downtrend & k_cross_down & (df["k"] > overbought - 10), "signal"] = -1

    return df


def get_signal(df: pd.DataFrame) -> int:
    df = calculate_stochastic(df)
    return int(df["signal"].iloc[-1])
