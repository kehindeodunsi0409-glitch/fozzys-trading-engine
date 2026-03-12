"""
Kalman Filter Trend Strategy
Best TF: H1/H4
Signal: Kalman filter estimates true price trend and velocity
        Long when velocity positive and accelerating, short when negative
"""

import pandas as pd
import numpy as np


def kalman_filter(prices: np.ndarray,
                  process_noise: float = 1e-4,
                  observation_noise: float = 1e-2) -> tuple:
    """
    Simple 2-state Kalman filter: [level, velocity]
    Returns arrays of filtered level and velocity.
    """
    n     = len(prices)
    level = np.zeros(n)
    vel   = np.zeros(n)

    # State transition: level += velocity
    F = np.array([[1, 1],
                  [0, 1]])
    H = np.array([[1, 0]])
    Q = process_noise  * np.eye(2)
    R = observation_noise

    x = np.array([prices[0], 0.0])
    P = np.eye(2)

    for i in range(n):
        # Predict
        x_pred = F @ x
        P_pred = F @ P @ F.T + Q

        # Update
        y     = prices[i] - H @ x_pred
        S     = H @ P_pred @ H.T + R
        K     = P_pred @ H.T / S[0, 0]
        x     = x_pred + K.flatten() * y[0]
        P     = (np.eye(2) - np.outer(K, H)) @ P_pred

        level[i] = x[0]
        vel[i]   = x[1]

    return level, vel


def calculate_signals(df: pd.DataFrame,
                      process_noise: float = 1e-4,
                      observation_noise: float = 1e-2) -> pd.DataFrame:
    df = df.copy()
    level, vel = kalman_filter(df["close"].values, process_noise, observation_noise)
    df["kf_level"] = level
    df["kf_vel"]   = vel

    vel_series = pd.Series(vel, index=df.index)
    vel_accel  = vel_series.diff()

    df["signal"] = 0
    df.loc[(vel_series > 0) & (vel_accel > 0), "signal"] = 1
    df.loc[(vel_series < 0) & (vel_accel < 0), "signal"] = -1

    return df


def get_signal(df: pd.DataFrame) -> int:
    df = calculate_signals(df)
    return int(df["signal"].iloc[-1])
