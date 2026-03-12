"""
Tick Volume Spike Scalping Strategy
Best TF: M1/M5
Signal: Large volume spike with directional candle suggests momentum continuation
"""

import pandas as pd
import numpy as np


def calculate_signals(df: pd.DataFrame,
                      vol_multiplier: float = 2.0,
                      vol_lookback: int = 20,
                      body_min_pct: float = 0.5) -> pd.DataFrame:
    """
    vol_multiplier: volume must be N x average to qualify
    body_min_pct: candle body must be >= this fraction of candle range
    """
    df = df.copy()
    df["avg_vol"]    = df["volume"].rolling(vol_lookback).mean()
    df["vol_spike"]  = df["volume"] >= (vol_multiplier * df["avg_vol"])

    body   = abs(df["close"] - df["open"])
    candle = (df["high"] - df["low"]).replace(0, np.nan)
    df["body_pct"] = body / candle

    bull_spike = df["vol_spike"] & (df["close"] > df["open"]) & (df["body_pct"] >= body_min_pct)
    bear_spike = df["vol_spike"] & (df["close"] < df["open"]) & (df["body_pct"] >= body_min_pct)

    df["signal"] = 0
    df.loc[bull_spike, "signal"] = 1
    df.loc[bear_spike, "signal"] = -1

    return df


def get_signal(df: pd.DataFrame,
               vol_multiplier: float = 2.0,
               body_min_pct: float = 0.5) -> int:
    df = calculate_signals(df, vol_multiplier, body_min_pct=body_min_pct)
    return int(df["signal"].iloc[-1])
