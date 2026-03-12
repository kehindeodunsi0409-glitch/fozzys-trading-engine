"""
Donchian Channel Breakout Strategy
Best TF: H4/D1
Signal: Price breaks above upper or below lower channel
"""

import pandas as pd
import numpy as np


def calculate_donchian(df: pd.DataFrame, period: int = 20) -> pd.DataFrame:
    df = df.copy()
    df["upper"]  = df["high"].rolling(period).max()
    df["lower"]  = df["low"].rolling(period).min()
    df["middle"] = (df["upper"] + df["lower"]) / 2

    df["signal"] = 0
    df.loc[df["close"] >= df["upper"].shift(1), "signal"] = 1
    df.loc[df["close"] <= df["lower"].shift(1), "signal"] = -1

    return df


def get_signal(df: pd.DataFrame, period: int = 20) -> int:
    df = calculate_donchian(df, period)
    return int(df["signal"].iloc[-1])
