# =============================================================================
#  risk_manager.py
#
#  Handles:
#  - Position sizing (% risk of equity)
#  - Daily loss limit enforcement
#  - Max trades per day
#  - Lot normalisation for broker constraints
# =============================================================================

import logging
import math

logger = logging.getLogger(__name__)


def calc_lots(equity: float, risk_pct: float, sl_dist_usd: float,
              tick_value: float, tick_size: float,
              vol_min: float, vol_step: float, vol_max: float) -> float:
    """
    Calculate lot size based on % equity risk.

    Formula:
        risk_usd   = equity * risk_pct / 100
        sl_ticks   = sl_dist / tick_size
        lots       = risk_usd / (sl_ticks * tick_value)

    Then normalised to broker lot constraints.
    """
    if sl_dist_usd <= 0 or tick_size <= 0 or tick_value <= 0:
        logger.warning("Invalid inputs for lot calc - returning min lot")
        return vol_min

    risk_usd = equity * risk_pct / 100.0
    sl_ticks = sl_dist_usd / tick_size
    raw_lots = risk_usd / (sl_ticks * tick_value)

    # Round down to nearest vol_step
    lots = math.floor(raw_lots / vol_step) * vol_step
    lots = max(vol_min, min(vol_max, lots))
    lots = round(lots, 2)

    logger.info(f"Lot calc | Equity={equity:.2f} Risk={risk_pct}% "
                f"SL_USD={sl_dist_usd:.2f} → {lots} lots "
                f"(risk={risk_usd:.2f})")
    return lots


def check_daily_limits(equity: float, start_equity: float,
                       max_loss_pct: float, trades_today: int,
                       max_trades: int) -> tuple[bool, str]:
    """
    Returns (ok_to_trade, reason_if_not).
    ok_to_trade = True means safe to enter new trade.
    """
    # Daily loss check
    if start_equity > 0:
        loss_pct = (start_equity - equity) / start_equity * 100
        if loss_pct >= max_loss_pct:
            return False, f"Daily loss limit hit: -{loss_pct:.2f}% >= -{max_loss_pct}%"

    # Max trades check
    if max_trades > 0 and trades_today >= max_trades:
        return False, f"Max daily trades reached: {trades_today}/{max_trades}"

    return True, "OK"


def validate_signal(signal: dict, spread_points: int,
                    spread_limit: int, min_rr: float) -> tuple[bool, str]:
    """
    Final gate before sending order.
    Checks spread, RR, and signal completeness.
    """
    if signal is None:
        return False, "No signal"

    required = ['direction', 'entry', 'sl', 'tp', 'sl_dist', 'tp_dist']
    for key in required:
        if key not in signal:
            return False, f"Missing signal field: {key}"

    if signal['sl_dist'] <= 0:
        return False, "SL distance is zero"

    if signal['rr'] < min_rr:
        return False, f"RR {signal['rr']:.2f} < min {min_rr}"

    if spread_points > spread_limit:
        return False, f"Spread {spread_points} > limit {spread_limit}"

    return True, "OK"
