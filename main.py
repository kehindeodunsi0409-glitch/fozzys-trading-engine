# =============================================================================
#  main.py  -  Fozzys Regime System
# =============================================================================

import time
import logging
import os
import sys
from datetime import datetime, timezone, date

from config import (
    MT5_LOGIN, MT5_PASSWORD, MT5_SERVER,
    INSTRUMENTS, SIGNAL_DIR, LOG_DIR, MODEL_DIR,
    HMM_BARS, HMM_RETRAIN_DAYS,
    MAX_DAILY_LOSS_PCT, MAX_TRADES_PER_DAY,
    LOOP_INTERVAL_SEC, EXECUTION_MODE,
)

# MT5_PATH is optional - only needed when running multiple terminals
try:
    from config import MT5_PATH
except ImportError:
    MT5_PATH = None

import data_feed   as df_mod
import strategies  as strat
import risk_manager as rm
import signal_writer as sw
from regime_detector import RegimeDetector


# ── Logging setup ─────────────────────────────────────────────────────────────

os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(MODEL_DIR, exist_ok=True)

log_file = os.path.join(LOG_DIR,
    f"regime_{datetime.utcnow().strftime('%Y%m%d')}.log")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout),
    ]
)
logger = logging.getLogger("main")


# ── Per-instrument state ──────────────────────────────────────────────────────

class InstrumentState:
    def __init__(self, symbol):
        self.symbol        = symbol
        self.detector      = RegimeDetector(symbol, n_states=3,
                                            model_dir=MODEL_DIR)
        self.day_start_eq  = None
        self.current_day   = None
        self.last_run_hour = None

    def reset_day_if_needed(self, equity):
        today = date.today()
        if self.current_day != today:
            self.current_day  = today
            self.day_start_eq = equity
            logger.info(f"[{self.symbol}] New day. Start equity={equity:.2f}")


# ── Main loop ─────────────────────────────────────────────────────────────────

def run_instrument(name: str, cfg: dict, state: InstrumentState):
    symbol = cfg['symbol']
    magic  = cfg['magic']

    timeframe = cfg.get("timeframe", "H1")
    bars = df_mod.get_bars(symbol, timeframe=timeframe, count=HMM_BARS + 50)
    if bars.empty:
        logger.error(f"[{symbol}] No bars - skipping")
        return

    account = df_mod.get_account()
    equity  = account.get('equity', 0)
    if equity <= 0:
        logger.error(f"[{symbol}] Bad equity reading")
        return

    state.reset_day_if_needed(equity)

    trades_td = df_mod.trades_today(symbol, magic)
    ok, reason = rm.check_daily_limits(
        equity, state.day_start_eq or equity,
        MAX_DAILY_LOSS_PCT, trades_td, MAX_TRADES_PER_DAY)
    if not ok:
        logger.info(f"[{symbol}] Trading halted: {reason}")
        sw.write_status(SIGNAL_DIR, symbol, "Halted", "none", 0, reason)
        return

    open_pos = df_mod.open_positions(symbol, magic)
    if open_pos:
        logger.info(f"[{symbol}] Position open ({len(open_pos)}) - skipping signal gen")
        return

    if state.detector.model is None:
        loaded = state.detector.load()
        if not loaded or state.detector.needs_retrain(HMM_RETRAIN_DAYS):
            state.detector.train(bars.tail(HMM_BARS))

    if state.detector.needs_retrain(HMM_RETRAIN_DAYS):
        state.detector.train(bars.tail(HMM_BARS))

    regime_info = state.detector.predict(bars.tail(HMM_BARS))
    regime      = regime_info['label']
    strategy    = regime_info['strategy']
    confidence  = regime_info['confidence']

    logger.info(f"[{symbol}] Regime={regime} | Strategy={strategy} | "
                f"Confidence={confidence:.2%}")

    sw.write_status(SIGNAL_DIR, symbol, regime, strategy, confidence)

    if strategy == "sit_out":
        sw.clear_signal(SIGNAL_DIR, symbol)
        return

    signal = strat.get_signal(bars, strategy, cfg)
    if signal is None:
        logger.info(f"[{symbol}] No setup found this bar")
        sw.clear_signal(SIGNAL_DIR, symbol)
        return

    tick = df_mod.get_tick(symbol)
    spread = tick.get('spread', 0)
    ok, reason = rm.validate_signal(
        signal, spread, cfg['spread_limit'], cfg['min_rr'])
    if not ok:
        logger.info(f"[{symbol}] Signal rejected: {reason}")
        sw.clear_signal(SIGNAL_DIR, symbol)
        return

    sl_dist_price = signal['sl_dist']
    tick_val  = tick.get('tick_value', 1.0)
    tick_size = tick.get('tick_size', 1.0)

    lots = rm.calc_lots(
        equity      = equity,
        risk_pct    = cfg['risk_pct'],
        sl_dist_usd = sl_dist_price,
        tick_value  = tick_val,
        tick_size   = tick_size,
        vol_min     = cfg['lot_min'],
        vol_step    = cfg['lot_step'],
        vol_max     = cfg['lot_max'],
    )

    sw.write_signal(SIGNAL_DIR, symbol, magic, signal, lots, regime)
    logger.info(f"[{symbol}] Signal ready | "
                f"{'BUY' if signal['direction']==1 else 'SELL'} {lots} lots | "
                f"RR=1:{signal['rr']}")

    if EXECUTION_MODE == "AUTO":
        logger.info(f"[{symbol}] AUTO-EXECUTE enabled. Sending order...")
        df_mod.send_market_order(
            symbol    = symbol,
            direction = signal['direction'],
            volume    = lots,
            sl        = signal['sl'],
            tp        = signal['tp'],
            magic     = magic,
            comment   = f"HMM_{regime}_{strategy}"
        )


def main():
    logger.info("=" * 60)
    logger.info("  Fozzys Regime System starting")
    logger.info(f"  Instruments: {list(INSTRUMENTS.keys())}")
    logger.info(f"  Signal dir:  {SIGNAL_DIR}")
    for n,c in INSTRUMENTS.items():
        logger.info(f"  {n}: timeframe={c.get('timeframe','H1')}")
    logger.info("=" * 60)

    if not df_mod.connect(MT5_LOGIN, MT5_PASSWORD, MT5_SERVER, MT5_PATH):
        logger.error("Cannot connect to MT5 - check config.py credentials")
        sys.exit(1)

    states = {name: InstrumentState(name) for name in INSTRUMENTS}

    try:
        while True:
            cycle_start = datetime.utcnow()
            logger.info(f"--- Cycle {cycle_start.strftime('%Y-%m-%d %H:%M:%S')} UTC ---")

            for name, cfg in INSTRUMENTS.items():
                try:
                    run_instrument(name, cfg, states[name])
                except Exception as e:
                    logger.error(f"[{name}] Unhandled error: {e}", exc_info=True)

            elapsed = (datetime.utcnow() - cycle_start).total_seconds()
            sleep_s = max(10, LOOP_INTERVAL_SEC - elapsed)
            logger.info(f"Cycle done in {elapsed:.1f}s. Next run in {sleep_s:.0f}s.")
            time.sleep(sleep_s)

    except KeyboardInterrupt:
        logger.info("Shutdown requested")
    finally:
        df_mod.disconnect()
        logger.info("Fozzys Regime System stopped cleanly")


if __name__ == "__main__":
    main()
