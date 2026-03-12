"""
ARIMA Forecasting Strategy
Best TF: H1/H4
Signal: ARIMA forecasts next close; if forecast > current = long, else short
Requires: statsmodels
"""

import pandas as pd
import numpy as np


def get_signal(df: pd.DataFrame,
               order: tuple = (2, 1, 2),
               forecast_steps: int = 1,
               min_move_pct: float = 0.0002) -> int:
    """
    order: ARIMA (p, d, q) params
    min_move_pct: minimum predicted % move to trigger a signal
    """
    try:
        from statsmodels.tsa.arima.model import ARIMA
        import warnings
        warnings.filterwarnings("ignore")

        series = df["close"].values[-200:]   # use last 200 bars for speed
        model  = ARIMA(series, order=order)
        fit    = model.fit()
        fc     = fit.forecast(steps=forecast_steps)
        pred   = fc.iloc[-1] if hasattr(fc, "iloc") else fc[-1]

        current = series[-1]
        move    = (pred - current) / current

        if move > min_move_pct:
            return 1
        elif move < -min_move_pct:
            return -1
        return 0

    except Exception:
        return 0
