# 📖 Fozzy's Regime System - Setup Guide

This is the professional-grade version of your HMM system, integrated directly with MetaTrader 5 (MT5).

## Step 1: Navigate to the Project Folder
Open your terminal (Command Prompt) and move to the folder where the files are located:
```bash
cd "c:\Users\Fred\pythonmachine learn trader"
```

## Step 2: Install Requirements
Run this command to install all the necessary tools:
```bash
python -m pip install -r requirements.txt
```
*Note: This includes `MetaTrader5`, `hmmlearn`, and `scikit-learn`.*

## Step 2: Configure MT5
1. Open **config.py**.
2. Enter your MT5 login, password, and server:
   ```python
   MT5_LOGIN    = 12345678
   MT5_PASSWORD = "your_password"
   MT5_SERVER   = "ICMarkets-Demo"
   ```
3. Ensure MetaTrader 5 is running on your computer.

## Step 3: Run the Pre-Flight Check
Before going live, run the test script to make sure everything (connection, AI model, strategies) works:
```bash
python test_system.py
```
*If anything says **FAIL**, follow the instructions in the terminal to fix it.*

## Step 5: Enable Auto-Trading (Optional)
By default, the system only writes signals to a CSV file. To make it trade **automatically**:
1. Open **config.py**.
2. Find `EXECUTION_MODE`.
3. Change it to `"AUTO"`:
   ```python
   EXECUTION_MODE = "AUTO"
   ```
4. Restart `main.py`. The system will now place trades directly on your MT5 account whenever a signal is found.

> [!IMPORTANT]
> **YOU MUST** click the **"Algo Trading"** button at the top of your MetaTrader 5 terminal. If it is red, the system cannot place trades! It must be green.

---

---

## ☁️ Running on a VPS (24/7 Trading)

To keep your system running 24/7 without your home PC being on, you can move it to a VPS.

### 1. Prepare your VPS
1. Log in to your Windows VPS via Remote Desktop.
2. Install **Python 3.10+** (Make sure to check "Add Python to PATH" during installation).
3. Install **MetaTrader 5** on the VPS and log in to your account.
4. **IMPORTANT**: Open MT5 and click the **"Algo Trading"** button so it's GREEN. 🟢

### 2. Transfer the Files
Copy the following files/folders from your local PC to your VPS folder (e.g., `Documents\TradingBot`):
- All `.py` files (`main.py`, `config.py`, etc.)
- `requirements.txt`
- `models/` folder (to keep your trained AI)

### 3. Final VPS Setup
1. Open the VPS terminal (CMD) and `cd` to your bot folder.
2. Run `python -m pip install -r requirements.txt`.
3. Open **config.py** on the VPS and update `MT5_PATH` if the MT5 installation folder is different (use `test_system.py` to find the correct path if it fails).
4. Run `python main.py` and leave the terminal open!

### 📂 File Guide
- **main.py**: The heart of the system. Runs the live loop.
- **test_system.py**: Your safety check. Run this first!
- **config.py**: Where you change settings and symbols.
- **regime_detector.py**: The HMM "Brain" that finds market moods.
- **strategies.py**: Divergence, Supertrend, and Liquidity Grab logics.
- **risk_manager.py**: Protects your account from big losses.
