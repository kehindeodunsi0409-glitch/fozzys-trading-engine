"""
Pin Bar at S/R Strategy
Best TF: H1/H4
Signal: Pin bar (hammer/shooting star) forming at a key support/resistance level
"""

import pandas as pd
import numpy as np


def is_pin_bar(row: pd.Series, direction: str,
               wick_ratio: float = 2.0, close_pct: float = 0.4) -> bool:
    body   = abs(row["close"] - row["open"])
    candle = row["high"] - row["low"]
    if candle == 0:
        return False

    if direction == "bull":
        lower_wick = min(row["open"], row["close"]) - row["low"]
        upper_wick = row["high"] - max(row["open"], row["close"])
        close_in_upper = (row["close"] - row["low"]) / candle >= (1 - close_pct)
        return (lower_wick >= wick_ratio * body) and close_in_upper and (lower_wick > upper_wick)

    elif direction == "bear":
        upper_wick = row["high"] - max(row["open"], row["close"])
        lower_wick = min(row["open"], row["close"]) - row["low"]
        close_in_lower = (row["high"] - row["close"]) / candle >= (1 - close_pct)
        return (upper_wick >= wick_ratio * body) and close_in_lower and (upper_wick > lower_wick)

    return False


def calculate_signals(df: pd.DataFrame,
                      sr_lookback: int = 20,
                      sr_tolerance_atr: float = 0.3) -> pd.DataFrame:
    df = df.copy()
    df["atr"]      = (df["high"] - df["low"]).rolling(14).mean()
    df["sr_high"]  = df["high"].rolling(sr_lookback).max().shift(1)
    df["sr_low"]   = df["low"].rolling(sr_lookback).min().shift(1)

    df["signal"] = 0
    for i in range(1, len(df)):
        row     = df.iloc[i]
        tol     = sr_tolerance_atr * row["atr"]
        near_lo = abs(row["low"] - row["sr_low"]) <= tol
        near_hi = abs(row["high"] - row["sr_high"]) <= tol

        if near_lo and is_pin_bar(row, "bull"):
            df.iloc[i, df.columns.get_loc("signal")] = 1
        elif near_hi and is_pin_bar(row, "bear"):
            df.iloc[i, df.columns.get_loc("signal")] = -1

    return df


def get_signal(df: pd.DataFrame) -> int:
    df = calculate_signals(df)
    return int(df["signal"].iloc[-1])
