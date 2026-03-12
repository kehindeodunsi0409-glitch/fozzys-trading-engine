# =============================================================================
#  strategies.py  —  FXMIXED v2
#  Strategies: rsi_divergence / supertrend / liquidity_grab
# =============================================================================

import numpy as np
import pandas as pd
import logging

logger = logging.getLogger(__name__)


# ── Indicators ────────────────────────────────────────────────────────────────

def ema(series: pd.Series, period: int) -> pd.Series:
    return series.ewm(span=period, adjust=False).mean()

def atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    hl  = df['high'] - df['low']
    hc  = (df['high'] - df['close'].shift(1)).abs()
    lc  = (df['low']  - df['close'].shift(1)).abs()
    tr  = pd.concat([hl, hc, lc], axis=1).max(axis=1)
    return tr.ewm(span=period, adjust=False).mean()

def rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    gain  = delta.clip(lower=0).ewm(span=period, adjust=False).mean()
    loss  = (-delta.clip(upper=0)).ewm(span=period, adjust=False).mean()
    rs    = gain / loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


# ── RSI Divergence Strategy ───────────────────────────────────────────────────

def rsi_divergence_signal(df: pd.DataFrame, cfg: dict) -> dict | None:
    rsi_p      = cfg.get("rsi_period", 14)
    atr_p      = cfg.get("atr_period", 14)
    atr_m      = cfg.get("atr_sl_mult", 2.0)
    min_rr     = cfg.get("min_rr", 2.0)
    lookback   = cfg.get("div_lookback", 30)
    swing_bars = cfg.get("swing_bars", 3)

    if len(df) < lookback + swing_bars + 5:
        return None

    atr_val = atr(df, atr_p)
    rsi_val = rsi(df['close'], rsi_p)
    a1      = atr_val.iloc[-2]

    if a1 is None or np.isnan(a1) or a1 <= 0:
        return None

    scan      = df.iloc[-lookback:]
    rsi_scan  = rsi_val.iloc[-lookback:]
    close1    = df['close'].iloc[-2]

    swing_lows  = []
    swing_highs = []

    for i in range(swing_bars, len(scan) - swing_bars - 1):
        bar_low  = scan['low'].iloc[i]
        bar_high = scan['high'].iloc[i]

        is_swing_low  = all(bar_low  <= scan['low'].iloc[i-j]  for j in range(1, swing_bars+1)) and \
                        all(bar_low  <= scan['low'].iloc[i+j]  for j in range(1, swing_bars+1))
        is_swing_high = all(bar_high >= scan['high'].iloc[i-j] for j in range(1, swing_bars+1)) and \
                        all(bar_high >= scan['high'].iloc[i+j] for j in range(1, swing_bars+1))

        if is_swing_low:
            swing_lows.append((i, bar_low, rsi_scan.iloc[i]))
        if is_swing_high:
            swing_highs.append((i, bar_high, rsi_scan.iloc[i]))

    if len(swing_lows) >= 2:
        prev = swing_lows[-2]
        last = swing_lows[-1]
        if (last[1] < prev[1]) and (last[2] > prev[2]):
            sl_dist = a1 * atr_m
            tp_dist = sl_dist * min_rr
            if sl_dist > 0:
                signal = {
                    "strategy": "rsi_divergence", "direction": 1,
                    "entry": round(close1, 5),
                    "sl": round(close1 - sl_dist, 5),
                    "tp": round(close1 + tp_dist, 5),
                    "sl_dist": round(sl_dist, 5), "tp_dist": round(tp_dist, 5),
                    "rr": round(tp_dist / sl_dist, 2), "atr": round(a1, 5),
                    "reason": f"Bullish divergence | price LL={last[1]:.5f} RSI HL={last[2]:.1f}",
                }
                logger.info(f"RSI_DIVERGENCE BUY @ {close1} | SL={signal['sl']} TP={signal['tp']} | RR=1:{signal['rr']}")
                return signal

    if len(swing_highs) >= 2:
        prev = swing_highs[-2]
        last = swing_highs[-1]
        if (last[1] > prev[1]) and (last[2] < prev[2]):
            sl_dist = a1 * atr_m
            tp_dist = sl_dist * min_rr
            if sl_dist > 0:
                signal = {
                    "strategy": "rsi_divergence", "direction": -1,
                    "entry": round(close1, 5),
                    "sl": round(close1 + sl_dist, 5),
                    "tp": round(close1 - tp_dist, 5),
                    "sl_dist": round(sl_dist, 5), "tp_dist": round(tp_dist, 5),
                    "rr": round(tp_dist / sl_dist, 2), "atr": round(a1, 5),
                    "reason": f"Bearish divergence | price HH={last[1]:.5f} RSI LH={last[2]:.1f}",
                }
                logger.info(f"RSI_DIVERGENCE SELL @ {close1} | SL={signal['sl']} TP={signal['tp']} | RR=1:{signal['rr']}")
                return signal

    return None


# ── Supertrend Strategy ───────────────────────────────────────────────────────

def supertrend_signal(df: pd.DataFrame, cfg: dict) -> dict | None:
    atr_p   = cfg.get("atr_period", 14)
    st_mult = cfg.get("st_multiplier", 3.0)
    min_rr  = cfg.get("min_rr", 2.0)

    if len(df) < atr_p + 10:
        return None

    atr_val = atr(df, atr_p)
    hl2     = (df['high'] + df['low']) / 2
    upper_band = hl2 + st_mult * atr_val
    lower_band = hl2 - st_mult * atr_val

    supertrend = pd.Series(index=df.index, dtype=float)
    direction  = pd.Series(index=df.index, dtype=int)

    for i in range(1, len(df)):
        curr_close = df['close'].iloc[i]
        prev_close = df['close'].iloc[i-1]

        ub = upper_band.iloc[i] if upper_band.iloc[i] < upper_band.iloc[i-1] or prev_close > upper_band.iloc[i-1] else upper_band.iloc[i-1]
        lb = lower_band.iloc[i] if lower_band.iloc[i] > lower_band.iloc[i-1] or prev_close < lower_band.iloc[i-1] else lower_band.iloc[i-1]

        if supertrend.iloc[i-1] == upper_band.iloc[i-1]:
            if curr_close <= ub:
                supertrend.iloc[i] = ub
                direction.iloc[i]  = -1
            else:
                supertrend.iloc[i] = lb
                direction.iloc[i]  = 1
        else:
            if curr_close >= lb:
                supertrend.iloc[i] = lb
                direction.iloc[i]  = 1
            else:
                supertrend.iloc[i] = ub
                direction.iloc[i]  = -1

    a1       = atr_val.iloc[-2]
    close1   = df['close'].iloc[-2]
    st_level = supertrend.iloc[-2]
    dir_curr = direction.iloc[-2]
    dir_prev = direction.iloc[-3]

    if a1 is None or np.isnan(a1) or a1 <= 0:
        return None
    if np.isnan(st_level) or st_level <= 0:
        return None

    flipped_up   = (dir_prev == -1) and (dir_curr == 1)
    flipped_down = (dir_prev == 1)  and (dir_curr == -1)

    if not flipped_up and not flipped_down:
        return None

    direction_val = 1 if flipped_up else -1
    sl_dist = abs(close1 - st_level)
    tp_dist = sl_dist * min_rr

    if sl_dist <= 0:
        return None

    sl = round(st_level, 5)
    tp = round(close1 + direction_val * tp_dist, 5)

    signal = {
        "strategy": "supertrend", "direction": direction_val,
        "entry": round(close1, 5), "sl": sl, "tp": tp,
        "sl_dist": round(sl_dist, 5), "tp_dist": round(tp_dist, 5),
        "rr": round(tp_dist / sl_dist, 2), "atr": round(a1, 5),
        "reason": f"Supertrend flip {'up' if flipped_up else 'down'} | ST={st_level:.5f}",
    }
    logger.info(f"SUPERTREND {'BUY' if direction_val==1 else 'SELL'} @ {close1} | SL={sl} TP={tp} | RR=1:{signal['rr']}")
    return signal


# ── Liquidity Grab Reversal ───────────────────────────────────────────────────

def liquidity_grab_signal(df: pd.DataFrame, cfg: dict) -> dict | None:
    """
    Liquidity Grab Reversal.
    Market makers push price beyond a recent swing high/low to trigger
    stop orders, then reverse sharply. We enter on the rejection.

    Bullish grab: bar wicks below swing low but closes above it
    Bearish grab: bar wicks above swing high but closes below it

    SL: beyond the wick extreme
    TP: 2R from entry
    """
    atr_p    = cfg.get("atr_period", 14)
    atr_m    = cfg.get("atr_sl_mult", 1.5)
    min_rr   = cfg.get("min_rr", 2.0)
    lookback = cfg.get("lg_lookback", 20)
    min_wick = cfg.get("lg_min_wick", 0.3)

    if len(df) < lookback + 5:
        return None

    atr_val = atr(df, atr_p)
    a1      = atr_val.iloc[-2]

    if a1 is None or np.isnan(a1) or a1 <= 0:
        return None

    bar       = df.iloc[-2]
    bar_high  = bar['high']
    bar_low   = bar['low']
    bar_close = bar['close']

    lookback_bars = df.iloc[-lookback-2:-2]
    swing_high    = lookback_bars['high'].max()
    swing_low     = lookback_bars['low'].min()

    bull_wick = swing_low - bar_low
    bull_grab = (bar_low < swing_low) and (bar_close > swing_low) and (bull_wick > a1 * min_wick)

    bear_wick = bar_high - swing_high
    bear_grab = (bar_high > swing_high) and (bar_close < swing_high) and (bear_wick > a1 * min_wick)

    if not bull_grab and not bear_grab:
        return None

    direction = 1 if bull_grab else -1
    entry     = bar_close

    if direction == 1:
        sl_dist = (entry - bar_low) + a1 * 0.3
    else:
        sl_dist = (bar_high - entry) + a1 * 0.3

    tp_dist = sl_dist * min_rr

    if sl_dist <= 0:
        return None

    sl = round(entry - direction * sl_dist, 5)
    tp = round(entry + direction * tp_dist, 5)
    wick_size = bull_wick if bull_grab else bear_wick

    signal = {
        "strategy": "liquidity_grab", "direction": direction,
        "entry": round(entry, 5), "sl": sl, "tp": tp,
        "sl_dist": round(sl_dist, 5), "tp_dist": round(tp_dist, 5),
        "rr": round(tp_dist / sl_dist, 2), "atr": round(a1, 5),
        "reason": f"{'Bull' if bull_grab else 'Bear'} liq grab | level={swing_low if bull_grab else swing_high:.5f} wick={wick_size:.5f}",
    }
    logger.info(f"LIQUIDITY_GRAB {'BUY' if direction==1 else 'SELL'} @ {entry} | SL={sl} TP={tp} | RR=1:{signal['rr']} | {signal['reason']}")
    return signal


# ── Dispatcher ────────────────────────────────────────────────────────────────

def get_signal(df: pd.DataFrame, strategy: str, cfg: dict) -> dict | None:
    if strategy == "rsi_divergence":
        return rsi_divergence_signal(df, cfg)
    elif strategy == "supertrend":
        return supertrend_signal(df, cfg)
    elif strategy == "liquidity_grab":
        return liquidity_grab_signal(df, cfg)
    elif strategy == "sit_out":
        return None
    else:
        logger.warning(f"Unknown strategy: {strategy}")
        return None
