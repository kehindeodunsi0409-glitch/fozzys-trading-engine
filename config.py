# =============================================================================
#  config.py  —  FXMIXED M5 Regime System
#  16 instruments: 7 Majors + 5 Crosses + XAUUSD + US30 + BTCUSD + GBPUSD
# =============================================================================

# --- MT5 Credentials (IC Markets) ---
MT5_LOGIN    = 52786887
MT5_PASSWORD = "YOUR_PASSWORD_HERE" # Update this on your VPS only!
MT5_SERVER   = "ICMarketsSC-Demo"

MT5_PATH = "C:/Program Files/MetaTrader 5 EXNESS/terminal64.exe"

# --- Execution Mode ---
# "MANUAL" = Only writes CSV signals.
# "AUTO"   = Places trades directly on MT5 (No EA needed).
EXECUTION_MODE = "AUTO"

# --- Signal Output ---
# TO FIND THIS PATH IN MT5: Go to File -> Open Data Folder -> MQL5 -> Files
# Copy that path and paste it below!
SIGNAL_DIR = "C:/Users/Fred/AppData/Roaming/MetaQuotes/Terminal/53785E099C927DB68A545C249CDBCE06/MQL5/Files/"

# --- Instruments ---
INSTRUMENTS = {
    "EURUSD": {
        "symbol": "EURUSD", "timeframe": "H1", "magic": 50001,
        "lot_min": 0.01, "lot_step": 0.01, "lot_max": 10.0,
        "spread_limit": 15, "atr_period": 14, "atr_sl_mult": 2.0,
        "atr_cap_usd": 200, "min_rr": 2.0, "risk_pct": 1.0,
    },
    "GBPUSD": {
        "symbol": "GBPUSD", "timeframe": "H1", "magic": 50002,
        "lot_min": 0.01, "lot_step": 0.01, "lot_max": 10.0,
        "spread_limit": 20, "atr_period": 14, "atr_sl_mult": 2.0,
        "atr_cap_usd": 200, "min_rr": 2.0, "risk_pct": 1.0,
    },
    "USDJPY": {
        "symbol": "USDJPY", "timeframe": "H1", "magic": 50003,
        "lot_min": 0.01, "lot_step": 0.01, "lot_max": 10.0,
        "spread_limit": 15, "atr_period": 14, "atr_sl_mult": 2.0,
        "atr_cap_usd": 200, "min_rr": 2.0, "risk_pct": 1.0,
    },
    "USDCHF": {
        "symbol": "USDCHF", "timeframe": "H1", "magic": 50004,
        "lot_min": 0.01, "lot_step": 0.01, "lot_max": 10.0,
        "spread_limit": 15, "atr_period": 14, "atr_sl_mult": 2.0,
        "atr_cap_usd": 200, "min_rr": 2.0, "risk_pct": 1.0,
    },
    "AUDUSD": {
        "symbol": "AUDUSD", "timeframe": "H1", "magic": 50005,
        "lot_min": 0.01, "lot_step": 0.01, "lot_max": 10.0,
        "spread_limit": 15, "atr_period": 14, "atr_sl_mult": 2.0,
        "atr_cap_usd": 200, "min_rr": 2.0, "risk_pct": 1.0,
    },
    "USDCAD": {
        "symbol": "USDCAD", "timeframe": "H1", "magic": 50006,
        "lot_min": 0.01, "lot_step": 0.01, "lot_max": 10.0,
        "spread_limit": 15, "atr_period": 14, "atr_sl_mult": 2.0,
        "atr_cap_usd": 200, "min_rr": 2.0, "risk_pct": 1.0,
    },
    "NZDUSD": {
        "symbol": "NZDUSD", "timeframe": "H1", "magic": 50007,
        "lot_min": 0.01, "lot_step": 0.01, "lot_max": 10.0,
        "spread_limit": 20, "atr_period": 14, "atr_sl_mult": 2.0,
        "atr_cap_usd": 200, "min_rr": 2.0, "risk_pct": 1.0,
    },
    "EURGBP": {
        "symbol": "EURGBP", "timeframe": "H1", "magic": 50008,
        "lot_min": 0.01, "lot_step": 0.01, "lot_max": 10.0,
        "spread_limit": 20, "atr_period": 14, "atr_sl_mult": 2.0,
        "atr_cap_usd": 200, "min_rr": 2.0, "risk_pct": 1.0,
    },
    "EURJPY": {
        "symbol": "EURJPY", "timeframe": "H1", "magic": 50009,
        "lot_min": 0.01, "lot_step": 0.01, "lot_max": 10.0,
        "spread_limit": 20, "atr_period": 14, "atr_sl_mult": 2.0,
        "atr_cap_usd": 200, "min_rr": 2.0, "risk_pct": 1.0,
    },
    "GBPJPY": {
        "symbol": "GBPJPY", "timeframe": "H1", "magic": 50010,
        "lot_min": 0.01, "lot_step": 0.01, "lot_max": 10.0,
        "spread_limit": 25, "atr_period": 14, "atr_sl_mult": 2.0,
        "atr_cap_usd": 200, "min_rr": 2.0, "risk_pct": 1.0,
    },
    "AUDJPY": {
        "symbol": "AUDJPY", "timeframe": "H1", "magic": 50011,
        "lot_min": 0.01, "lot_step": 0.01, "lot_max": 10.0,
        "spread_limit": 20, "atr_period": 14, "atr_sl_mult": 2.0,
        "atr_cap_usd": 200, "min_rr": 2.0, "risk_pct": 1.0,
    },
    "CADJPY": {
        "symbol": "CADJPY", "timeframe": "H1", "magic": 50012,
        "lot_min": 0.01, "lot_step": 0.01, "lot_max": 10.0,
        "spread_limit": 20, "atr_period": 14, "atr_sl_mult": 2.0,
        "atr_cap_usd": 200, "min_rr": 2.0, "risk_pct": 1.0,
    },
    "XAUUSD": {
        "symbol": "XAUUSD", "timeframe": "H1", "magic": 50013,
        "lot_min": 0.01, "lot_step": 0.01, "lot_max": 5.0,
        "spread_limit": 30, "atr_period": 14, "atr_sl_mult": 2.0,
        "atr_cap_usd": 500, "min_rr": 2.0, "risk_pct": 1.0,
    },
    "US30": {
        "symbol": "US30", "timeframe": "H1", "magic": 50014,
        "lot_min": 0.01, "lot_step": 0.01, "lot_max": 5.0,
        "spread_limit": 300, "atr_period": 14, "atr_sl_mult": 2.0,
        "atr_cap_usd": 500, "min_rr": 2.0, "risk_pct": 1.0,
    },
    "BTCUSD": {
        "symbol": "BTCUSD", "timeframe": "H1", "magic": 50015,
        "lot_min": 0.01, "lot_step": 0.01, "lot_max": 1.0,
        "spread_limit": 2000, "atr_period": 14, "atr_sl_mult": 2.0,
        "atr_cap_usd": 500, "min_rr": 2.0, "risk_pct": 1.0,
    },
}

# --- HMM Settings ---
HMM_BARS         = 500
HMM_RETRAIN_DAYS = 7

# --- Regime -> Strategy Mapping ---
REGIME_STRATEGIES = {
    0: "rsi_divergence",
    1: "supertrend",
    2: "liquidity_grab",
}

# --- Risk Controls ---
MAX_DAILY_LOSS_PCT = 3.0
MAX_TRADES_PER_DAY = 4
LOOP_INTERVAL_SEC  = 60
LOG_DIR            = "logs/"
MODEL_DIR          = "models/"
