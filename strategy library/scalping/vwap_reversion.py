"""
VWAP Reversion Scalping Strategy
Best TF: M5/M15
Signal: Price deviates from VWAP then reverts back — fade the deviation
"""

import pandas as pd
import numpy as np


def calculate_vwap(df: pd.DataFrame) -> pd.DataFrame:
    """
    df index must be UTC datetime.
    VWAP resets at the start of each trading day.
    """
    df = df.copy()
    df.index  = pd.to_datetime(df.index, utc=True)
    df["date"] = df.index.date
    df["tp"]   = (df["high"] + df["low"] + df["close"]) / 3

    vwap_list = []
    for date, group in df.groupby("date"):
        cum_tpv = (group["tp"] * group["volume"]).cumsum()
        cum_vol = group["volume"].cumsum()
        vwap    = cum_tpv / cum_vol.replace(0, np.nan)
        vwap_list.append(vwap)

    df["vwap"] = pd.concat(vwap_list)
    df["std"]  = df.groupby("date")["close"].transform(lambda x: x.expanding().std())
    df["vwap_upper"] = df["vwap"] + df["std"]
    df["vwap_lower"] = df["vwap"] - df["std"]

    # Fade: price was outside band, now crossing back inside
    was_above = df["close"].shift(1) > df["vwap_upper"].shift(1)
    was_below = df["close"].shift(1) < df["vwap_lower"].shift(1)
    back_in   = (df["close"] <= df["vwap_upper"]) & (df["close"] >= df["vwap_lower"])

    df["signal"] = 0
    df.loc[was_above & back_in, "signal"] = -1
    df.loc[was_below & back_in, "signal"] = 1

    return df


def get_signal(df: pd.DataFrame) -> int:
    """df must include 'volume' column and UTC datetime index."""
    df = calculate_vwap(df)
    return int(df["signal"].iloc[-1])
