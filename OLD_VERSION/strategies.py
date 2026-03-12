import pandas as pd
import numpy as np
import pandas_ta as ta

def mean_reversion_strategy(df):
    """
    Ranging Strategy: Bollinger Bands Mean Reversion.
    """
    data = df.copy()
    close = data['Close']
    if isinstance(close, pd.DataFrame):
        close = close.iloc[:, 0]
        
    bb = ta.bbands(close, length=20, std=2)
    if bb is None or bb.empty:
        return pd.Series(0, index=data.index)
        
    # Get column names dynamically to avoid naming mismatches
    lower_match = bb.filter(like='BBL')
    upper_match = bb.filter(like='BBU')
    
    if lower_match.empty or upper_match.empty:
        return pd.Series(0, index=data.index)
        
    lower_col = lower_match.columns[0]
    upper_col = upper_match.columns[0]
    
    data = pd.concat([data, bb], axis=1)
    
    # Signals
    data['signal'] = 0
    data.loc[data['Close'] < data[lower_col], 'signal'] = 1  # Buy
    data.loc[data['Close'] > data[upper_col], 'signal'] = -1 # Sell
    return data['signal']

def trend_following_strategy(df):
    """
    Trending Strategy: EMA Cross or MACD.
    """
    data = df.copy()
    ema_short = ta.ema(data['Close'], length=9)
    ema_long = ta.ema(data['Close'], length=21)
    data['ema_s'] = ema_short
    data['ema_l'] = ema_long
    
    # Signals
    data['signal'] = 0
    data.loc[data['ema_s'] > data['ema_l'], 'signal'] = 1  # Bullish
    data.loc[data['ema_s'] < data['ema_l'], 'signal'] = -1 # Bearish
    return data['signal']

def volatile_breakout_strategy(df):
    """
    Volatile Strategy: Donchian Channel Breakout.
    """
    data = df.copy()
    high = data['High']
    low = data['Low']
    if isinstance(high, pd.DataFrame): high = high.iloc[:, 0]
    if isinstance(low, pd.DataFrame): low = low.iloc[:, 0]
    
    donchian = ta.donchian(high, low, lower_length=20, upper_length=20)
    if donchian is None or donchian.empty:
        return pd.Series(0, index=data.index)
        
    upper_match = donchian.filter(like='DCH')
    lower_match = donchian.filter(like='DCL')
    
    if upper_match.empty or lower_match.empty:
        return pd.Series(0, index=data.index)
        
    upper_col = upper_match.columns[0]
    lower_col = lower_match.columns[0]
    
    data = pd.concat([data, donchian], axis=1)
    
    # Signals
    data['signal'] = 0
    data.loc[data['Close'] >= data[upper_col], 'signal'] = 1 # Breakout Up
    data.loc[data['Close'] <= data[lower_col], 'signal'] = -1 # Breakout Down
    return data['signal']

def apply_regime_strategies(df, states):
    """
    Applies the strategy mapping to each state.
    States: 0=Ranging, 1=Trending, 2=Volatile
    """
    signals = pd.Series(index=df.index, data=0)
    
    ranging_sigs = mean_reversion_strategy(df)
    trending_sigs = trend_following_strategy(df)
    volatile_sigs = volatile_breakout_strategy(df)
    
    # Combine signals based on states
    # Note: states might be shorter due to feature engineering
    for i, state in enumerate(states):
        timestamp = df.index[len(df) - len(states) + i]
        if state == 0:
            signals.loc[timestamp] = ranging_sigs.loc[timestamp]
        elif state == 1:
            signals.loc[timestamp] = trending_sigs.loc[timestamp]
        elif state == 2:
            signals.loc[timestamp] = volatile_sigs.loc[timestamp]
            
    return signals
