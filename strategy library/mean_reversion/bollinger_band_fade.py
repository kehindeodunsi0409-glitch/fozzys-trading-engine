"""
Bollinger Band Fade Strategy
Best TF: M15/H1
Signal: Price touches/closes outside band then reverts back inside
"""

import pandas as pd
import numpy as np


def calculate_bbands(df: pd.DataFrame, period: int = 20, std_dev: float = 2.0) -> pd.DataFrame:
    df = df.copy()
    df["bb_mid"]   = df["close"].rolling(period).mean()
    df["bb_std"]   = df["close"].rolling(period).std()
    df["bb_upper"] = df["bb_mid"] + (std_dev * df["bb_std"])
    df["bb_lower"] = df["bb_mid"] - (std_dev * df["bb_std"])
    df["bb_pct"]   = (df["close"] - df["bb_lower"]) / (df["bb_upper"] - df["bb_lower"]).replace(0, np.nan)

    # Fade: price was outside band and re-enters
    was_above = df["close"].shift(1) > df["bb_upper"].shift(1)
    was_below = df["close"].shift(1) < df["bb_lower"].shift(1)
    back_in   = (df["close"] <= df["bb_upper"]) & (df["close"] >= df["bb_lower"])

    df["signal"] = 0
    df.loc[was_above & back_in, "signal"] = -1  # fade the upper band touch
    df.loc[was_below & back_in, "signal"] = 1   # fade the lower band touch

    return df


def get_signal(df: pd.DataFrame, period: int = 20, std_dev: float = 2.0) -> int:
    df = calculate_bbands(df, period, std_dev)
    return int(df["signal"].iloc[-1])
