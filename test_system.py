# =============================================================================
#  test_system.py
#
#  Run this BEFORE going live to verify every component works.
#  Fix any FAIL before running main.py
#
#  Usage:  python test_system.py
# =============================================================================

import sys
import os

print("=" * 55)
print("  Fozzys Regime System - Pre-flight Check")
print("=" * 55)

passed = 0
failed = 0

def ok(msg):
    global passed
    passed += 1
    print(f"  PASS  {msg}")

def fail(msg):
    global failed
    failed += 1
    print(f"  FAIL  {msg}")


# ── 1. Python packages ────────────────────────────────────────────────────────
print("\n[1] Checking Python packages...")
packages = {
    "MetaTrader5": "pip install MetaTrader5",
    "pandas":      "pip install pandas",
    "numpy":       "pip install numpy",
    "hmmlearn":    "pip install hmmlearn",
    "sklearn":     "pip install scikit-learn",
}
for pkg, install_cmd in packages.items():
    try:
        __import__(pkg)
        ok(f"{pkg} installed")
    except ImportError:
        fail(f"{pkg} NOT installed -> run:  {install_cmd}")


# ── 2. Config file ────────────────────────────────────────────────────────────
print("\n[2] Checking config.py...")
try:
    from config import (MT5_LOGIN, MT5_PASSWORD, MT5_SERVER,
                        INSTRUMENTS, SIGNAL_DIR, MAX_DAILY_LOSS_PCT)
    if MT5_LOGIN == 0:
        fail("MT5_LOGIN not set in config.py")
    else:
        ok(f"MT5_LOGIN = {MT5_LOGIN}")

    if not MT5_PASSWORD:
        fail("MT5_PASSWORD not set in config.py")
    else:
        ok("MT5_PASSWORD set")

    if not MT5_SERVER:
        fail("MT5_SERVER not set in config.py")
    else:
        ok(f"MT5_SERVER = {MT5_SERVER}")

    ok(f"Instruments configured: {list(INSTRUMENTS.keys())}")
    ok(f"Signal dir: {SIGNAL_DIR}")
    ok(f"Max daily loss: {MAX_DAILY_LOSS_PCT}%")

except Exception as e:
    fail(f"config.py error: {e}")


# ── 3. Signal directory ───────────────────────────────────────────────────────
print("\n[3] Checking signal directory...")
try:
    os.makedirs(SIGNAL_DIR, exist_ok=True)
    # Try writing a test file
    test_path = os.path.join(SIGNAL_DIR, "test_write.txt")
    with open(test_path, 'w') as f:
        f.write("test")
    os.remove(test_path)
    ok(f"Signal dir writable: {SIGNAL_DIR}")
except Exception as e:
    fail(f"Cannot write to {SIGNAL_DIR}: {e}")
    print(f"         -> Create this folder manually: {SIGNAL_DIR}")


# ── 4. MT5 connection ─────────────────────────────────────────────────────────
print("\n[4] Checking MT5 connection...")
try:
    import MetaTrader5 as mt5
    if not mt5.initialize():
        fail(f"MT5 init failed: {mt5.last_error()}")
        print("         → Is MT5 running on this machine?")
    else:
        if MT5_LOGIN and MT5_PASSWORD and MT5_SERVER:
            if mt5.login(MT5_LOGIN, password=MT5_PASSWORD, server=MT5_SERVER):
                acc = mt5.account_info()
                ok(f"MT5 logged in | Balance: {acc.balance:.2f} {acc.currency}")
            else:
                fail(f"MT5 login failed: {mt5.last_error()}")
                print("         → Check MT5_LOGIN, MT5_PASSWORD, MT5_SERVER in config.py")
        else:
            ok("MT5 connected (no login credentials - using active terminal)")

        # Check each symbol exists
        print("\n[5] Checking symbols on broker...")
        for name, cfg in INSTRUMENTS.items():
            sym = cfg['symbol']
            if mt5.symbol_select(sym, True):
                info = mt5.symbol_info(sym)
                tick = mt5.symbol_info_tick(sym)
                if info and tick:
                    spread = round((tick.ask - tick.bid) / info.point)
                    ok(f"{sym} found | Ask={tick.ask} Spread={spread}pts")
                else:
                    fail(f"{sym} selected but no tick data")
            else:
                fail(f"{sym} NOT found on broker")
                print(f"         -> Check Market Watch in MT5 for exact symbol name")
                print(f"         -> Update 'symbol' in config.py INSTRUMENTS['{name}']")

        mt5.shutdown()

except Exception as e:
    fail(f"MT5 check error: {e}")


# ── 5. HMM test ───────────────────────────────────────────────────────────────
print("\n[6] Testing HMM regime detector...")
try:
    import numpy as np
    import pandas as pd
    from hmmlearn.hmm import GaussianHMM

    # Generate fake OHLCV data
    np.random.seed(42)
    n = 600
    close = 50000 + np.cumsum(np.random.randn(n) * 200)
    df_test = pd.DataFrame({
        'open':   close - np.abs(np.random.randn(n) * 50),
        'high':   close + np.abs(np.random.randn(n) * 150),
        'low':    close - np.abs(np.random.randn(n) * 150),
        'close':  close,
        'volume': np.random.randint(100, 1000, n).astype(float),
    }, index=pd.date_range('2024-01-01', periods=n, freq='h'))

    from regime_detector import RegimeDetector
    det = RegimeDetector("TEST", n_states=3, model_dir="models_test/")
    trained = det.train(df_test)
    if trained:
        result = det.predict(df_test)
        ok(f"HMM trained and predicted | Regime={result['label']} "
           f"Confidence={result['confidence']:.1%}")
    else:
        fail("HMM training failed")

    # Cleanup test model
    import shutil
    if os.path.exists("models_test"):
        shutil.rmtree("models_test")

except Exception as e:
    fail(f"HMM test failed: {e}")


# ── 6. Strategy test ──────────────────────────────────────────────────────────
print("\n[7] Testing signal generators...")
try:
    import numpy as np
    import pandas as pd
    from strategies import supertrend_signal, rsi_divergence_signal

    # Generate trending data for supertrend test
    np.random.seed(1)
    n = 150
    trend = np.linspace(50000, 55000, n)
    noise = np.random.randn(n) * 100
    close = trend + noise
    df_trend = pd.DataFrame({
        'open':   close - 50,
        'high':   close + 200,
        'low':    close - 200,
        'close':  close,
        'volume': np.ones(n) * 500,
    }, index=pd.date_range('2024-01-01', periods=n, freq='h'))

    cfg = {"atr_period":14, "st_multiplier":3.0, "min_rr":2.0}

    sig = supertrend_signal(df_trend, cfg)
    if sig:
        ok(f"Supertrend signal: {sig['reason']} RR=1:{sig['rr']}")
    else:
        ok("Supertrend: no signal on test data (normal)")

    # Divergence test
    cfg2 = {"rsi_period":14, "atr_period":14, "atr_sl_mult":2.0, "min_rr":2.0}
    sig2 = rsi_divergence_signal(df_trend, cfg2)
    ok(f"RSI Divergence: {'signal found' if sig2 else 'no signal (normal)'}")

except Exception as e:
    fail(f"Strategy test failed: {e}")


# ── Summary ───────────────────────────────────────────────────────────────────
print("\n" + "=" * 55)
print(f"  Results: {passed} passed, {failed} failed")
if failed == 0:
    print("  ALL CHECKS PASSED - safe to run main.py")
else:
    print(f"  FIX THE {failed} FAILURES ABOVE BEFORE RUNNING main.py")
print("=" * 55)
