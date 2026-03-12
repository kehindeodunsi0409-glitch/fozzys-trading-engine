"""
Break and Retest Strategy
Best TF: H1/H4
Signal: Price breaks a key level, pulls back to retest it, then continues
"""

import pandas as pd
import numpy as np


def calculate_signals(df: pd.DataFrame,
                      lookback: int = 20,
                      retest_atr: float = 0.3,
                      max_retest_bars: int = 10) -> pd.DataFrame:
    df = df.copy()
    df["atr"]      = (df["high"] - df["low"]).rolling(14).mean()
    df["res"]      = df["high"].rolling(lookback).max().shift(1)
    df["sup"]      = df["low"].rolling(lookback).min().shift(1)

    df["signal"] = 0
    broke_res = None
    broke_sup = None
    break_bar = None

    for i in range(lookback + 1, len(df)):
        row = df.iloc[i]
        tol = retest_atr * row["atr"]

        # Check for fresh breakout
        if df.iloc[i - 1]["close"] > df.iloc[i - 1]["res"]:
            broke_res = df.iloc[i - 1]["res"]
            break_bar = i - 1
        if df.iloc[i - 1]["close"] < df.iloc[i - 1]["sup"]:
            broke_sup = df.iloc[i - 1]["sup"]
            break_bar = i - 1

        # Retest of broken resistance (now support)
        if broke_res and break_bar and (i - break_bar) <= max_retest_bars:
            if abs(row["low"] - broke_res) <= tol and row["close"] > broke_res:
                df.iloc[i, df.columns.get_loc("signal")] = 1
                broke_res = None

        # Retest of broken support (now resistance)
        if broke_sup and break_bar and (i - break_bar) <= max_retest_bars:
            if abs(row["high"] - broke_sup) <= tol and row["close"] < broke_sup:
                df.iloc[i, df.columns.get_loc("signal")] = -1
                broke_sup = None

    return df


def get_signal(df: pd.DataFrame) -> int:
    df = calculate_signals(df)
    return int(df["signal"].iloc[-1])
