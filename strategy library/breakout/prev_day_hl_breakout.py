"""
Previous Day High/Low Breakout Strategy
Best TF: H1/H4
Signal: Price breaks and closes above prev day high or below prev day low
"""

import pandas as pd
import numpy as np


def calculate_signals(df: pd.DataFrame, atr_buffer: float = 0.1) -> pd.DataFrame:
    """
    df index must be UTC datetime.
    atr_buffer: fraction of ATR added to breakout level to reduce false breaks
    """
    df = df.copy()
    df.index   = pd.to_datetime(df.index, utc=True)
    df["date"] = df.index.date

    daily = df.groupby("date").agg(
        high=("high", "max"), low=("low", "min")
    ).shift(1)

    df["prev_high"] = df["date"].map(daily["high"])
    df["prev_low"]  = df["date"].map(daily["low"])
    df["atr"]       = (df["high"] - df["low"]).rolling(14).mean()

    buffer = atr_buffer * df["atr"]

    broke_up   = (df["close"] > df["prev_high"] + buffer) & (df["close"].shift(1) <= df["prev_high"].shift(1) + buffer)
    broke_down = (df["close"] < df["prev_low"]  - buffer) & (df["close"].shift(1) >= df["prev_low"].shift(1)  - buffer)

    df["signal"] = 0
    df.loc[broke_up,   "signal"] = 1
    df.loc[broke_down, "signal"] = -1

    return df


def get_signal(df: pd.DataFrame) -> int:
    df = calculate_signals(df)
    return int(df["signal"].iloc[-1])
