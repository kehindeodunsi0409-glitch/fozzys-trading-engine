"""
LSTM Price Prediction Strategy
Best TF: H1/H4
Signal: LSTM predicts next bar direction from sequence of OHLCV features
Requires: tensorflow / keras, scikit-learn
"""

import numpy as np
import pandas as pd
import os
import pickle


SEQUENCE_LEN = 30   # bars of lookback fed into LSTM
FEATURES     = ["ret_1", "rsi", "atr_norm", "bb_pct", "body_ratio"]


# ── Feature Engineering ───────────────────────────────────────────────────────

def build_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["ret_1"]      = df["close"].pct_change()
    delta            = df["close"].diff()
    gain             = delta.clip(lower=0).ewm(com=13, adjust=False).mean()
    loss             = (-delta.clip(upper=0)).ewm(com=13, adjust=False).mean()
    df["rsi"]        = 100 - (100 / (1 + gain / loss.replace(0, np.nan)))
    df["atr"]        = (df["high"] - df["low"]).rolling(14).mean()
    df["atr_norm"]   = df["atr"] / df["close"]
    mid              = df["close"].rolling(20).mean()
    std              = df["close"].rolling(20).std()
    df["bb_pct"]     = (df["close"] - (mid - 2 * std)) / (4 * std).replace(0, np.nan)
    body             = abs(df["close"] - df["open"])
    candle           = (df["high"] - df["low"]).replace(0, np.nan)
    df["body_ratio"] = body / candle
    return df[FEATURES].dropna()


def build_sequences(features: np.ndarray, labels: np.ndarray, seq_len: int):
    X, y = [], []
    for i in range(seq_len, len(features)):
        X.append(features[i - seq_len:i])
        y.append(labels[i])
    return np.array(X), np.array(y)


# ── Training ──────────────────────────────────────────────────────────────────

def train(df: pd.DataFrame, model_path: str = "lstm_model.keras",
          scaler_path: str = "lstm_scaler.pkl",
          forward_bars: int = 3, epochs: int = 30):
    from sklearn.preprocessing import StandardScaler
    from sklearn.utils.class_weight import compute_class_weight
    import tensorflow as tf

    feat_df = build_features(df)
    atr     = (df["high"] - df["low"]).rolling(14).mean()
    fwd     = df["close"].shift(-forward_bars) - df["close"]
    thresh  = 0.5 * atr
    labels  = pd.Series(0, index=df.index)
    labels[fwd >  thresh] = 1
    labels[fwd < -thresh] = 2  # keras needs 0-indexed classes
    labels = labels.reindex(feat_df.index).fillna(0).astype(int)

    scaler  = StandardScaler()
    scaled  = scaler.fit_transform(feat_df.values)
    X, y    = build_sequences(scaled, labels.values, SEQUENCE_LEN)

    split   = int(len(X) * 0.8)
    X_tr, X_te = X[:split], X[split:]
    y_tr, y_te = y[:split], y[split:]

    cw = compute_class_weight("balanced", classes=np.unique(y_tr), y=y_tr)
    cw_dict = {i: w for i, w in enumerate(cw)}

    model = tf.keras.Sequential([
        tf.keras.layers.LSTM(64, input_shape=(SEQUENCE_LEN, len(FEATURES)), return_sequences=True),
        tf.keras.layers.Dropout(0.2),
        tf.keras.layers.LSTM(32),
        tf.keras.layers.Dropout(0.2),
        tf.keras.layers.Dense(3, activation="softmax"),
    ])
    model.compile(optimizer="adam", loss="sparse_categorical_crossentropy", metrics=["accuracy"])
    model.fit(X_tr, y_tr, validation_data=(X_te, y_te),
              epochs=epochs, batch_size=32, class_weight=cw_dict, verbose=1)

    model.save(model_path)
    with open(scaler_path, "wb") as f:
        pickle.dump(scaler, f)
    print(f"LSTM model saved to {model_path}")


# ── Inference ─────────────────────────────────────────────────────────────────

def get_signal(df: pd.DataFrame,
               model_path: str  = "lstm_model.keras",
               scaler_path: str = "lstm_scaler.pkl",
               min_proba: float = 0.55) -> int:
    if not os.path.exists(model_path) or not os.path.exists(scaler_path):
        return 0

    import tensorflow as tf

    with open(scaler_path, "rb") as f:
        scaler = pickle.load(f)

    model    = tf.keras.models.load_model(model_path)
    feat_df  = build_features(df)
    if len(feat_df) < SEQUENCE_LEN:
        return 0

    seq      = scaler.transform(feat_df.values[-SEQUENCE_LEN:])
    proba    = model.predict(seq[np.newaxis], verbose=0)[0]
    best_idx = np.argmax(proba)

    if proba[best_idx] < min_proba:
        return 0
    # 0=flat, 1=long, 2=short
    return {0: 0, 1: 1, 2: -1}[best_idx]
