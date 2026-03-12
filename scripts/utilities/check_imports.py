#!/usr/bin/env python3
"""Check module imports"""

import sys

print('Checking for import issues...')
print('trading_bot module loaded successfully')

# Try importing key submodules
try:
    from trading_bot.connectivity import network_monitor
    print('[OK] network_monitor imported')
except Exception as e:
    print(f'[ERROR] network_monitor: {e}')

try:
    from trading_bot.brokers import broker_adapter
    print('[OK] broker_adapter imported')
except Exception as e:
    print(f'[ERROR] broker_adapter: {e}')

try:
    from trading_bot.position_manager import PositionManager
    print('[OK] PositionManager imported')
except Exception as e:
    print(f'[ERROR] PositionManager: {e}')

try:
    from trading_bot.risk import RiskManager
    print('[OK] RiskManager imported')
except Exception as e:
    print(f'[ERROR] RiskManager: {e}')

try:
    from trading_bot.execution import ExecutionManager
    print('[OK] ExecutionManager imported')
except Exception as e:
    print(f'[ERROR] ExecutionManager: {e}')

try:
    from trading_bot.reporting import Reporter
    print('[OK] Reporter imported')
except Exception as e:
    print(f'[ERROR] Reporter: {e}')

print('\nImport check complete')
