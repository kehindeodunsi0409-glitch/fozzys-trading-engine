"""
Random Forest Classification Strategy
Best TF: M15/H1
Signal: Trained RF model predicts next bar direction from technical features
Requires: scikit-learn
"""

import pandas as pd
import numpy as np
import pickle
import os
from typing import Optional


# ── Feature Engineering ──────────────────────────────────────────────────────

def build_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # Returns
    for p in [1, 3, 5, 10]:
        df[f"ret_{p}"] = df["close"].pct_change(p)

    # EMAs
    for p in [8, 21, 50, 200]:
        df[f"ema_{p}"] = df["close"].ewm(span=p, adjust=False).mean()

    df["ema_8_21_dist"]  = (df["ema_8"]  - df["ema_21"])  / df["close"]
    df["ema_21_50_dist"] = (df["ema_21"] - df["ema_50"])  / df["close"]

    # RSI
    delta = df["close"].diff()
    gain  = delta.clip(lower=0).ewm(com=13, adjust=False).mean()
    loss  = (-delta.clip(upper=0)).ewm(com=13, adjust=False).mean()
    df["rsi"] = 100 - (100 / (1 + gain / loss.replace(0, np.nan)))

    # ATR normalised
    df["atr"] = (df["high"] - df["low"]).rolling(14).mean()
    df["atr_norm"] = df["atr"] / df["close"]

    # Bollinger %B
    mid = df["close"].rolling(20).mean()
    std = df["close"].rolling(20).std()
    df["bb_pct"] = (df["close"] - (mid - 2 * std)) / (4 * std).replace(0, np.nan)

    # Volume ratio
    if "volume" in df.columns:
        df["vol_ratio"] = df["volume"] / df["volume"].rolling(20).mean()

    # Candle body ratio
    body    = abs(df["close"] - df["open"])
    candle  = (df["high"] - df["low"]).replace(0, np.nan)
    df["body_ratio"]  = body / candle
    df["upper_wick"]  = (df["high"] - df[["open", "close"]].max(axis=1)) / candle
    df["lower_wick"]  = (df[["open", "close"]].min(axis=1) - df["low"])  / candle

    feature_cols = [c for c in df.columns if c not in ["open", "high", "low", "close", "volume"]]
    return df[feature_cols].dropna()


# ── Label Generation ──────────────────────────────────────────────────────────

def build_labels(df: pd.DataFrame, forward_bars: int = 3,
                 min_move_atr: float = 0.5) -> pd.Series:
    """
    1  = up move >= min_move_atr * ATR over next N bars
    -1 = down move
    0  = flat
    """
    atr    = (df["high"] - df["low"]).rolling(14).mean()
    fwd    = df["close"].shift(-forward_bars) - df["close"]
    thresh = min_move_atr * atr

    labels = pd.Series(0, index=df.index)
    labels[fwd >  thresh] = 1
    labels[fwd < -thresh] = -1
    return labels


# ── Training ──────────────────────────────────────────────────────────────────

def train(df: pd.DataFrame, model_path: str = "rf_model.pkl",
          forward_bars: int = 3, min_move_atr: float = 0.5):
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import classification_report

    features = build_features(df)
    labels   = build_labels(df, forward_bars, min_move_atr).reindex(features.index).dropna()
    features = features.reindex(labels.index)

    X_train, X_test, y_train, y_test = train_test_split(
        features, labels, test_size=0.2, shuffle=False
    )

    clf = RandomForestClassifier(
        n_estimators=200, max_depth=8, min_samples_leaf=20,
        class_weight="balanced", random_state=42, n_jobs=-1
    )
    clf.fit(X_train, y_train)
    print(classification_report(y_test, clf.predict(X_test)))

    with open(model_path, "wb") as f:
        pickle.dump(clf, f)
    print(f"Model saved to {model_path}")
    return clf


# ── Inference ─────────────────────────────────────────────────────────────────

def get_signal(df: pd.DataFrame, model_path: str = "rf_model.pkl",
               min_proba: float = 0.55) -> int:
    if not os.path.exists(model_path):
        return 0

    with open(model_path, "rb") as f:
        clf = pickle.load(f)

    features = build_features(df)
    if features.empty:
        return 0

    last_row = features.iloc[[-1]]
    proba    = clf.predict_proba(last_row)[0]
    classes  = clf.classes_

    best_idx   = np.argmax(proba)
    best_proba = proba[best_idx]
    best_class = classes[best_idx]

    if best_proba >= min_proba and best_class != 0:
        return int(best_class)
    return 0
