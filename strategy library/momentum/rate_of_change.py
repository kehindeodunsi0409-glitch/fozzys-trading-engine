"""
Rate of Change (ROC) Strategy
Best TF: H1/H4
Signal: ROC crosses zero line with momentum confirmation
"""

import pandas as pd
import numpy as np


def calculate_roc(df: pd.DataFrame, period: int = 12, smooth: int = 3) -> pd.DataFrame:
    df = df.copy()
    df["roc"]        = ((df["close"] - df["close"].shift(period)) / df["close"].shift(period)) * 100
    df["roc_smooth"] = df["roc"].rolling(smooth).mean()

    cross_up   = (df["roc_smooth"] > 0) & (df["roc_smooth"].shift(1) <= 0)
    cross_down = (df["roc_smooth"] < 0) & (df["roc_smooth"].shift(1) >= 0)

    df["signal"] = 0
    df.loc[cross_up,   "signal"] = 1
    df.loc[cross_down, "signal"] = -1

    return df


def get_signal(df: pd.DataFrame, period: int = 12) -> int:
    df = calculate_roc(df, period)
    return int(df["signal"].iloc[-1])
