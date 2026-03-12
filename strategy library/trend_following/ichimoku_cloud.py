"""
Ichimoku Cloud Breakout Strategy
Best TF: H4/D1
Signal: Price breaks above/below cloud (Kumo), confirmed by Tenkan/Kijun cross
"""

import pandas as pd
import numpy as np


def calculate_ichimoku(df: pd.DataFrame,
                       tenkan: int = 9, kijun: int = 26,
                       senkou_b: int = 52, displacement: int = 26) -> pd.DataFrame:
    df = df.copy()

    df["tenkan_sen"]  = (df["high"].rolling(tenkan).max()   + df["low"].rolling(tenkan).min())  / 2
    df["kijun_sen"]   = (df["high"].rolling(kijun).max()    + df["low"].rolling(kijun).min())   / 2
    df["senkou_a"]    = ((df["tenkan_sen"] + df["kijun_sen"]) / 2).shift(displacement)
    df["senkou_b"]    = ((df["high"].rolling(senkou_b).max() + df["low"].rolling(senkou_b).min()) / 2).shift(displacement)
    df["chikou_span"] = df["close"].shift(-displacement)

    cloud_top    = df[["senkou_a", "senkou_b"]].max(axis=1)
    cloud_bottom = df[["senkou_a", "senkou_b"]].min(axis=1)

    above_cloud = df["close"] > cloud_top
    below_cloud = df["close"] < cloud_bottom
    tk_bull     = df["tenkan_sen"] > df["kijun_sen"]
    tk_bear     = df["tenkan_sen"] < df["kijun_sen"]

    df["signal"] = 0
    df.loc[above_cloud & tk_bull, "signal"] = 1
    df.loc[below_cloud & tk_bear, "signal"] = -1

    df["entry"] = df["signal"].diff().fillna(0)
    df["entry"] = df["entry"].apply(lambda x: 1 if x > 0 else (-1 if x < 0 else 0))

    return df


def get_signal(df: pd.DataFrame) -> int:
    df = calculate_ichimoku(df)
    return int(df["entry"].iloc[-1])
