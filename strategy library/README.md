# Python Strategy Library

A collection of standalone trading strategy modules. Each file exposes a
`get_signal(df) -> int` function returning:

  1  = Long signal
 -1  = Short signal
  0  = No signal / neutral

All strategies expect a pandas DataFrame with columns:
  open, high, low, close, volume (where applicable)

---

## Folder Structure

```
strategies/
├── trend_following/
│   ├── ema_sma_crossover.py      H1/H4
│   ├── supertrend.py             H1/H4
│   ├── donchian_breakout.py      H4/D1
│   ├── adx_directional.py        H1/H4
│   ├── parabolic_sar.py          H1
│   └── ichimoku_cloud.py         H4/D1
│
├── momentum/
│   ├── rsi_pullback.py           M15/H1
│   ├── macd_crossover.py         H1/H4
│   ├── stochastic_trend.py       M15/H1
│   ├── rate_of_change.py         H1/H4
│   └── cci_breakout.py           H1
│
├── mean_reversion/
│   ├── bollinger_band_fade.py    M15/H1
│   ├── rsi_extreme_reversal.py   M15/H1
│   ├── zscore_reversion.py       H1
│   └── pairs_cointegration.py    H1/H4
│
├── breakout/
│   ├── session_range_breakout.py M15/H1
│   ├── pivot_point_breakout.py   H1
│   ├── prev_day_hl_breakout.py   H1/H4
│   └── atr_volatility_breakout.py H1
│
├── price_action/
│   ├── pin_bar_sr.py             H1/H4
│   ├── engulfing_structure.py    H1/H4
│   ├── inside_bar_breakout.py    H4
│   ├── break_and_retest.py       H1/H4
│   └── fair_value_gap.py         M15/H1
│
├── machine_learning/
│   ├── random_forest.py          M15/H1  (sklearn)
│   ├── lstm_prediction.py        H1/H4   (tensorflow)
│   ├── xgboost_classifier.py     M15/H1  (xgboost)
│   └── hmm_regime.py             H1/H4   (hmmlearn)
│
├── statistical/
│   ├── kalman_filter_trend.py    H1/H4
│   ├── hurst_exponent.py         H4/D1
│   ├── arima_forecast.py         H1/H4   (statsmodels)
│   └── fourier_cycle.py          H4/D1
│
├── sentiment_macro/
│   ├── cot_positioning.py        D1 bias
│   ├── retail_sentiment_fade.py  H1/H4
│   └── economic_calendar_filter.py  Any TF (filter/guard)
│
└── scalping/
    ├── vwap_reversion.py         M5/M15
    ├── tick_volume_spike.py      M1/M5
    └── spread_fade.py            M1
```

---

## Usage Example

```python
import MetaTrader5 as mt5
import pandas as pd
from strategies.trend_following.ema_sma_crossover import get_signal

mt5.initialize()
bars = mt5.copy_rates_from_pos("EURUSD", mt5.TIMEFRAME_H1, 0, 300)
df   = pd.DataFrame(bars)
df.columns = [c.lower() for c in df.columns]

signal = get_signal(df)
print(signal)  # 1, -1, or 0
```

---

## ML Strategies — Train First

```python
from strategies.machine_learning.random_forest import train, get_signal

# Train once
train(df, model_path="rf_eurusd_h1.pkl")

# Then use
signal = get_signal(df, model_path="rf_eurusd_h1.pkl")
```

---

## Notes

- `economic_calendar_filter.py` is a **guard** not a signal generator.
  Use it to block entries before high-impact news.
- All datetime-aware strategies expect UTC index.
- For TREND_PY integration, wrap any `get_signal()` call in the
  Gate 4 entry logic and respect Gates 1–3 upstream.
