"""
ATR Volatility Breakout Strategy
Best TF: H1
Signal: Price moves more than N x ATR from open within the session
"""

import pandas as pd
import numpy as np


def calculate_signals(df: pd.DataFrame, atr_period: int = 14,
                      atr_multiplier: float = 1.5) -> pd.DataFrame:
    df = df.copy()
    df.index   = pd.to_datetime(pd.to_datetime(df.index), utc=True)
    df["date"] = df.index.date

    df["atr"]        = (df["high"] - df["low"]).rolling(atr_period).mean()
    daily_open       = df.groupby("date")["open"].first()
    df["daily_open"] = df["date"].map(daily_open)

    move_up   = df["close"] - df["daily_open"]
    move_down = df["daily_open"] - df["close"]
    threshold = atr_multiplier * df["atr"]

    df["signal"] = 0
    df.loc[(move_up > threshold)   & (move_up.shift(1)   <= threshold.shift(1)), "signal"] = 1
    df.loc[(move_down > threshold) & (move_down.shift(1) <= threshold.shift(1)), "signal"] = -1

    return df


def get_signal(df: pd.DataFrame, atr_multiplier: float = 1.5) -> int:
    df = calculate_signals(df, atr_multiplier=atr_multiplier)
    return int(df["signal"].iloc[-1])
