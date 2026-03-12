"""
Inside Bar Breakout Strategy
Best TF: H4
Signal: Inside bar forms then price breaks the mother bar high/low
"""

import pandas as pd
import numpy as np


def calculate_signals(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    prev = df.shift(1)

    # Inside bar: current high < prev high AND current low > prev low
    is_inside = (df["high"] < prev["high"]) & (df["low"] > prev["low"])

    # Break of mother bar after inside bar
    mother_high = prev["high"].where(is_inside.shift(1).fillna(False))
    mother_low  = prev["low"].where(is_inside.shift(1).fillna(False))

    mother_high = mother_high.ffill()
    mother_low  = mother_low.ffill()

    broke_up   = (df["close"] > mother_high) & (df["close"].shift(1) <= mother_high.shift(1))
    broke_down = (df["close"] < mother_low)  & (df["close"].shift(1) >= mother_low.shift(1))

    df["signal"] = 0
    df.loc[broke_up,   "signal"] = 1
    df.loc[broke_down, "signal"] = -1

    return df


def get_signal(df: pd.DataFrame) -> int:
    df = calculate_signals(df)
    return int(df["signal"].iloc[-1])
