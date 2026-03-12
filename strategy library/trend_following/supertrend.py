"""
Supertrend Strategy
Best TF: H1/H4
Signal: Price crosses above/below Supertrend line
"""

import pandas as pd
import numpy as np


def calculate_supertrend(df: pd.DataFrame, period: int = 10, multiplier: float = 3.0) -> pd.DataFrame:
    df = df.copy()
    hl2 = (df["high"] + df["low"]) / 2

    # ATR
    df["tr"] = np.maximum(
        df["high"] - df["low"],
        np.maximum(
            abs(df["high"] - df["close"].shift(1)),
            abs(df["low"] - df["close"].shift(1))
        )
    )
    df["atr"] = df["tr"].ewm(span=period, adjust=False).mean()

    df["upper"] = hl2 + (multiplier * df["atr"])
    df["lower"] = hl2 - (multiplier * df["atr"])

    supertrend = [np.nan] * len(df)
    direction  = [0] * len(df)

    for i in range(1, len(df)):
        if df["close"].iloc[i] > supertrend[i - 1] if not np.isnan(supertrend[i - 1]) else True:
            supertrend[i] = df["lower"].iloc[i]
            direction[i]  = 1
        else:
            supertrend[i] = df["upper"].iloc[i]
            direction[i]  = -1

    df["supertrend"] = supertrend
    df["signal"]     = direction
    df["entry"]      = pd.Series(direction).diff().fillna(0)
    df["entry"]      = df["entry"].apply(lambda x: 1 if x > 0 else (-1 if x < 0 else 0))

    return df


def get_signal(df: pd.DataFrame, period: int = 10, multiplier: float = 3.0) -> int:
    df = calculate_supertrend(df, period, multiplier)
    return int(df["entry"].iloc[-1])
