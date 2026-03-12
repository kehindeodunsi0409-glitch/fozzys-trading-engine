"""
CCI Breakout Strategy
Best TF: H1
Signal: CCI breaks above +100 (long) or below -100 (short)
"""

import pandas as pd
import numpy as np


def calculate_cci(df: pd.DataFrame, period: int = 20,
                  long_threshold: float = 100.0,
                  short_threshold: float = -100.0) -> pd.DataFrame:
    df = df.copy()
    tp            = (df["high"] + df["low"] + df["close"]) / 3
    tp_ma         = tp.rolling(period).mean()
    mean_dev      = tp.rolling(period).apply(lambda x: np.mean(np.abs(x - x.mean())), raw=True)
    df["cci"]     = (tp - tp_ma) / (0.015 * mean_dev)

    cross_above = (df["cci"] > long_threshold)  & (df["cci"].shift(1) <= long_threshold)
    cross_below = (df["cci"] < short_threshold) & (df["cci"].shift(1) >= short_threshold)

    df["signal"] = 0
    df.loc[cross_above, "signal"] = 1
    df.loc[cross_below, "signal"] = -1

    return df


def get_signal(df: pd.DataFrame, period: int = 20) -> int:
    df = calculate_cci(df, period)
    return int(df["signal"].iloc[-1])
