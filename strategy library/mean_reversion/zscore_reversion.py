"""
Z-Score Mean Reversion Strategy
Best TF: H1
Signal: Price deviates significantly from rolling mean (z-score extreme)
"""

import pandas as pd
import numpy as np


def calculate_zscore(df: pd.DataFrame, period: int = 20,
                     entry_z: float = 2.0, exit_z: float = 0.5) -> pd.DataFrame:
    df = df.copy()
    df["mean"]    = df["close"].rolling(period).mean()
    df["std"]     = df["close"].rolling(period).std()
    df["zscore"]  = (df["close"] - df["mean"]) / df["std"].replace(0, np.nan)

    # Entry at extremes, exit near mean
    df["signal"] = 0
    df.loc[df["zscore"] <= -entry_z, "signal"] = 1   # oversold extreme -> long
    df.loc[df["zscore"] >= entry_z,  "signal"] = -1  # overbought extreme -> short

    return df


def get_signal(df: pd.DataFrame, period: int = 20, entry_z: float = 2.0) -> int:
    df = calculate_zscore(df, period, entry_z)
    return int(df["signal"].iloc[-1])
