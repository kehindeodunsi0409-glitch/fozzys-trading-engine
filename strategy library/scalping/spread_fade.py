"""
Spread Fade Scalping Strategy
Best TF: M1
Signal: Temporary spread widening followed by normalisation
        Used for very short-term scalping when spread spikes above average
        NOTE: Requires bid/ask data — uses synthetic spread from OHLC if unavailable
"""

import pandas as pd
import numpy as np


def estimate_spread(df: pd.DataFrame, lookback: int = 20) -> pd.Series:
    """
    If bid/ask columns exist, use real spread.
    Otherwise estimate from OHLC: spread ~ high - open or close - low proxy.
    """
    if "ask" in df.columns and "bid" in df.columns:
        return df["ask"] - df["bid"]
    # Fallback: use intrabar range as spread proxy
    return df["high"] - df["low"]


def calculate_signals(df: pd.DataFrame,
                      spread_multiplier: float = 2.0,
                      lookback: int = 20) -> pd.DataFrame:
    """
    Signal when spread spikes above average then reverts:
    - If spread was very wide and price is near session open -> fade
    """
    df = df.copy()
    df["spread"]     = estimate_spread(df, lookback)
    df["avg_spread"] = df["spread"].rolling(lookback).mean()
    df["spread_z"]   = (df["spread"] - df["avg_spread"]) / df["spread"].rolling(lookback).std().replace(0, np.nan)

    spike   = df["spread"].shift(1) >= spread_multiplier * df["avg_spread"].shift(1)
    reverts = df["spread"] < df["avg_spread"]

    # After a spike resolves: trade in direction price moved after spike
    df["signal"] = 0
    bull_after = spike & reverts & (df["close"] > df["open"])
    bear_after = spike & reverts & (df["close"] < df["open"])

    df.loc[bull_after, "signal"] = 1
    df.loc[bear_after, "signal"] = -1

    return df


def get_signal(df: pd.DataFrame, spread_multiplier: float = 2.0) -> int:
    df = calculate_signals(df, spread_multiplier)
    return int(df["signal"].iloc[-1])
