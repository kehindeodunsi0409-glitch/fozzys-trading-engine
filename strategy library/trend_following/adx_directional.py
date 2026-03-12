"""
ADX + Directional Index Strategy
Best TF: H1/H4
Signal: ADX > threshold confirms trend, DI+/DI- gives direction
"""

import pandas as pd
import numpy as np


def calculate_adx(df: pd.DataFrame, period: int = 14, adx_threshold: float = 25.0) -> pd.DataFrame:
    df = df.copy()

    df["tr"] = np.maximum(
        df["high"] - df["low"],
        np.maximum(
            abs(df["high"] - df["close"].shift(1)),
            abs(df["low"]  - df["close"].shift(1))
        )
    )
    df["dm_plus"]  = np.where((df["high"] - df["high"].shift(1)) > (df["low"].shift(1) - df["low"]),
                               np.maximum(df["high"] - df["high"].shift(1), 0), 0)
    df["dm_minus"] = np.where((df["low"].shift(1) - df["low"]) > (df["high"] - df["high"].shift(1)),
                               np.maximum(df["low"].shift(1) - df["low"], 0), 0)

    df["atr"]      = df["tr"].ewm(span=period, adjust=False).mean()
    df["di_plus"]  = 100 * df["dm_plus"].ewm(span=period, adjust=False).mean()  / df["atr"]
    df["di_minus"] = 100 * df["dm_minus"].ewm(span=period, adjust=False).mean() / df["atr"]
    df["dx"]       = 100 * abs(df["di_plus"] - df["di_minus"]) / (df["di_plus"] + df["di_minus"]).replace(0, np.nan)
    df["adx"]      = df["dx"].ewm(span=period, adjust=False).mean()

    df["signal"] = 0
    trend_on = df["adx"] >= adx_threshold
    df.loc[trend_on & (df["di_plus"] > df["di_minus"]), "signal"] = 1
    df.loc[trend_on & (df["di_minus"] > df["di_plus"]), "signal"] = -1

    df["entry"] = df["signal"].diff().fillna(0)
    df["entry"] = df["entry"].apply(lambda x: 1 if x > 0 else (-1 if x < 0 else 0))

    return df


def get_signal(df: pd.DataFrame, period: int = 14, adx_threshold: float = 25.0) -> int:
    df = calculate_adx(df, period, adx_threshold)
    return int(df["entry"].iloc[-1])
