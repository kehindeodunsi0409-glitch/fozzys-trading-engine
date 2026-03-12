# =============================================================================
#  signal_writer.py
# =============================================================================

import os
import csv
import logging
from datetime import datetime, timezone, timedelta

logger = logging.getLogger(__name__)

# VPS is UTC+2, MT5 uses local time for TimeCurrent()
VPS_UTC_OFFSET = 2


def write_signal(signal_dir: str, symbol: str, magic: int,
                 signal: dict, lots: float, regime: str):
    os.makedirs(signal_dir, exist_ok=True)
    path = os.path.join(signal_dir, f"{symbol}_signal.csv")

    direction_str = "BUY" if signal['direction'] == 1 else "SELL"
    timestamp = (datetime.now(timezone.utc) + timedelta(hours=VPS_UTC_OFFSET)).strftime("%Y.%m.%d %H:%M")

    row = {
        "symbol":    symbol,
        "direction": direction_str,
        "entry":     signal['entry'],
        "sl":        signal['sl'],
        "tp":        signal['tp'],
        "lots":      lots,
        "magic":     magic,
        "timestamp": timestamp,
        "strategy":  signal.get('strategy', 'unknown'),
        "regime":    regime,
        "rr":        signal.get('rr', 0),
        "reason":    signal.get('reason', ''),
    }

    with open(path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=row.keys())
        writer.writeheader()
        writer.writerow(row)

    logger.info(f"Signal written -> {path} | {direction_str} {lots} lots | "
                f"Entry={signal['entry']} SL={signal['sl']} TP={signal['tp']} | "
                f"Regime={regime} Strategy={signal.get('strategy','unknown')}")


def clear_signal(signal_dir: str, symbol: str):
    path = os.path.join(signal_dir, f"{symbol}_signal.csv")
    if os.path.exists(path):
        os.remove(path)
        logger.debug(f"Signal cleared for {symbol}")


def write_status(signal_dir: str, symbol: str, regime: str,
                 strategy: str, confidence: float, reason: str = ""):
    os.makedirs(signal_dir, exist_ok=True)
    path = os.path.join(signal_dir, f"{symbol}_status.csv")
    timestamp = (datetime.now(timezone.utc) + timedelta(hours=VPS_UTC_OFFSET)).strftime("%Y.%m.%d %H:%M:%S")

    row = {
        "symbol":     symbol,
        "regime":     regime,
        "strategy":   strategy,
        "confidence": confidence,
        "reason":     reason,
        "timestamp":  timestamp,
    }

    with open(path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=row.keys())
        writer.writeheader()
        writer.writerow(row)
