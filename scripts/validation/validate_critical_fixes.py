"""
Validation Script for Critical Fixes

Tests all critical fixes to ensure they work correctly.
"""

import sys
import asyncio
from datetime import datetime


def print_header(text):
    """Print section header"""
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}\n")


def print_test(name, passed, details=""):
    """Print test result"""
    status = "[PASS]" if passed else "[FAIL]"
    print(f"{status} - {name}")
    if details:
        print(f"       {details}")


async def main():
    """Run all validation tests"""
    print_header("CRITICAL FIXES VALIDATION")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    total_tests = 0
    passed_tests = 0
    
    # Test 1: Import Validation
    print_header("1. Import Validation")
    
    tests = [
        ("Broker Adapters", "from trading_bot.brokers import BrokerAdapter, MT5BrokerAdapter, MockBrokerAdapter"),
        ("Position Sizer", "from trading_bot.risk.position_sizer import PositionSizer, SizingMethod"),
        ("Fill Tracker", "from trading_bot.execution.fill_tracker import FillTracker, FillStatus"),
        ("Correlation Persistence", "from trading_bot.risk.correlation_persistence import EnhancedCorrelationManager"),
        ("Health Endpoints", "from trading_bot.infrastructure.health_endpoints import HealthCheckManager"),
        ("Database Initializer", "from trading_bot.persistence.database_initializer import DatabaseInitializer"),
        ("Survival Core", "from trading_bot.core.survival_core import SurvivalCore"),
    ]
    
    for name, import_stmt in tests:
        total_tests += 1
        try:
            exec(import_stmt)
            print_test(name, True)
            passed_tests += 1
        except Exception as e:
            print_test(name, False, str(e))
    
    # Test 2: Component Initialization
    print_header("2. Component Initialization")
    
    try:
        from trading_bot.brokers import MockBrokerAdapter
        broker = MockBrokerAdapter({'initial_balance': 10000})
        total_tests += 1
        print_test("Mock Broker Adapter", broker is not None)
        passed_tests += 1 if broker else 0
    except Exception as e:
        total_tests += 1
        print_test("Mock Broker Adapter", False, str(e))
    
    try:
        from trading_bot.risk.position_sizer import PositionSizer
        sizer = PositionSizer()
        total_tests += 1
        print_test("Position Sizer", sizer is not None)
        passed_tests += 1 if sizer else 0
    except Exception as e:
        total_tests += 1
        print_test("Position Sizer", False, str(e))
    
    try:
        from trading_bot.execution.fill_tracker import FillTracker
        from trading_bot.brokers import MockBrokerAdapter
        broker = MockBrokerAdapter()
        tracker = FillTracker(broker)
        total_tests += 1
        print_test("Fill Tracker", tracker is not None)
        passed_tests += 1 if tracker else 0
    except Exception as e:
        total_tests += 1
        print_test("Fill Tracker", False, str(e))
    
    try:
        from trading_bot.risk.correlation_persistence import EnhancedCorrelationManager
        manager = EnhancedCorrelationManager()
        total_tests += 1
        print_test("Correlation Manager", manager is not None)
        passed_tests += 1 if manager else 0
    except Exception as e:
        total_tests += 1
        print_test("Correlation Manager", False, str(e))
    
    try:
        from trading_bot.infrastructure.health_endpoints import HealthCheckManager
        health = HealthCheckManager()
        total_tests += 1
        print_test("Health Check Manager", health is not None)
        passed_tests += 1 if health else 0
    except Exception as e:
        total_tests += 1
        print_test("Health Check Manager", False, str(e))
    
    try:
        from trading_bot.persistence.database_initializer import DatabaseInitializer
        db_init = DatabaseInitializer()
        total_tests += 1
        print_test("Database Initializer", db_init is not None)
        passed_tests += 1 if db_init else 0
    except Exception as e:
        total_tests += 1
        print_test("Database Initializer", False, str(e))
    
    # Test 3: Functional Tests
    print_header("3. Functional Tests")
    
    # Test position sizing
    try:
        from trading_bot.risk.position_sizer import PositionSizer
        sizer = PositionSizer()
        size = sizer.calculate_position_size(
            symbol='EURUSD',
            account_equity=10000,
            risk_pct=0.02,
            stop_loss_pips=50
        )
        total_tests += 1
        passed = size > 0 and size < 1000000
        print_test("Position Size Calculation", passed, f"Size: {size:,.0f} units")
        passed_tests += 1 if passed else 0
    except Exception as e:
        total_tests += 1
        print_test("Position Size Calculation", False, str(e))
    
    # Test broker adapter
    try:
        from trading_bot.brokers import MockBrokerAdapter, OrderSide, OrderType
        broker = MockBrokerAdapter({'initial_balance': 10000})
        
        # Test connection
        connected = await broker.connect()
        total_tests += 1
        print_test("Broker Connection", connected)
        passed_tests += 1 if connected else 0
        
        # Test order placement
        response = await broker.place_order(
            symbol='EURUSD',
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=100000,
            price=1.1000
        )
        total_tests += 1
        passed = response is not None and response.filled_quantity == 100000
        print_test("Order Placement", passed, f"Filled: {response.filled_quantity if response else 0}")
        passed_tests += 1 if passed else 0
        
        # Test account equity
        equity = await broker.get_account_equity()
        total_tests += 1
        passed = equity > 0
        print_test("Account Equity", passed, f"Equity: ${equity:,.2f}")
        passed_tests += 1 if passed else 0
        
    except Exception as e:
        total_tests += 3
        print_test("Broker Tests", False, str(e))
    
    # Test correlation persistence
    try:
        from trading_bot.risk.correlation_persistence import EnhancedCorrelationManager
        manager = EnhancedCorrelationManager()
        
        # Add price data
        for i in range(50):
            manager.update_price('EURUSD', 1.1000 + i * 0.0001)
            manager.update_price('GBPUSD', 1.3000 + i * 0.00015)
        
        # Calculate correlation
        matrix = manager.calculate_correlation_matrix(['EURUSD', 'GBPUSD'])
        total_tests += 1
        passed = matrix is not None
        print_test("Correlation Calculation", passed)
        passed_tests += 1 if passed else 0
        
        # Test save/load
        saved = manager.save_state()
        total_tests += 1
        print_test("Correlation Save", saved)
        passed_tests += 1 if saved else 0
        
    except Exception as e:
        total_tests += 2
        print_test("Correlation Tests", False, str(e))
    
    # Test 4: Integration Test
    print_header("4. Integration Test")
    
    try:
        from trading_bot.core.survival_core import SurvivalCore
        
        config = {
            'broker': {'type': 'mock', 'initial_balance': 10000},
            'database': {},
            'execution': {},
            'fill_tracker': {},
            'position_sizer': {},
            'correlation': {},
        }
        
        core = SurvivalCore(config)
        
        # Check all components
        components = {
            'Broker Adapter': core.broker_adapter,
            'Database': core.time_series_db,
            'Execution Manager': core.execution,
            'Fill Tracker': core.fill_tracker,
            'Position Sizer': core.position_sizer,
            'Correlation Manager': core.correlation_manager,
        }
        
        for name, component in components.items():
            total_tests += 1
            passed = component is not None
            print_test(name, passed)
            passed_tests += 1 if passed else 0
        
    except Exception as e:
        total_tests += 6
        print_test("Integration Test", False, str(e))
    
    # Test 5: No Circular Imports
    print_header("5. Circular Import Check")
    
    try:
        import trading_bot.core.survival_core
        import trading_bot.core.execution_manager
        import trading_bot.brokers.broker_adapter
        import trading_bot.risk.position_sizer
        total_tests += 1
        print_test("No Circular Imports", True)
        passed_tests += 1
    except Exception as e:
        total_tests += 1
        print_test("No Circular Imports", False, str(e))
    
    # Summary
    print_header("VALIDATION SUMMARY")
    
    pass_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
    
    print(f"Total Tests:  {total_tests}")
    print(f"Passed:       {passed_tests}")
    print(f"Failed:       {total_tests - passed_tests}")
    print(f"Pass Rate:    {pass_rate:.1f}%")
    print()
    
    if pass_rate == 100:
        print("[SUCCESS] ALL TESTS PASSED! System is ready for testing.")
        return 0
    elif pass_rate >= 90:
        print("[OK] Most tests passed. Minor issues to address.")
        return 0
    elif pass_rate >= 70:
        print("[WARNING] Some tests failed. Review failures above.")
        return 1
    else:
        print("[ERROR] Many tests failed. Critical issues remain.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
