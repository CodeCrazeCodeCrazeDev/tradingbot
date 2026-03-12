"""
Simple validation test - checks if basic imports work
"""

print("Testing basic imports...")

try:
    import MetaTrader5 as mt5
    print("[OK] MetaTrader5 imported")
except ImportError as e:
    print(f"[FAIL] MetaTrader5 import failed: {e}")

try:
    import pandas as pd
    print("[OK] pandas imported")
except ImportError as e:
    print(f"[FAIL] pandas import failed: {e}")

try:
    import numpy as np
    print("[OK] numpy imported")
except ImportError as e:
    print(f"[FAIL] numpy import failed: {e}")

try:
    import yaml
    print("[OK] yaml imported")
except ImportError as e:
    print(f"[FAIL] yaml import failed: {e}")

try:
    import psutil
    print("[OK] psutil imported")
except ImportError as e:
    print(f"[FAIL] psutil import failed: {e}")
    print("Run: py -m pip install psutil")

print("\nTesting MT5 initialization...")
try:
    if mt5.initialize():
        print("[OK] MT5 initialized successfully")
        account_info = mt5.account_info()
        if account_info:
            print(f"[OK] Account: {account_info.login}")
            print(f"[OK] Balance: ${account_info.balance:.2f}")
        mt5.shutdown()
    else:
        print("[FAIL] MT5 initialization failed")
        print("Make sure MetaTrader5 is installed and running")
except Exception as e:
    print(f"[FAIL] MT5 test error: {e}")

print("\n" + "="*60)
print("Basic validation test complete")
print("="*60)
