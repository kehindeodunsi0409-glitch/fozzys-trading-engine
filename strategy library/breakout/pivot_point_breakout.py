"""
Pivot Point Breakout Strategy
Best TF: H1
Signal: Price breaks through daily pivot levels (R1/R2/S1/S2)
Supports: Classical, Camarilla, Woodie
"""

import pandas as pd
import numpy as np


def calculate_pivots(prev_high: float, prev_low: float, prev_close: float,
                     method: str = "classical") -> dict:
    if method == "classical":
        pp = (prev_high + prev_low + prev_close) / 3
        r1 = (2 * pp) - prev_low
        r2 = pp + (prev_high - prev_low)
        s1 = (2 * pp) - prev_high
        s2 = pp - (prev_high - prev_low)
    elif method == "camarilla":
        diff = prev_high - prev_low
        pp = (prev_high + prev_low + prev_close) / 3
        r1 = prev_close + diff * 1.1 / 12
        r2 = prev_close + diff * 1.1 / 6
        s1 = prev_close - diff * 1.1 / 12
        s2 = prev_close - diff * 1.1 / 6
    elif method == "woodie":
        pp = (prev_high + prev_low + 2 * prev_close) / 4
        r1 = (2 * pp) - prev_low
        r2 = pp + (prev_high - prev_low)
        s1 = (2 * pp) - prev_high
        s2 = pp - (prev_high - prev_low)
    else:
        raise ValueError("method must be classical, camarilla or woodie")

    return {"pp": pp, "r1": r1, "r2": r2, "s1": s1, "s2": s2}


def calculate_signals(df: pd.DataFrame, method: str = "classical") -> pd.DataFrame:
    """df index must be UTC datetime."""
    df = df.copy()
    df.index  = pd.to_datetime(df.index, utc=True)
    df["date"] = df.index.date

    # Calculate previous day OHLC
    daily = df.groupby("date").agg(
        high=("high", "max"), low=("low", "min"), close=("close", "last")
    ).shift(1)

    for level in ["pp", "r1", "r2", "s1", "s2"]:
        df[level] = np.nan

    for date, row in daily.iterrows():
        if pd.isna(row["high"]):
            continue
        pivots = calculate_pivots(row["high"], row["low"], row["close"], method)
        mask = df["date"] == date
        for k, v in pivots.items():
            df.loc[mask, k] = v

    df["signal"] = 0
    df.loc[(df["close"] > df["r1"]) & (df["close"].shift(1) <= df["r1"]), "signal"] = 1
    df.loc[(df["close"] < df["s1"]) & (df["close"].shift(1) >= df["s1"]), "signal"] = -1

    return df


def get_signal(df: pd.DataFrame, method: str = "classical") -> int:
    df = calculate_signals(df, method)
    return int(df["signal"].iloc[-1])
