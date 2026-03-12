"""
Session Range Breakout Strategy
Best TF: M15/H1
Signal: Price breaks above/below Asian or London session range
Asian session:  00:00 - 08:00 UTC
London session: 08:00 - 16:00 UTC
"""

import pandas as pd
import numpy as np
from datetime import time


def get_session_range(df: pd.DataFrame, session: str = "asian",
                      atr_filter: float = 0.0) -> pd.DataFrame:
    """
    df index must be UTC datetime.
    session: 'asian' (00-08 UTC) or 'london' (08-16 UTC)
    atr_filter: minimum ATR multiple range must be to qualify
    """
    df = df.copy()
    df.index = pd.to_datetime(df.index, utc=True)

    if session == "asian":
        start_h, end_h = 0, 8
    elif session == "london":
        start_h, end_h = 8, 16
    else:
        raise ValueError("session must be 'asian' or 'london'")

    df["date"]     = df.index.date
    df["hour"]     = df.index.hour
    in_session     = (df["hour"] >= start_h) & (df["hour"] < end_h)

    daily_high = df[in_session].groupby("date")["high"].max()
    daily_low  = df[in_session].groupby("date")["low"].min()

    df["session_high"] = df["date"].map(daily_high)
    df["session_low"]  = df["date"].map(daily_low)

    # ATR for range quality filter
    df["atr"] = (df["high"] - df["low"]).rolling(14).mean()

    # Only trade after session closes
    post_session = df["hour"] >= end_h

    df["signal"] = 0
    broke_up   = post_session & (df["close"] > df["session_high"]) & (df["close"].shift(1) <= df["session_high"].shift(1))
    broke_down = post_session & (df["close"] < df["session_low"])  & (df["close"].shift(1) >= df["session_low"].shift(1))

    if atr_filter > 0:
        range_ok = (df["session_high"] - df["session_low"]) >= (atr_filter * df["atr"])
        broke_up   = broke_up   & range_ok
        broke_down = broke_down & range_ok

    df.loc[broke_up,   "signal"] = 1
    df.loc[broke_down, "signal"] = -1

    return df


def get_signal(df: pd.DataFrame, session: str = "asian") -> int:
    df = get_session_range(df, session)
    return int(df["signal"].iloc[-1])
