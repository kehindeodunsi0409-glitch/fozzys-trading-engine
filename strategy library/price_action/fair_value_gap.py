"""
Fair Value Gap (FVG) Strategy — ICT Concept
Best TF: M15/H1
Signal: Price returns to fill an unfilled FVG in the direction of the trend
Bullish FVG: gap between candle[i-2] high and candle[i] low
Bearish FVG: gap between candle[i-2] low and candle[i] high
"""

import pandas as pd
import numpy as np


def calculate_fvgs(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["bull_fvg_top"]    = np.nan
    df["bull_fvg_bottom"] = np.nan
    df["bear_fvg_top"]    = np.nan
    df["bear_fvg_bottom"] = np.nan

    for i in range(2, len(df)):
        c0 = df.iloc[i]      # current
        c2 = df.iloc[i - 2]  # two bars back

        # Bullish FVG: c2 high < c0 low (gap up — unfilled space below current)
        if c2["high"] < c0["low"]:
            df.iloc[i, df.columns.get_loc("bull_fvg_top")]    = c0["low"]
            df.iloc[i, df.columns.get_loc("bull_fvg_bottom")] = c2["high"]

        # Bearish FVG: c2 low > c0 high (gap down — unfilled space above current)
        if c2["low"] > c0["high"]:
            df.iloc[i, df.columns.get_loc("bear_fvg_top")]    = c2["low"]
            df.iloc[i, df.columns.get_loc("bear_fvg_bottom")] = c0["high"]

    return df


def calculate_signals(df: pd.DataFrame, ema_period: int = 50) -> pd.DataFrame:
    df = calculate_fvgs(df)
    df["ema"] = df["close"].ewm(span=ema_period, adjust=False).mean()

    # Track open FVGs
    open_bull_fvgs = []  # list of (bottom, top)
    open_bear_fvgs = []

    df["signal"] = 0

    for i in range(len(df)):
        row = df.iloc[i]

        # Register new FVGs
        if not np.isnan(row["bull_fvg_top"]):
            open_bull_fvgs.append((row["bull_fvg_bottom"], row["bull_fvg_top"]))
        if not np.isnan(row["bear_fvg_top"]):
            open_bear_fvgs.append((row["bear_fvg_bottom"], row["bear_fvg_top"]))

        # Check if price enters a bull FVG (in uptrend = long signal)
        if row["close"] > row["ema"]:
            for bottom, top in open_bull_fvgs:
                if bottom <= row["low"] <= top:
                    df.iloc[i, df.columns.get_loc("signal")] = 1
                    break

        # Check if price enters a bear FVG (in downtrend = short signal)
        if row["close"] < row["ema"]:
            for bottom, top in open_bear_fvgs:
                if bottom <= row["high"] <= top:
                    df.iloc[i, df.columns.get_loc("signal")] = -1
                    break

        # Expire filled FVGs
        open_bull_fvgs = [(b, t) for b, t in open_bull_fvgs if row["low"] > b]
        open_bear_fvgs = [(b, t) for b, t in open_bear_fvgs if row["high"] < t]

    return df


def get_signal(df: pd.DataFrame) -> int:
    df = calculate_signals(df)
    return int(df["signal"].iloc[-1])
