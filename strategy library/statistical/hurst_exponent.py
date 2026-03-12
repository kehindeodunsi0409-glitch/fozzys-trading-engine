"""
Hurst Exponent Regime Filter
Best TF: H4/D1
Signal: Hurst > 0.55 = trending (use trend strategy)
        Hurst < 0.45 = mean reverting (use MR strategy)
        0.45 <= Hurst <= 0.55 = random walk (sit out)
"""

import pandas as pd
import numpy as np


def hurst_exponent(ts: np.ndarray, min_lag: int = 2, max_lag: int = 20) -> float:
    """R/S analysis Hurst exponent estimate."""
    lags  = range(min_lag, max_lag)
    tau   = []
    for lag in lags:
        sub = [ts[i:i + lag] for i in range(0, len(ts) - lag, lag)]
        if len(sub) < 2:
            continue
        rs_list = []
        for s in sub:
            if len(s) < 2:
                continue
            mean_s = np.mean(s)
            dev    = np.cumsum(s - mean_s)
            R      = np.max(dev) - np.min(dev)
            S      = np.std(s, ddof=1)
            if S > 0:
                rs_list.append(R / S)
        if rs_list:
            tau.append(np.mean(rs_list))

    if len(tau) < 2:
        return 0.5  # fallback to random walk

    lags_used = list(range(min_lag, min_lag + len(tau)))
    poly      = np.polyfit(np.log(lags_used), np.log(tau), 1)
    return poly[0]


def calculate_signals(df: pd.DataFrame,
                      lookback: int = 100,
                      trend_ema_fast: int = 10,
                      trend_ema_slow: int = 30,
                      mr_rsi_period: int = 14) -> pd.DataFrame:
    df = df.copy()
    df["hurst"]    = np.nan
    df["signal"]   = 0
    df["ema_fast"] = df["close"].ewm(span=trend_ema_fast, adjust=False).mean()
    df["ema_slow"] = df["close"].ewm(span=trend_ema_slow, adjust=False).mean()

    delta = df["close"].diff()
    gain  = delta.clip(lower=0).ewm(com=mr_rsi_period - 1, adjust=False).mean()
    loss  = (-delta.clip(upper=0)).ewm(com=mr_rsi_period - 1, adjust=False).mean()
    df["rsi"] = 100 - (100 / (1 + gain / loss.replace(0, np.nan)))

    for i in range(lookback, len(df)):
        window = df["close"].iloc[i - lookback:i].values
        h      = hurst_exponent(window)
        df.iloc[i, df.columns.get_loc("hurst")] = h

        if h > 0.55:   # trending
            sig = 1 if df["ema_fast"].iloc[i] > df["ema_slow"].iloc[i] else -1
        elif h < 0.45:  # mean reverting
            rsi = df["rsi"].iloc[i]
            sig = 1 if rsi < 35 else (-1 if rsi > 65 else 0)
        else:
            sig = 0

        df.iloc[i, df.columns.get_loc("signal")] = sig

    return df


def get_signal(df: pd.DataFrame, lookback: int = 100) -> int:
    df = calculate_signals(df, lookback)
    return int(df["signal"].iloc[-1])
