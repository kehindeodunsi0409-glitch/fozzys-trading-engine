"""
Parabolic SAR Strategy
Best TF: H1
Signal: Price crosses above/below SAR dot
"""

import pandas as pd
import numpy as np


def calculate_psar(df: pd.DataFrame, af_start: float = 0.02, af_step: float = 0.02, af_max: float = 0.2) -> pd.DataFrame:
    df   = df.copy()
    high = df["high"].values
    low  = df["low"].values
    n    = len(df)

    sar       = np.zeros(n)
    ep        = np.zeros(n)
    af        = np.zeros(n)
    bull      = np.ones(n, dtype=bool)

    sar[0]  = low[0]
    ep[0]   = high[0]
    af[0]   = af_start
    bull[0] = True

    for i in range(1, n):
        prev_bull = bull[i - 1]
        prev_sar  = sar[i - 1]
        prev_ep   = ep[i - 1]
        prev_af   = af[i - 1]

        if prev_bull:
            new_sar = prev_sar + prev_af * (prev_ep - prev_sar)
            new_sar = min(new_sar, low[i - 1], low[i - 2] if i >= 2 else low[i - 1])
            if low[i] < new_sar:
                bull[i] = False
                sar[i]  = prev_ep
                ep[i]   = low[i]
                af[i]   = af_start
            else:
                bull[i] = True
                sar[i]  = new_sar
                if high[i] > prev_ep:
                    ep[i] = high[i]
                    af[i] = min(prev_af + af_step, af_max)
                else:
                    ep[i] = prev_ep
                    af[i] = prev_af
        else:
            new_sar = prev_sar - prev_af * (prev_sar - prev_ep)
            new_sar = max(new_sar, high[i - 1], high[i - 2] if i >= 2 else high[i - 1])
            if high[i] > new_sar:
                bull[i] = True
                sar[i]  = prev_ep
                ep[i]   = high[i]
                af[i]   = af_start
            else:
                bull[i] = False
                sar[i]  = new_sar
                if low[i] < prev_ep:
                    ep[i] = low[i]
                    af[i] = min(prev_af + af_step, af_max)
                else:
                    ep[i] = prev_ep
                    af[i] = prev_af

    df["psar"]   = sar
    df["signal"] = np.where(bull, 1, -1)
    df["entry"]  = pd.Series(df["signal"]).diff().fillna(0)
    df["entry"]  = df["entry"].apply(lambda x: 1 if x > 0 else (-1 if x < 0 else 0))
    return df


def get_signal(df: pd.DataFrame) -> int:
    df = calculate_psar(df)
    return int(df["entry"].iloc[-1])
