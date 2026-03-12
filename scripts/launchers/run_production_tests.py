"""
Production Testing Suite

Runs all production-readiness tests before live deployment.
"""

import asyncio
import sys
import logging
from pathlib import Path
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'logs/production_tests_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


async def run_production_tests():
    """Run complete production test suite"""
    
    print("=" * 80)
    print("ELITE TRADING BOT - PRODUCTION READINESS TESTS")
    print("=" * 80)
    print(f"Start Time: {datetime.now().isoformat()}")
    print("=" * 80)
    print()
    
    results = {
        'timestamp': datetime.now().isoformat(),
        'tests': {},
        'overall_status': 'PASS'
    }
    
    # Test 1: Broker Connection
    print("\n" + "=" * 80)
    print("TEST 1: BROKER CONNECTION")
    print("=" * 80)
    
    try:
        from tests.test_broker_connection import test_broker_connection
        
        broker_config = {
            'login': 12345678,  # Replace with your login
            'password': 'your_password',  # Replace with your password
            'server': 'YourBroker-Demo'  # Replace with your server
        }
        
        broker_results = await test_broker_connection(broker_config)
        results['tests']['broker_connection'] = broker_results
        
        if broker_results['overall_status'] != 'PASS':
            results['overall_status'] = 'FAIL'
            print("\n❌ Broker connection test FAILED - cannot proceed")
            return results
        
        print("\n✅ Broker connection test PASSED")
        
    except Exception as e:
        logger.error(f"Broker connection test failed: {e}")
        results['tests']['broker_connection'] = {'error': str(e), 'passed': False}
        results['overall_status'] = 'FAIL'
        return results
    
    # Test 2: Order Confirmation System
    print("\n" + "=" * 80)
    print("TEST 2: ORDER CONFIRMATION SYSTEM")
    print("=" * 80)
    
    try:
        from trading_bot.execution.order_confirmation import OrderConfirmationSystem
        from trading_bot.brokers.mt5_adapter import MT5BrokerAdapter
        
        broker = MT5BrokerAdapter(broker_config)
        confirmation_system = OrderConfirmationSystem(broker, {
            'confirmation_timeout': 30,
            'max_retries': 3
        })
        
        # Test order with confirmation
        order = await confirmation_system.place_order_with_confirmation(
            symbol='EURUSD',
            order_type='buy',
            volume=0.01,
            comment='confirmation_test'
        )
        
        if order:
            print(f"✅ Order confirmed: {order.get('order_id')}")
            
            # Close test order
            await broker.close_position(order.get('order_id'))
            print("✅ Test order closed")
            
            results['tests']['order_confirmation'] = {'passed': True}
        else:
            print("❌ Order confirmation failed")
            results['tests']['order_confirmation'] = {'passed': False}
            results['overall_status'] = 'FAIL'
        
        broker.shutdown()
        
    except Exception as e:
        logger.error(f"Order confirmation test failed: {e}")
        results['tests']['order_confirmation'] = {'error': str(e), 'passed': False}
        results['overall_status'] = 'FAIL'
    
    # Test 3: Slippage Protection
    print("\n" + "=" * 80)
    print("TEST 3: SLIPPAGE PROTECTION")
    print("=" * 80)
    
    try:
        from trading_bot.execution.slippage_protection import SlippageProtection
        from trading_bot.brokers.mt5_adapter import MT5BrokerAdapter
        
        broker = MT5BrokerAdapter(broker_config)
        slippage_protection = SlippageProtection({
            'max_slippage_bps': 50
        })
        
        # Get current price
        symbol_info = await broker.get_symbol_info('EURUSD')
        expected_price = symbol_info['ask']
        
        # Execute with slippage protection
        order = await slippage_protection.execute_with_protection(
            broker=broker,
            symbol='EURUSD',
            order_type='buy',
            volume=0.01,
            expected_price=expected_price,
            comment='slippage_test'
        )
        
        if order:
            stats = slippage_protection.get_slippage_stats()
            print(f"✅ Slippage protection working")
            print(f"   Avg slippage: {stats['avg_slippage_bps']:.2f} bps")
            
            # Close test order
            await broker.close_position(order.get('order_id'))
            
            results['tests']['slippage_protection'] = {
                'passed': True,
                'stats': stats
            }
        else:
            print("❌ Slippage protection test failed")
            results['tests']['slippage_protection'] = {'passed': False}
            results['overall_status'] = 'FAIL'
        
        broker.shutdown()
        
    except Exception as e:
        logger.error(f"Slippage protection test failed: {e}")
        results['tests']['slippage_protection'] = {'error': str(e), 'passed': False}
        results['overall_status'] = 'FAIL'
    
    # Test 4: Position Size Calculator
    print("\n" + "=" * 80)
    print("TEST 4: POSITION SIZE CALCULATOR")
    print("=" * 80)
    
    try:
        from trading_bot.risk.position_size_calculator import PositionSizeCalculator, PositionSizeMethod
        
        calculator = PositionSizeCalculator({
            'default_risk_pct': 0.01,
            'min_position_size': 0.01,
            'max_position_size': 10.0
        })
        
        # Test different methods
        account_equity = 10000
        
        # Fixed risk
        size1 = calculator.calculate_position_size(
            symbol='EURUSD',
            account_equity=account_equity,
            risk_pct=0.01,
            stop_loss_pips=50,
            method=PositionSizeMethod.FIXED_RISK
        )
        
        # Kelly criterion
        size2 = calculator.calculate_position_size(
            symbol='EURUSD',
            account_equity=account_equity,
            risk_pct=0.01,
            method=PositionSizeMethod.KELLY_CRITERION
        )
        
        print(f"✅ Position size calculator working")
        print(f"   Fixed risk: {size1:.2f} lots")
        print(f"   Kelly: {size2:.2f} lots")
        
        results['tests']['position_calculator'] = {
            'passed': True,
            'fixed_risk_size': size1,
            'kelly_size': size2
        }
        
    except Exception as e:
        logger.error(f"Position calculator test failed: {e}")
        results['tests']['position_calculator'] = {'error': str(e), 'passed': False}
        results['overall_status'] = 'FAIL'
    
    # Test 5: Load Testing (Optional - takes time)
    print("\n" + "=" * 80)
    print("TEST 5: LOAD TESTING (Quick)")
    print("=" * 80)
    
    try:
        from tests.test_load_testing import LoadTestSuite
        from trading_bot.core.execution_manager import ExecutionManager
        from trading_bot.data.market_data_stream import MarketDataStream
        
        execution = ExecutionManager({})
        data_stream = MarketDataStream({})
        
        load_tester = LoadTestSuite(execution, data_stream)
        
        # Run quick tests
        print("Running high-frequency test (100 orders)...")
        hf_result = await load_tester.test_high_frequency_orders(count=100)
        
        print(f"✅ Load testing complete")
        print(f"   Orders/sec: {hf_result['orders_per_second']:.2f}")
        
        results['tests']['load_testing'] = {
            'passed': True,
            'orders_per_second': hf_result['orders_per_second']
        }
        
    except Exception as e:
        logger.error(f"Load testing failed: {e}")
        results['tests']['load_testing'] = {'error': str(e), 'passed': False}
        # Don't fail overall for load testing
    
    # Generate Final Report
    print("\n" + "=" * 80)
    print("PRODUCTION READINESS REPORT")
    print("=" * 80)
    
    passed_tests = sum(1 for t in results['tests'].values() if t.get('passed', False))
    total_tests = len(results['tests'])
    
    print(f"\nTests Passed: {passed_tests}/{total_tests}")
    print(f"Overall Status: {results['overall_status']}")
    
    print("\nTest Results:")
    for test_name, test_result in results['tests'].items():
        status = "✅ PASS" if test_result.get('passed') else "❌ FAIL"
        print(f"  {test_name}: {status}")
        if 'error' in test_result:
            print(f"    Error: {test_result['error']}")
    
    print("\n" + "=" * 80)
    
    if results['overall_status'] == 'PASS':
        print("✅ SYSTEM IS READY FOR PRODUCTION")
        print("\nNext Steps:")
        print("  1. Review test logs")
        print("  2. Configure production settings")
        print("  3. Start with paper trading")
        print("  4. Monitor for 1 week")
        print("  5. Gradually increase position sizes")
    else:
        print("❌ SYSTEM IS NOT READY FOR PRODUCTION")
        print("\nRequired Actions:")
        print("  1. Fix failed tests")
        print("  2. Re-run production tests")
        print("  3. Do not proceed to live trading")
    
    print("=" * 80)
    
    # Save results
    import json
    results_file = Path('logs') / f'production_test_results_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nResults saved to: {results_file}")
    
    return results


if __name__ == "__main__":
    # Create logs directory
    Path('logs').mkdir(exist_ok=True)
    
    try:
        results = asyncio.run(run_production_tests())
        
        # Exit with appropriate code
        sys.exit(0 if results['overall_status'] == 'PASS' else 1)
        
    except KeyboardInterrupt:
        print("\n\nTests interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)
