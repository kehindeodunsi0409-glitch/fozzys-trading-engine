"""
Pairs Trading / Cointegration Strategy
Best TF: H1/H4
Signal: Spread between two cointegrated instruments deviates from mean
Requires two price series (e.g. EURUSD + GBPUSD)
"""

import pandas as pd
import numpy as np


def calculate_spread(s1: pd.Series, s2: pd.Series, lookback: int = 60) -> pd.DataFrame:
    """
    s1, s2: price series of two cointegrated instruments
    Returns DataFrame with spread, zscore and signal
    """
    df = pd.DataFrame({"s1": s1, "s2": s2}).dropna()

    # Rolling OLS hedge ratio
    hedge = df["s1"].rolling(lookback).cov(df["s2"]) / df["s2"].rolling(lookback).var()
    df["spread"]   = df["s1"] - hedge * df["s2"]
    df["mean"]     = df["spread"].rolling(lookback).mean()
    df["std"]      = df["spread"].rolling(lookback).std()
    df["zscore"]   = (df["spread"] - df["mean"]) / df["std"].replace(0, np.nan)

    df["signal"] = 0
    df.loc[df["zscore"] <= -2.0, "signal"] = 1   # spread too low -> long s1, short s2
    df.loc[df["zscore"] >= 2.0,  "signal"] = -1  # spread too high -> short s1, long s2

    return df


def get_signal(s1: pd.Series, s2: pd.Series, lookback: int = 60) -> int:
    df = calculate_spread(s1, s2, lookback)
    return int(df["signal"].iloc[-1])
