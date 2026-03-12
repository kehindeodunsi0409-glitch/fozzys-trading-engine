"""
Engulfing Candle at Structure Strategy
Best TF: H1/H4
Signal: Bullish or bearish engulfing candle at a key S/R level
"""

import pandas as pd
import numpy as np


def calculate_signals(df: pd.DataFrame,
                      sr_lookback: int = 20,
                      sr_tolerance_atr: float = 0.5) -> pd.DataFrame:
    df = df.copy()
    df["atr"]     = (df["high"] - df["low"]).rolling(14).mean()
    df["sr_high"] = df["high"].rolling(sr_lookback).max().shift(1)
    df["sr_low"]  = df["low"].rolling(sr_lookback).min().shift(1)

    prev = df.shift(1)

    # Bullish engulfing: prev bearish, current bullish and engulfs prev body
    bull_eng = (
        (prev["close"] < prev["open"]) &         # prev candle bearish
        (df["close"] > df["open"]) &             # current candle bullish
        (df["open"] < prev["close"]) &           # opens below prev close
        (df["close"] > prev["open"])             # closes above prev open
    )

    # Bearish engulfing: prev bullish, current bearish and engulfs prev body
    bear_eng = (
        (prev["close"] > prev["open"]) &
        (df["close"] < df["open"]) &
        (df["open"] > prev["close"]) &
        (df["close"] < prev["open"])
    )

    tol      = sr_tolerance_atr * df["atr"]
    near_lo  = abs(df["low"]  - df["sr_low"])  <= tol
    near_hi  = abs(df["high"] - df["sr_high"]) <= tol

    df["signal"] = 0
    df.loc[bull_eng & near_lo, "signal"] = 1
    df.loc[bear_eng & near_hi, "signal"] = -1

    return df


def get_signal(df: pd.DataFrame) -> int:
    df = calculate_signals(df)
    return int(df["signal"].iloc[-1])
