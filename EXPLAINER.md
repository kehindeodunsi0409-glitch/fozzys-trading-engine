# 📈 Beginner's Guide to HMM Trading

Welcome! This guide explains how our automated trading system works in plain English. No PhD in Math required!

## 1. What is a "Hidden Markov Model" (HMM)?
Imagine you are looking at a person through a blurry window. You can't see exactly what they are doing, but you see their **movements** (the prices). 
- The **Hidden** part: We can't see the "true" state of the market directly (is it actually trending or just ranging?).
- The **Markov** part: We assume the market's state tomorrow depends mostly on its state today.

## 2. The Three Market Regimes
Our AI classifies the market into three "moods":

| Regime | Description | What the AI sees | Strategy |
| :--- | :--- | :--- | :--- |
| **Ranging** | Price bounces between two levels. | Low volatility, no clear direction. | **Mean Reversion**: Buy low, sell high. |
| **Trending** | Price is moving strongly up or down. | High momentum, consistent direction. | **Trend Following**: Ride the wave. |
| **Volatile** | Price is jumping around crazily. | Extreme price swings, high risk. | **Breakout**: Wait for a clear exit, tight stops. |

## 3. Why is this better than typical AI?
Most AI (like XGBoost) needs someone to "label" the data first (e.g., "This was a good trade"). 
Our HMM is **Unsupervised**. It looks at the patterns of returns and volatility and says, *"I've seen this pattern before, it looks like a 'Type A' market,"* without us telling it anything!

## 4. How to use this system
1.  **Data Loading**: We fetch prices from the internet (Yahoo Finance).
2.  **Feature Prep**: we calculate things like "Daily Returns" and "Range".
3.  **HMM Training**: The AI learns the three regimes from the data.
4.  **Strategy execution**: For every new price, the AI picks the best strategy based on the current regime.

---
*Note: Trading involves risk. Even the smartest AI can't predict the future 100% of the time!*
