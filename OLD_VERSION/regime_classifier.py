import numpy as np
import pandas as pd
from hmmlearn.hmm import GaussianHMM
import matplotlib.pyplot as plt

class MarketRegimeHMM:
    def __init__(self, n_regimes=3):
        self.n_regimes = n_regimes
        self.model = GaussianHMM(
            n_components=n_regimes, 
            covariance_type="full", 
            n_iter=1000,
            random_state=42
        )
        self.means_ = None
        self.covars_ = None

    def prepare_features(self, df):
        """
        Engineers features for HMM:
        1. Log Returns
        2. High-Low Range (normalized by Close)
        3. Volatility (rolling std of returns)
        """
        data = df.copy()
        data['LogReturns'] = np.log(data['Close'] / data['Close'].shift(1))
        data['Range'] = (data['High'] - data['Low']) / data['Close']
        data['Volatility'] = data['LogReturns'].rolling(window=10).std()
        
        # Drop NaNs created by rolling/shift
        features = data[['LogReturns', 'Range', 'Volatility']].dropna()
        return features, data.index[len(data) - len(features):]

    def fit(self, features):
        """
        Trains the HMM on the provided features.
        """
        self.model.fit(features)
        self.means_ = self.model.means_
        self.covars_ = self.model.covars_

    def predict(self, features):
        """
        Predicts the hidden states (regimes).
        """
        return self.model.predict(features)

    def sort_regimes(self, features, states):
        """
        Map states to human-readable regimes based on volatility/variance.
        We assume:
        - State with lowest volatility = Ranging
        - State with highest volatility = Volatile
        - Intermediate state = Trending
        """
        # Calculate avg volatility per state
        # Features index 2 is Volatility
        state_vol = []
        for i in range(self.n_regimes):
            vol = features.iloc[states == i, 2].mean()
            state_vol.append((i, vol))
        
        # Sort by volatility
        sorted_states = sorted(state_vol, key=lambda x: x[1])
        
        mapping = {
            sorted_states[0][0]: 0, # Low Vol = Ranging
            sorted_states[1][0]: 1, # Mid Vol = Trending
            sorted_states[2][0]: 2  # High Vol = Volatile
        }
        return np.array([mapping[s] for s in states])

if __name__ == "__main__":
    # Example usage with dummy data
    from data_loader import fetch_data
    df = fetch_data("BTC-USD")
    if df is not None:
        hmm_model = MarketRegimeHMM()
        feats, idx = hmm_model.prepare_features(df)
        hmm_model.fit(feats)
        states = hmm_model.predict(feats)
        mapped_states = hmm_model.sort_regimes(feats, states)
        
        # Visualize
        plt.figure(figsize=(15, 6))
        plt.subplot(211)
        plt.plot(idx, df.loc[idx, 'Close'])
        plt.title("Price")
        
        plt.subplot(212)
        plt.scatter(idx, mapped_states, c=mapped_states, cmap='viridis')
        plt.title("HMM Regimes (0: Ranging, 1: Trending, 2: Volatile)")
        plt.show()
