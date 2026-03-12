"""
Economic Calendar Filter
Best TF: Any
Usage: Call before entering a trade to check for high-impact events
       Returns True if it is safe to trade (no imminent high-impact news)
Requires: requests
"""

import json
import urllib.request
from datetime import datetime, timezone, timedelta


# Free economic calendar API (no key required)
CALENDAR_URL = "https://nfs.faireconomy.media/ff_calendar_thisweek.json"

HIGH_IMPACT_CURRENCIES = {
    "EURUSD": ["EUR", "USD"],
    "GBPUSD": ["GBP", "USD"],
    "USDJPY": ["USD", "JPY"],
    "USDCHF": ["USD", "CHF"],
    "AUDUSD": ["AUD", "USD"],
    "USDCAD": ["USD", "CAD"],
    "NZDUSD": ["NZD", "USD"],
    "XAUUSD": ["USD"],
    "US30":   ["USD"],
    "BTCUSD": ["USD"],
}


def fetch_calendar() -> list:
    """Fetch ForexFactory weekly calendar. Returns list of events."""
    try:
        req = urllib.request.Request(CALENDAR_URL, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception:
        return []


def is_safe_to_trade(symbol: str,
                     buffer_before_min: int = 30,
                     buffer_after_min: int  = 15,
                     min_impact: str = "High") -> bool:
    """
    Returns True if no high-impact news for the symbol's currencies
    is within the buffer window.

    min_impact: 'High' or 'Medium'
    """
    currencies = HIGH_IMPACT_CURRENCIES.get(symbol, [])
    if not currencies:
        return True

    events   = fetch_calendar()
    now      = datetime.now(timezone.utc)
    impact_levels = {"High"} if min_impact == "High" else {"High", "Medium"}

    for event in events:
        if event.get("impact") not in impact_levels:
            continue
        if event.get("country") not in currencies:
            continue

        try:
            event_time = datetime.fromisoformat(event["date"].replace("Z", "+00:00"))
        except Exception:
            continue

        window_start = event_time - timedelta(minutes=buffer_before_min)
        window_end   = event_time + timedelta(minutes=buffer_after_min)

        if window_start <= now <= window_end:
            return False   # inside news window — do not trade

    return True


def next_high_impact_event(symbol: str) -> dict | None:
    """Returns the next high-impact event dict for the symbol, or None."""
    currencies = HIGH_IMPACT_CURRENCIES.get(symbol, [])
    events     = fetch_calendar()
    now        = datetime.now(timezone.utc)
    upcoming   = []

    for event in events:
        if event.get("impact") != "High":
            continue
        if event.get("country") not in currencies:
            continue
        try:
            event_time = datetime.fromisoformat(event["date"].replace("Z", "+00:00"))
            if event_time > now:
                upcoming.append((event_time, event))
        except Exception:
            continue

    if not upcoming:
        return None
    upcoming.sort(key=lambda x: x[0])
    return upcoming[0][1]
