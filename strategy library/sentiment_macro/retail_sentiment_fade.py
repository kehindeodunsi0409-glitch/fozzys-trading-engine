"""
Retail Sentiment Fade Strategy
Best TF: H1/H4
Signal: Fade extreme retail positioning (OANDA/myfxbook)
        >65% retail long = short signal (fade the crowd)
        <35% retail long = long signal
"""

import json
import urllib.request


OANDA_URL = "https://www.oanda.com/cfds-trading/en-gb/sentiment/data/"

SYMBOL_MAP = {
    "EURUSD": "eur_usd", "GBPUSD": "gbp_usd", "USDJPY": "usd_jpy",
    "USDCHF": "usd_chf", "AUDUSD": "aud_usd", "USDCAD": "usd_cad",
    "NZDUSD": "nzd_usd", "XAUUSD": "xau_usd",
}


def fetch_oanda_sentiment(symbol: str) -> float:
    """Returns long ratio 0.0–1.0, or 0.5 on failure."""
    oanda_sym = SYMBOL_MAP.get(symbol)
    if not oanda_sym:
        return 0.5
    try:
        url = f"{OANDA_URL}?instrument={oanda_sym}"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return float(data.get("longPositionRatio", 0.5))
    except Exception:
        return 0.5


def get_signal(symbol: str,
               long_threshold: float = 0.65,
               short_threshold: float = 0.35) -> int:
    """
    Returns fade signal:
      1  = retail crowd is very short -> go long
     -1  = retail crowd is very long  -> go short
      0  = no extreme positioning
    """
    ratio = fetch_oanda_sentiment(symbol)
    if ratio >= long_threshold:
        return -1   # crowd is long -> fade -> short
    elif ratio <= short_threshold:
        return 1    # crowd is short -> fade -> long
    return 0
