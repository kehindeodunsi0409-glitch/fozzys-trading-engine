"""
COT Positioning Strategy
Best TF: D1 bias (weekly signal)
Signal: CFTC COT large speculator net positioning
        Net long > threshold = bullish, net short = bearish
This is a standalone version — see bias_engine.py for the full TREND_PY integration.
"""

import urllib.request
import pandas as pd
import numpy as np


COT_URL = "https://www.cftc.gov/dea/newcot/c_disagg.txt"

# CFTC contract codes
COT_CODES = {
    "EURUSD": "099741",
    "GBPUSD": "096742",
    "USDJPY": "097741",
    "AUDUSD": "232741",
    "NZDUSD": "112741",
    "USDCAD": "090741",
    "USDCHF": "092741",
    "XAUUSD": "088691",
    "DXY":    "098662",
}


def fetch_cot() -> dict:
    """
    Fetch COT disaggregated report.
    Returns dict keyed by code: {ls_long, ls_short, net, net_pct}

    Column layout (0-indexed, comma-delimited):
      parts[3]  = CFTC Contract Market Code
      parts[17] = Leveraged Money Longs
      parts[18] = Leveraged Money Shorts
    """
    result = {}
    req = urllib.request.Request(COT_URL, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        lines = resp.read().decode("utf-8", errors="ignore").splitlines()

    for line in lines[1:]:
        parts = line.split(",")
        if len(parts) < 20:
            continue
        try:
            code     = parts[3].strip().strip('"')
            ls_long  = int(parts[17].strip().replace('"', ''))
            ls_short = int(parts[18].strip().replace('"', ''))
            total    = ls_long + ls_short
            net      = ls_long - ls_short
            net_pct  = net / total if total > 0 else 0
            result[code] = {"ls_long": ls_long, "ls_short": ls_short,
                            "net": net, "net_pct": net_pct}
        except (ValueError, IndexError):
            continue

    return result


def get_signal(symbol: str, neutral_band: float = 0.05,
               usd_base: bool = False) -> int:
    """
    symbol: one of the keys in COT_CODES
    neutral_band: ignore positions with |net_pct| < this value
    usd_base: True for USDJPY/USDCHF etc (inverts signal)
    Returns: 1=long, -1=short, 0=neutral
    """
    code = COT_CODES.get(symbol)
    if not code:
        return 0

    cot = fetch_cot()
    if code not in cot:
        return 0

    net_pct = cot[code]["net_pct"]
    if abs(net_pct) < neutral_band:
        return 0

    raw = 1 if net_pct > 0 else -1
    return -raw if usd_base else raw
