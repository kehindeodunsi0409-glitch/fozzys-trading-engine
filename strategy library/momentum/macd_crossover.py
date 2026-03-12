"""
MACD Crossover Strategy
Best TF: H1/H4
Signal: MACD line crosses signal line, confirmed by histogram direction
"""

import pandas as pd
import numpy as np


def calculate_macd(df: pd.DataFrame,
                   fast: int = 12, slow: int = 26, signal: int = 9) -> pd.DataFrame:
    df = df.copy()
    df["ema_fast"]  = df["close"].ewm(span=fast,   adjust=False).mean()
    df["ema_slow"]  = df["close"].ewm(span=slow,   adjust=False).mean()
    df["macd"]      = df["ema_fast"] - df["ema_slow"]
    df["macd_sig"]  = df["macd"].ewm(span=signal,  adjust=False).mean()
    df["histogram"] = df["macd"] - df["macd_sig"]

    # Crossover entry
    cross_up   = (df["macd"] > df["macd_sig"]) & (df["macd"].shift(1) <= df["macd_sig"].shift(1))
    cross_down = (df["macd"] < df["macd_sig"]) & (df["macd"].shift(1) >= df["macd_sig"].shift(1))

    df["signal"] = 0
    df.loc[cross_up,   "signal"] = 1
    df.loc[cross_down, "signal"] = -1

    return df


def get_signal(df: pd.DataFrame) -> int:
    df = calculate_macd(df)
    return int(df["signal"].iloc[-1])
