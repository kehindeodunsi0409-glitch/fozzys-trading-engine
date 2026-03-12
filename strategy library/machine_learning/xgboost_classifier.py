"""
XGBoost Signal Classifier Strategy
Best TF: M15/H1
Signal: XGBoost model classifies next bar direction
Requires: xgboost, scikit-learn
"""

import pandas as pd
import numpy as np
import pickle
import os


# ── Feature Engineering ───────────────────────────────────────────────────────

def build_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for p in [1, 3, 5, 10, 20]:
        df[f"ret_{p}"] = df["close"].pct_change(p)

    for p in [8, 21, 50]:
        df[f"ema_{p}"] = df["close"].ewm(span=p, adjust=False).mean()
        df[f"ema_{p}_dist"] = (df["close"] - df[f"ema_{p}"]) / df["close"]

    delta = df["close"].diff()
    gain  = delta.clip(lower=0).ewm(com=13, adjust=False).mean()
    loss  = (-delta.clip(upper=0)).ewm(com=13, adjust=False).mean()
    df["rsi"] = 100 - (100 / (1 + gain / loss.replace(0, np.nan)))
    df["rsi_lag1"] = df["rsi"].shift(1)

    df["atr"]      = (df["high"] - df["low"]).rolling(14).mean()
    df["atr_norm"] = df["atr"] / df["close"]

    mid = df["close"].rolling(20).mean()
    std = df["close"].rolling(20).std()
    df["bb_pct"] = (df["close"] - (mid - 2 * std)) / (4 * std).replace(0, np.nan)
    df["bb_width"] = (4 * std) / mid

    body   = abs(df["close"] - df["open"])
    candle = (df["high"] - df["low"]).replace(0, np.nan)
    df["body_ratio"]  = body / candle
    df["upper_wick"]  = (df["high"] - df[["open", "close"]].max(axis=1)) / candle
    df["lower_wick"]  = (df[["open", "close"]].min(axis=1) - df["low"])  / candle
    df["is_bull"]     = (df["close"] > df["open"]).astype(int)

    if "volume" in df.columns:
        df["vol_ratio"] = df["volume"] / df["volume"].rolling(20).mean()

    drop_cols = ["open", "high", "low", "close", "volume",
                 "ema_8", "ema_21", "ema_50"]
    feat_cols = [c for c in df.columns if c not in drop_cols]
    return df[feat_cols].dropna()


# ── Training ──────────────────────────────────────────────────────────────────

def train(df: pd.DataFrame, model_path: str = "xgb_model.pkl",
          forward_bars: int = 3, min_move_atr: float = 0.5):
    from xgboost import XGBClassifier
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import classification_report
    from sklearn.preprocessing import LabelEncoder

    features = build_features(df)
    atr      = (df["high"] - df["low"]).rolling(14).mean()
    fwd      = df["close"].shift(-forward_bars) - df["close"]
    thresh   = min_move_atr * atr
    labels   = pd.Series(0, index=df.index)
    labels[fwd >  thresh] = 1
    labels[fwd < -thresh] = -1
    labels = labels.reindex(features.index).dropna()
    features = features.reindex(labels.index)

    le = LabelEncoder()
    y  = le.fit_transform(labels)

    X_tr, X_te, y_tr, y_te = train_test_split(features, y, test_size=0.2, shuffle=False)

    clf = XGBClassifier(
        n_estimators=300, max_depth=6, learning_rate=0.05,
        subsample=0.8, colsample_bytree=0.8,
        use_label_encoder=False, eval_metric="mlogloss",
        random_state=42, n_jobs=-1
    )
    clf.fit(X_tr, y_tr, eval_set=[(X_te, y_te)], verbose=False)
    print(classification_report(y_te, clf.predict(X_te), target_names=[str(c) for c in le.classes_]))

    with open(model_path, "wb") as f:
        pickle.dump((clf, le), f)
    print(f"XGB model saved to {model_path}")
    return clf, le


# ── Inference ─────────────────────────────────────────────────────────────────

def get_signal(df: pd.DataFrame, model_path: str = "xgb_model.pkl",
               min_proba: float = 0.55) -> int:
    if not os.path.exists(model_path):
        return 0

    with open(model_path, "rb") as f:
        clf, le = pickle.load(f)

    features = build_features(df)
    if features.empty:
        return 0

    proba    = clf.predict_proba(features.iloc[[-1]])[0]
    best_idx = np.argmax(proba)

    if proba[best_idx] < min_proba:
        return 0
    return int(le.classes_[best_idx])
