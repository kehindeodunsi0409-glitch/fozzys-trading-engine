"""
Fourier Cycle Analysis Strategy
Best TF: H4/D1
Signal: Dominant price cycles identified via FFT; signal based on cycle phase
"""

import pandas as pd
import numpy as np


def dominant_cycles(prices: np.ndarray, n_cycles: int = 3) -> list:
    """Returns dominant cycle periods (in bars) using FFT."""
    detrended = prices - np.polyval(np.polyfit(np.arange(len(prices)), prices, 1), np.arange(len(prices)))
    fft_vals  = np.fft.rfft(detrended)
    power     = np.abs(fft_vals) ** 2
    freqs     = np.fft.rfftfreq(len(prices))

    # Exclude DC (index 0) and very high frequencies
    power[0] = 0
    power[freqs > 0.4] = 0

    top_idx    = np.argsort(power)[::-1][:n_cycles]
    periods    = [int(1 / freqs[i]) for i in top_idx if freqs[i] > 0]
    return periods


def reconstruct_cycle(prices: np.ndarray, period: int) -> np.ndarray:
    """Reconstruct a single dominant cycle component."""
    n        = len(prices)
    detrend  = prices - np.polyval(np.polyfit(np.arange(n), prices, 1), np.arange(n))
    fft_vals = np.fft.rfft(detrend)
    freqs    = np.fft.rfftfreq(n)
    target   = 1.0 / period

    # Zero out all components except the target frequency band
    mask = np.abs(freqs - target) > (target * 0.3)
    fft_filtered = fft_vals.copy()
    fft_filtered[mask] = 0
    return np.fft.irfft(fft_filtered, n=n)


def calculate_signals(df: pd.DataFrame, lookback: int = 128) -> pd.DataFrame:
    df = df.copy()
    df["signal"] = 0

    for i in range(lookback, len(df)):
        prices  = df["close"].iloc[i - lookback:i].values
        cycles  = dominant_cycles(prices)
        if not cycles:
            continue

        # Use the dominant cycle
        main_cycle = cycles[0]
        if main_cycle < 4 or main_cycle > lookback // 2:
            continue

        reconstructed = reconstruct_cycle(prices, main_cycle)
        slope = reconstructed[-1] - reconstructed[-3]

        df.iloc[i, df.columns.get_loc("signal")] = 1 if slope > 0 else -1

    return df


def get_signal(df: pd.DataFrame, lookback: int = 128) -> int:
    df = calculate_signals(df, lookback)
    return int(df["signal"].iloc[-1])
