"""
HMM Regime Detection Strategy
Best TF: H1/H4
Signal: Hidden Markov Model classifies market regime (trending/ranging/volatile)
        then applies regime-appropriate signal
Requires: hmmlearn
"""

import numpy as np
import pandas as pd
import pickle
import os


N_STATES = 3   # 0=ranging, 1=trending_up, 2=trending_down (labels assigned post-hoc)


# ── Feature Engineering ───────────────────────────────────────────────────────

def build_obs(df: pd.DataFrame) -> np.ndarray:
    """Build observation matrix for HMM."""
    ret     = df["close"].pct_change().fillna(0)
    atr     = (df["high"] - df["low"]).rolling(14).mean().fillna(method="bfill")
    vol_ret = ret.rolling(10).std().fillna(method="bfill")
    return np.column_stack([ret.values, vol_ret.values, atr.values / df["close"].values])


# ── Training ──────────────────────────────────────────────────────────────────

def train(df: pd.DataFrame, model_path: str = "hmm_model.pkl"):
    from hmmlearn.hmm import GaussianHMM

    obs = build_obs(df)
    model = GaussianHMM(n_components=N_STATES, covariance_type="full",
                        n_iter=200, random_state=42)
    model.fit(obs)

    # Assign regime labels based on mean returns per state
    states   = model.predict(obs)
    state_df = pd.DataFrame({"state": states, "ret": df["close"].pct_change().fillna(0).values})
    means    = state_df.groupby("state")["ret"].mean()
    sorted_s = means.sort_values()
    label_map = {
        sorted_s.index[0]: -1,  # lowest mean ret = downtrend
        sorted_s.index[1]:  0,  # middle = ranging
        sorted_s.index[2]:  1,  # highest mean ret = uptrend
    }

    with open(model_path, "wb") as f:
        pickle.dump((model, label_map), f)
    print(f"HMM model saved to {model_path}")
    return model, label_map


# ── Inference ─────────────────────────────────────────────────────────────────

def get_regime(df: pd.DataFrame, model_path: str = "hmm_model.pkl") -> int:
    """Returns regime: 1=uptrend, -1=downtrend, 0=ranging"""
    if not os.path.exists(model_path):
        return 0

    with open(model_path, "rb") as f:
        model, label_map = pickle.load(f)

    obs   = build_obs(df)
    state = model.predict(obs)[-1]
    return label_map.get(state, 0)


def get_signal(df: pd.DataFrame, model_path: str = "hmm_model.pkl") -> int:
    """
    In trending regimes, return trend-following signal via EMA.
    In ranging regime, return 0 (sit out or use mean reversion separately).
    """
    regime = get_regime(df, model_path)
    if regime == 0:
        return 0

    # Simple EMA confirmation in trending regime
    ema_fast = df["close"].ewm(span=10, adjust=False).mean()
    ema_slow = df["close"].ewm(span=30, adjust=False).mean()
    ema_sig  = 1 if ema_fast.iloc[-1] > ema_slow.iloc[-1] else -1

    # Only take signal if EMA agrees with regime direction
    if ema_sig == regime:
        return regime
    return 0
