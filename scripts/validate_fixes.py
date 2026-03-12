"""
Validate all fixes made to the trading bot.
"""

import sys
sys.path.insert(0, '.')

def main():
    print('=' * 80)
    print('COMPREHENSIVE FIX VALIDATION')
    print('=' * 80)

    results = []

    # 1. Core Safety Modules
    print('\n[1] CORE SAFETY MODULES')
    print('-' * 40)

    try:
        from trading_bot.core.fail_safe import FailSafe, TradingMode, SystemHealth
        fs = FailSafe()
        results.append(('FailSafe', 'PASS', f'Mode={fs.trading_mode.name}'))
        print('   FailSafe: PASS')
    except Exception as e:
        results.append(('FailSafe', 'FAIL', str(e)))
        print(f'   FailSafe: FAIL - {e}')

    try:
        from trading_bot.core.circuit_breaker import CircuitBreaker, CircuitBreakerManager
        cb = CircuitBreaker('test')
        results.append(('CircuitBreaker', 'PASS', f'State={cb.state.name}'))
        print('   CircuitBreaker: PASS')
    except Exception as e:
        results.append(('CircuitBreaker', 'FAIL', str(e)))
        print(f'   CircuitBreaker: FAIL - {e}')

    try:
        from trading_bot.core.emergency_kill_switch import EmergencyKillSwitch, EmergencyLevel
        ks = EmergencyKillSwitch()
        results.append(('EmergencyKillSwitch', 'PASS', f'Level={ks.level.name}'))
        print('   EmergencyKillSwitch: PASS')
    except Exception as e:
        results.append(('EmergencyKillSwitch', 'FAIL', str(e)))
        print(f'   EmergencyKillSwitch: FAIL - {e}')

    # 2. Execution Modules
    print('\n[2] EXECUTION MODULES')
    print('-' * 40)

    try:
        from trading_bot.execution.order_manager import OrderManager, OrderType, OrderSide
        om = OrderManager()
        order = om.create_order('EURUSD', OrderSide.BUY, 0.1, OrderType.MARKET)
        results.append(('OrderManager', 'PASS', 'Order created'))
        print('   OrderManager: PASS')
    except Exception as e:
        results.append(('OrderManager', 'FAIL', str(e)))
        print(f'   OrderManager: FAIL - {e}')

    # 3. Broker Adapters
    print('\n[3] BROKER ADAPTERS')
    print('-' * 40)

    try:
        from trading_bot.brokers.broker_adapter import (
            MT5BrokerAdapter, AlpacaBrokerAdapter, BinanceBrokerAdapter, 
            MockBrokerAdapter, get_broker_adapter
        )
        
        # Test factory function
        mock = get_broker_adapter('mock')
        mt5 = get_broker_adapter('mt5')
        alpaca = get_broker_adapter('alpaca')
        binance = get_broker_adapter('binance')
        
        results.append(('BrokerAdapters', 'PASS', '4 adapters available'))
        print('   MT5BrokerAdapter: PASS')
        print('   AlpacaBrokerAdapter: PASS')
        print('   BinanceBrokerAdapter: PASS')
        print('   MockBrokerAdapter: PASS')
        print('   get_broker_adapter(): PASS')
    except Exception as e:
        results.append(('BrokerAdapters', 'FAIL', str(e)))
        print(f'   BrokerAdapters: FAIL - {e}')

    # 4. Security Modules
    print('\n[4] SECURITY MODULES')
    print('-' * 40)

    try:
        from trading_bot.security.vault import SecureVault, create_vault
        vault = create_vault()
        vault.initialize('test_password')
        vault.store('TEST_KEY', 'test_value')
        retrieved = vault.retrieve('TEST_KEY')
        status = vault.get_status()
        enc_type = status.get('encryption', 'Unknown')
        results.append(('SecureVault', 'PASS', enc_type))
        print(f'   SecureVault: PASS ({enc_type})')
    except Exception as e:
        results.append(('SecureVault', 'FAIL', str(e)))
        print(f'   SecureVault: FAIL - {e}')

    # 5. Configuration
    print('\n[5] CONFIGURATION')
    print('-' * 40)

    try:
        from trading_bot.config.constants import (
            MAX_RISK_PER_TRADE, MAX_DAILY_LOSS, MAX_DRAWDOWN,
            DEFAULT_TIMEOUT, KILL_SWITCH_FILES, get_limit, get_timeout
        )
        results.append(('Constants', 'PASS', f'MAX_RISK={MAX_RISK_PER_TRADE}'))
        print('   Constants: PASS')
        print(f'   - MAX_RISK_PER_TRADE: {MAX_RISK_PER_TRADE}')
        print(f'   - MAX_DAILY_LOSS: {MAX_DAILY_LOSS}')
        print(f'   - MAX_DRAWDOWN: {MAX_DRAWDOWN}')
    except Exception as e:
        results.append(('Constants', 'FAIL', str(e)))
        print(f'   Constants: FAIL - {e}')

    # 6. Risk Module Integration
    print('\n[6] RISK MODULE INTEGRATION')
    print('-' * 40)

    try:
        from trading_bot.risk import EmergencyKillSwitch, get_kill_switch
        ks = get_kill_switch()
        results.append(('RiskKillSwitch', 'PASS', 'Accessible from risk module'))
        print('   Kill switch in risk module: PASS')
    except Exception as e:
        results.append(('RiskKillSwitch', 'FAIL', str(e)))
        print(f'   Kill switch in risk module: FAIL - {e}')

    # Summary
    print('\n' + '=' * 80)
    print('VALIDATION SUMMARY')
    print('=' * 80)

    passed = sum(1 for r in results if r[1] == 'PASS')
    failed = sum(1 for r in results if r[1] == 'FAIL')

    print(f'\nTotal Tests: {len(results)}')
    print(f'Passed: {passed}')
    print(f'Failed: {failed}')
    
    if failed == 0:
        print('\nStatus: ALL TESTS PASSED')
    else:
        print('\nStatus: SOME TESTS FAILED')
        print('\nFailed Tests:')
        for name, status, detail in results:
            if status == 'FAIL':
                print(f'  - {name}: {detail}')

    print('=' * 80)
    
    return 0 if failed == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
