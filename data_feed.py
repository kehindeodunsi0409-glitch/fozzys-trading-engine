# =============================================================================
#  data_feed.py  -  Pulls OHLCV from MT5
# =============================================================================

import MetaTrader5 as mt5
import pandas as pd
import numpy as np
from datetime import datetime, timezone, date, timedelta
import logging
import time

logger = logging.getLogger(__name__)

TF_MAP = {
    "M1":  mt5.TIMEFRAME_M1,
    "M5":  mt5.TIMEFRAME_M5,
    "M15": mt5.TIMEFRAME_M15,
    "H1":  mt5.TIMEFRAME_H1,
    "H4":  mt5.TIMEFRAME_H4,
    "D1":  mt5.TIMEFRAME_D1,
}


def connect(login, password, server, mt5_path=None):
    for attempt in range(5):
        mt5.shutdown()
        time.sleep(2)
        kwargs = {}
        if mt5_path:
            kwargs['path'] = mt5_path
        if not mt5.initialize(**kwargs):
            logger.error(f"MT5 init failed (attempt {attempt+1}): {mt5.last_error()}")
            continue
        if login:
            if not mt5.login(login, password=password, server=server):
                logger.error(f"MT5 login failed: {mt5.last_error()}")
                mt5.shutdown()
                continue
        acc = mt5.account_info()
        if acc is None:
            logger.error("MT5 account_info returned None")
            mt5.shutdown()
            continue
        logger.info(f"MT5 connected | {acc.server} | #{acc.login} | "
                    f"Balance: {acc.balance:.2f} {acc.currency}")
        return True
    return False


def disconnect():
    mt5.shutdown()


def get_bars(symbol, timeframe="H1", count=600):
    tf = TF_MAP.get(timeframe, mt5.TIMEFRAME_H1)
    mt5.symbol_select(symbol, True)
    rates = mt5.copy_rates_from_pos(symbol, tf, 0, count)
    if rates is None or len(rates) == 0:
        logger.error(f"No data for {symbol} {timeframe}")
        return pd.DataFrame()
    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s', utc=True)
    df.set_index('time', inplace=True)
    df = df[['open','high','low','close','tick_volume']].rename(
        columns={'tick_volume':'volume'})
    return df.sort_index()


def get_account():
    a = mt5.account_info()
    if a is None:
        return {}
    return {"balance": a.balance, "equity": a.equity,
            "currency": a.currency, "free_margin": a.margin_free}


def get_tick(symbol):
    t = mt5.symbol_info_tick(symbol)
    i = mt5.symbol_info(symbol)
    if t is None or i is None:
        return {}
    return {"bid": t.bid, "ask": t.ask,
            "spread": round((t.ask - t.bid) / i.point),
            "point": i.point, "digits": i.digits,
            "tick_value": i.trade_tick_value,
            "tick_size": i.trade_tick_size,
            "vol_min": i.volume_min,
            "vol_step": i.volume_step,
            "vol_max": i.volume_max}


def open_positions(symbol, magic):
    pos = mt5.positions_get(symbol=symbol)
    if pos is None:
        return []
    return [p for p in pos if p.magic == magic]


def trades_today(symbol, magic):
    start = datetime.combine(date.today(), datetime.min.time()).replace(
        tzinfo=timezone.utc)
    deals = mt5.history_deals_get(start, datetime.now(timezone.utc))
    if deals is None:
        return 0
    return sum(1 for d in deals
               if d.symbol == symbol and d.magic == magic
               and d.entry == mt5.DEAL_ENTRY_IN)


def pnl_today(magic):
    start = datetime.combine(date.today(), datetime.min.time()).replace(
        tzinfo=timezone.utc)
    deals = mt5.history_deals_get(start, datetime.now(timezone.utc))
    if deals is None:
        return 0.0
    return sum(d.profit for d in deals if d.magic == magic)


def send_market_order(symbol: str, direction: int, volume: float,
                      sl: float, tp: float, magic: int, comment: str = ""):
    """
    Sends a market order via MT5 API. 
    direction: 1 (Buy) or -1 (Sell).
    """
    if not mt5.initialize():
        logger.error("MT5 not initialized - cannot send order")
        return None

    price = mt5.symbol_info_tick(symbol).ask if direction == 1 else mt5.symbol_info_tick(symbol).bid
    order_type = mt5.ORDER_TYPE_BUY if direction == 1 else mt5.ORDER_TYPE_SELL

    request = {
        "action":       mt5.TRADE_ACTION_DEAL,
        "symbol":       symbol,
        "volume":       float(volume),
        "type":         order_type,
        "price":        float(price),
        "sl":           float(sl),
        "tp":           float(tp),
        "deviation":    20,
        "magic":        int(magic),
        "comment":      comment,
        "type_time":    mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }

    result = mt5.order_send(request)
    if result is None:
        logger.error(f"order_send returned None for {symbol}")
        return None

    if result.retcode != mt5.TRADE_RETCODE_DONE:
        logger.error(f"Order failed for {symbol}: {result.comment} (retcode={result.retcode})")
    else:
        logger.info(f"Order EXECUTED for {symbol}: {result.comment} | Ticket={result.order}")

    return result
