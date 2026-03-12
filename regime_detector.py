# =============================================================================
#  regime_detector.py
#
#  Uses a Hidden Markov Model (HMM) to classify the current market regime.
#
#  WHY HMM:
#  Markets switch between hidden states (trending, ranging, volatile) that
#  drive price behaviour. HMM learns these states purely from price data -
#  no rules, no indicators, no human assumptions.
#  It then tells you: "right now we are in state X" so you pick the right
#  strategy for that state.
#
#  3 STATES:
#  After training the model labels each bar as state 0, 1, or 2.
#  You'll see in the logs which state corresponds to what behaviour.
#  Typically:
#    Low vol state  → ranging → mean reversion works
#    Med vol state  → trending → momentum works
#    High vol state → spiky/news → sit out
# =============================================================================

import numpy as np
import pandas as pd
import pickle
import os
import logging
from datetime import datetime
from hmmlearn.hmm import GaussianHMM

logger = logging.getLogger(__name__)


def build_features(df: pd.DataFrame) -> np.ndarray:
    """
    Build feature matrix from OHLCV data.
    Features: log returns, rolling volatility, normalised ATR, volume ratio.
    All normalised so HMM treats them equally.
    """
    feat = pd.DataFrame(index=df.index)

    # 1. Log returns - captures direction and magnitude
    feat['returns'] = np.log(df['close'] / df['close'].shift(1))

    # 2. Rolling volatility (20-bar std of returns) - regime signature
    feat['volatility'] = feat['returns'].rolling(20).std()

    # 3. ATR normalised by price - volatility relative to price level
    high_low   = df['high'] - df['low']
    high_close = (df['high'] - df['close'].shift(1)).abs()
    low_close  = (df['low']  - df['close'].shift(1)).abs()
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    atr = tr.rolling(14).mean()
    feat['atr_norm'] = atr / df['close']

    # 4. Volume relative to its 20-bar mean - detects institutional activity
    vol_ma = df['volume'].rolling(20).mean()
    feat['vol_ratio'] = df['volume'] / vol_ma.replace(0, np.nan)

    # Drop NaN rows (from rolling windows)
    feat = feat.dropna()

    # Normalise each feature to zero mean, unit variance
    from sklearn.preprocessing import StandardScaler
    scaler = StandardScaler()
    X = scaler.fit_transform(feat.values)

    return X, feat.index, scaler


class RegimeDetector:
    """
    Wraps a GaussianHMM with training, prediction, persistence, and
    regime labelling logic.
    """

    def __init__(self, symbol: str, n_states: int = 3, model_dir: str = "models/"):
        self.symbol    = symbol
        self.n_states  = n_states
        self.model_dir = model_dir
        self.model     = None
        self.scaler    = None
        self.vol_order = {0:0, 1:1, 2:2}  # default, overwritten on train/load
        self.last_trained = None
        os.makedirs(model_dir, exist_ok=True)

    @property
    def model_path(self):
        return os.path.join(self.model_dir, f"hmm_{self.symbol}.pkl")

    def train(self, df: pd.DataFrame):
        """
        Train HMM on historical OHLCV data.
        Called on first run and every HMM_RETRAIN_DAYS after.
        """
        logger.info(f"[{self.symbol}] Training HMM on {len(df)} bars...")

        X, idx, scaler = build_features(df)
        if len(X) < 100:
            logger.error(f"[{self.symbol}] Not enough data to train ({len(X)} rows)")
            return False

        # Train HMM - multiple restarts to find best fit
        best_model = None
        best_score = -np.inf
        for seed in range(5):
            try:
                model = GaussianHMM(
                    n_components=self.n_states,
                    covariance_type="full",
                    n_iter=200,
                    random_state=seed,
                    tol=1e-4
                )
                model.fit(X)
                score = model.score(X)
                if score > best_score:
                    best_score = score
                    best_model = model
            except Exception as e:
                logger.warning(f"HMM seed {seed} failed: {e}")

        if best_model is None:
            logger.error(f"[{self.symbol}] HMM training failed")
            return False

        self.model       = best_model
        self.scaler      = scaler
        self.last_trained = datetime.utcnow()

        # Characterise each state so we can log what it means
        self._label_states(X, df, idx)

        # Persist model
        with open(self.model_path, 'wb') as f:
            pickle.dump({"model": self.model, "scaler": self.scaler,
                         "state_labels": self.state_labels,
                         "vol_order": self.vol_order,
                         "trained": self.last_trained}, f)

        logger.info(f"[{self.symbol}] HMM trained. Score={best_score:.2f} | "
                    f"States: {self.state_labels}")
        return True

    def _label_states(self, X, df, idx):
        """
        After training, characterise each state by its average volatility.
        Sorts states: 0=lowest vol, 1=medium vol, 2=highest vol.
        This gives consistent meaning to state numbers across retrains.
        """
        states = self.model.predict(X)
        df_feat = df.loc[idx].copy()
        df_feat['state'] = states

        # Compute mean ATR per state
        high_low = df_feat['high'] - df_feat['low']
        state_vols = {}
        for s in range(self.n_states):
            mask = df_feat['state'] == s
            avg_range = high_low[mask].mean() if mask.sum() > 0 else 0
            state_vols[s] = avg_range

        # Sort by volatility: state with lowest vol → 0, highest → 2
        sorted_states = sorted(state_vols, key=state_vols.get)
        self.vol_order = {old: new for new, old in enumerate(sorted_states)}
        self.state_labels = {}
        for orig, reordered in self.vol_order.items():
            label = ["Ranging", "Trending", "Volatile"][reordered]
            avg   = state_vols[orig]
            self.state_labels[orig] = f"{label} (avg_range={avg:.2f})"

    def load(self) -> bool:
        """Load previously trained model from disk."""
        if not os.path.exists(self.model_path):
            return False
        try:
            with open(self.model_path, 'rb') as f:
                data = pickle.load(f)
            self.model        = data['model']
            self.scaler       = data['scaler']
            self.state_labels = data.get('state_labels', {})
            self.vol_order    = data.get('vol_order', {0:0,1:1,2:2})
            self.last_trained = data.get('trained')
            logger.info(f"[{self.symbol}] HMM loaded (trained: {self.last_trained})")
            return True
        except KeyError:
            logger.warning(f"[{self.symbol}] HMM model outdated - will retrain")
            if os.path.exists(self.model_path):
                os.remove(self.model_path)
            return False
        except Exception as e:
            logger.error(f"[{self.symbol}] HMM load failed: {e}")
            return False

    def needs_retrain(self, retrain_days: int = 7) -> bool:
        if self.last_trained is None:
            return True
        age = (datetime.utcnow() - self.last_trained).total_seconds() / 86400
        return age >= retrain_days

    def predict(self, df: pd.DataFrame) -> dict:
        """
        Predict current regime from latest bars.
        Returns dict with state, label, strategy, and confidence.
        """
        if self.model is None:
            return {"state": -1, "label": "Unknown", "strategy": "sit_out",
                    "confidence": 0}

        X, idx, _ = build_features(df)
        # Apply same scaler from training
        X_scaled = self.scaler.transform(
            pd.DataFrame(X, columns=range(X.shape[1])).values
            if hasattr(X, 'shape') else X
        )

        # Predict sequence - take last state as current regime
        try:
            # Re-scale using trained scaler
            feat = pd.DataFrame(index=df.index)
            feat['returns']    = np.log(df['close'] / df['close'].shift(1))
            feat['volatility'] = feat['returns'].rolling(20).std()
            hl = df['high'] - df['low']
            hc = (df['high'] - df['close'].shift(1)).abs()
            lc = (df['low']  - df['close'].shift(1)).abs()
            tr = pd.concat([hl,hc,lc],axis=1).max(axis=1)
            feat['atr_norm']  = tr.rolling(14).mean() / df['close']
            vol_ma = df['volume'].rolling(20).mean()
            feat['vol_ratio'] = df['volume'] / vol_ma.replace(0, np.nan)
            feat = feat.dropna()

            X_raw    = feat.values
            X_scaled = self.scaler.transform(X_raw)
            states   = self.model.predict(X_scaled)
            current  = int(states[-1])

            # Get posterior probability for confidence
            log_probs = self.model.predict_proba(X_scaled)
            confidence = float(log_probs[-1][current])

            # Remap to volatility-ordered state
            ordered = self.vol_order.get(current, current)
            from config import REGIME_STRATEGIES
            strategy = REGIME_STRATEGIES.get(ordered, "sit_out")
            label    = ["Ranging", "Trending", "Volatile"][ordered]

            return {
                "state":      ordered,
                "raw_state":  current,
                "label":      label,
                "strategy":   strategy,
                "confidence": round(confidence, 3),
            }
        except Exception as e:
            logger.error(f"[{self.symbol}] Predict failed: {e}")
            return {"state": -1, "label": "Error", "strategy": "sit_out",
                    "confidence": 0}
