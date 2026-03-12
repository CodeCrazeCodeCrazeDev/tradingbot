"""
Comprehensive Test Suite for AlphaAlgo Trading Bot

Tests all components, functionality, and integration points.
"""

import asyncio
import logging
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Any
import numpy as np
import pandas as pd

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ComprehensiveTestSuite:
    """Comprehensive testing suite for the trading bot"""
    
    def __init__(self):
        self.test_results = {
            'unit_tests': [],
            'integration_tests': [],
            'performance_tests': [],
            'stress_tests': [],
            'end_to_end_tests': []
        }
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0
    
    def print_header(self, title: str):
        """Print section header"""
        print(f"\n{'='*70}")
        print(f"  {title}")
        print(f"{'='*70}")
    
    def record_test(self, category: str, name: str, passed: bool, details: str = ""):
        """Record test result"""
        self.total_tests += 1
        if passed:
            self.passed_tests += 1
            status = "[PASS]"
        else:
            self.failed_tests += 1
            status = "[FAIL]"
        
        result = {
            'name': name,
            'passed': passed,
            'details': details,
            'timestamp': datetime.now()
        }
        
        self.test_results[category].append(result)
        print(f"{status} {name}")
        if details:
            print(f"       {details}")
        
        return passed
    
    async def test_broker_adapter(self):
        """Test broker adapter functionality"""
        self.print_header("1. BROKER ADAPTER TESTS")
        
        try:
            from trading_bot.brokers import MockBrokerAdapter, BrokerAdapter
            
            # Test 1: Initialization
            broker = MockBrokerAdapter({'initial_balance': 10000})
            self.record_test('unit_tests', 'Broker Initialization', 
                           broker is not None, f"Balance: ${broker.account_balance:,.0f}")
            
            # Test 2: Connection
            await broker.connect()
            self.record_test('unit_tests', 'Broker Connection', 
                           broker.connected, "Connected successfully")
            
            # Test 3: Get Account Info
            equity = await broker.get_account_equity()
            self.record_test('unit_tests', 'Get Account Equity', 
                           equity == 10000, f"Equity: ${equity:,.0f}")
            
            # Test 4: Place Order
            from trading_bot.brokers.broker_adapter import OrderSide, OrderType
            order = await broker.place_order(
                symbol='EURUSD',
                side=OrderSide.BUY,
                order_type=OrderType.MARKET,
                quantity=10000
            )
            self.record_test('unit_tests', 'Place Order', 
                           order is not None, f"Order ID: {order.order_id if order else 'None'}")
            
            # Test 5: Get Positions
            positions = await broker.get_positions()
            self.record_test('unit_tests', 'Get Positions', 
                           isinstance(positions, list), f"Positions: {len(positions)}")
            
            # Test 6: Disconnection
            await broker.disconnect()
            self.record_test('unit_tests', 'Broker Disconnection', 
                           not broker.connected, "Disconnected successfully")
            
        except Exception as e:
            self.record_test('unit_tests', 'Broker Adapter Tests', False, str(e))
    
    async def test_position_sizer(self):
        """Test position sizing functionality"""
        self.print_header("2. POSITION SIZER TESTS")
        
        try:
            from trading_bot.risk.position_sizer import PositionSizer, SizingMethod
            
            sizer = PositionSizer({
                'default_risk_pct': 0.02,
                'max_position_size': 1000000,
                'min_position_size': 1000
            })
            
            # Test 1: Fixed Risk Sizing
            size = sizer.calculate_position_size(
                symbol='EURUSD',
                account_equity=10000,
                risk_pct=0.02,
                stop_loss_pips=50,
                entry_price=1.1000,
                method=SizingMethod.FIXED_RISK
            )
            self.record_test('unit_tests', 'Fixed Risk Position Sizing', 
                           size > 0, f"Size: {size:,.0f} units")
            
            # Test 2: Kelly Criterion
            size = sizer.calculate_position_size(
                symbol='EURUSD',
                account_equity=10000,
                risk_pct=0.02,
                stop_loss_pips=50,
                entry_price=1.1000,
                method=SizingMethod.KELLY_CRITERION,
                win_rate=0.6,
                avg_win=100,
                avg_loss=50
            )
            self.record_test('unit_tests', 'Kelly Criterion Position Sizing', 
                           size > 0, f"Size: {size:,.0f} units")
            
            # Test 3: Volatility Adjusted
            size = sizer.calculate_position_size(
                symbol='EURUSD',
                account_equity=10000,
                risk_pct=0.02,
                stop_loss_pips=50,
                entry_price=1.1000,
                method=SizingMethod.VOLATILITY_ADJUSTED,
                volatility=0.015
            )
            self.record_test('unit_tests', 'Volatility Adjusted Position Sizing', 
                           size > 0, f"Size: {size:,.0f} units")
            
            # Test 4: Position Size Limits
            size = sizer.calculate_position_size(
                symbol='EURUSD',
                account_equity=10000,
                risk_pct=0.5,  # Very high risk
                stop_loss_pips=10,
                entry_price=1.1000
            )
            self.record_test('unit_tests', 'Position Size Limits', 
                           size <= sizer.max_position_size, 
                           f"Size: {size:,.0f} (max: {sizer.max_position_size:,.0f})")
            
        except Exception as e:
            self.record_test('unit_tests', 'Position Sizer Tests', False, str(e))
    
    async def test_fill_tracker(self):
        """Test fill tracker functionality"""
        self.print_header("3. FILL TRACKER TESTS")
        
        try:
            from trading_bot.brokers import MockBrokerAdapter
            from trading_bot.execution.fill_tracker import FillTracker
            
            broker = MockBrokerAdapter({'initial_balance': 10000})
            await broker.connect()
            
            tracker = FillTracker(broker, {
                'confirmation_timeout': 30,
                'max_retries': 3
            })
            
            # Test 1: Track Order Fill
            from trading_bot.brokers.broker_adapter import OrderSide, OrderType
            order = await broker.place_order(
                symbol='EURUSD',
                side=OrderSide.BUY,
                order_type=OrderType.MARKET,
                quantity=10000
            )
            
            if order:
                # Track order with correct parameters
                from trading_bot.brokers.broker_adapter import OrderSide
                fill_record = await tracker.track_order(
                    order_id=order.order_id,
                    symbol='EURUSD',
                    side='BUY',
                    quantity=10000,
                    expected_price=1.1000
                )
                # Wait a bit for confirmation
                await asyncio.sleep(0.1)
                self.record_test('unit_tests', 'Track Order Fill', 
                               fill_record is not None, 
                               f"Fill: {fill_record.filled_quantity if fill_record else 0:,.0f} units")
            else:
                self.record_test('unit_tests', 'Track Order Fill', False, "Order placement failed")
            
            # Test 2: Slippage Calculation
            slippage_stats = tracker.get_slippage_stats('EURUSD')
            self.record_test('unit_tests', 'Slippage Statistics', 
                           isinstance(slippage_stats, dict), 
                           f"Stats: {len(slippage_stats)} metrics")
            
            await broker.disconnect()
            
        except Exception as e:
            self.record_test('unit_tests', 'Fill Tracker Tests', False, str(e))
    
    async def test_correlation_persistence(self):
        """Test correlation persistence"""
        self.print_header("4. CORRELATION PERSISTENCE TESTS")
        
        try:
            from trading_bot.risk.correlation_persistence import CorrelationPersistence
            import tempfile
            import os
            
            # Create temp directory
            temp_dir = tempfile.mkdtemp()
            
            persistence = CorrelationPersistence({
                'storage_dir': temp_dir
            })
            
            # Test 1: Save Correlation Matrix
            symbols = ['EURUSD', 'GBPUSD', 'USDJPY']
            
            # Create DataFrame for correlation matrix
            correlation_matrix = pd.DataFrame(
                np.random.rand(3, 3),
                index=symbols,
                columns=symbols
            )
            correlation_matrix = (correlation_matrix + correlation_matrix.T) / 2
            np.fill_diagonal(correlation_matrix.values, 1.0)
            
            # Price history
            price_history = {symbol: [1.1 + i*0.001 for i in range(100)] for symbol in symbols}
            
            success = persistence.save_correlation_state(correlation_matrix, price_history)
            self.record_test('unit_tests', 'Save Correlation Matrix', 
                           success, f"Saved {len(symbols)} symbols")
            
            # Test 2: Load Correlation State
            loaded_state = persistence.load_correlation_state()
            self.record_test('unit_tests', 'Load Correlation State', 
                           loaded_state is not None and 'matrix' in loaded_state,
                           f"Loaded {len(loaded_state.get('history', {})) if loaded_state else 0} symbols")
            
            # Test 3: Verify Data Integrity
            if loaded_state:
                loaded_matrix = loaded_state.get('matrix')
                loaded_history = loaded_state.get('history')
                integrity_ok = (
                    loaded_matrix is not None and
                    loaded_history is not None and
                    len(loaded_history) == len(symbols)
                )
                self.record_test('unit_tests', 'Data Integrity Check', 
                               integrity_ok,
                               f"Matrix shape: {loaded_matrix.shape if loaded_matrix is not None else 'None'}")
            else:
                self.record_test('unit_tests', 'Data Integrity Check', False, "No state loaded")
            
            # Cleanup
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)
            
        except Exception as e:
            self.record_test('unit_tests', 'Correlation Persistence Tests', False, str(e))
    
    async def test_health_endpoints(self):
        """Test health check endpoints"""
        self.print_header("5. HEALTH ENDPOINTS TESTS")
        
        try:
            from trading_bot.infrastructure.health_endpoints import HealthCheckManager
            
            health = HealthCheckManager({
                'check_interval': 30,
                'startup_grace_period': 0
            })
            
            # Test 1: Register Component
            health.register_component('test_component', lambda: True)
            self.record_test('unit_tests', 'Register Health Component', 
                           'test_component' in health.components,
                           "Component registered")
            
            # Test 2: Check All Components
            results = await health.check_all()
            self.record_test('unit_tests', 'Health Check All', 
                           len(results) > 0,
                           f"Checked {len(results)} components")
            
            # Test 3: Get Status Summary
            status = health.get_status_summary()
            self.record_test('unit_tests', 'Status Summary', 
                           isinstance(status, dict), f"Status: {status.get('overall_status', 'unknown')}")
            
        except Exception as e:
            self.record_test('unit_tests', 'Health Endpoints Tests', False, str(e))
    
    async def test_performance_optimization(self):
        """Test performance optimization"""
        self.print_header("6. PERFORMANCE OPTIMIZATION TESTS")
        
        try:
            from trading_bot.infrastructure.memory_optimizer import MemoryOptimizer
            from trading_bot.infrastructure.network_optimizer import NetworkOptimizer
            
            # Test 1: Memory Optimizer
            mem_opt = MemoryOptimizer({'min_free_memory_mb': 500})
            stats = mem_opt.get_memory_stats()
            self.record_test('performance_tests', 'Memory Optimizer', 
                           stats.get('available_mb', 0) > 0,
                           f"Available: {stats.get('available_mb', 0):.0f}MB")
            
            # Test 2: Memory Optimization
            result = mem_opt.optimize_memory(force=True)
            self.record_test('performance_tests', 'Memory Optimization', 
                           result.get('optimized', False),
                           f"Freed: {result.get('freed_mb', 0):.1f}MB")
            
            # Test 3: Network Optimizer
            net_opt = NetworkOptimizer({'max_latency_ms': 100})
            self.record_test('performance_tests', 'Network Optimizer', 
                           net_opt is not None,
                           f"Target: <{net_opt.max_latency_ms}ms")
            
        except Exception as e:
            self.record_test('performance_tests', 'Performance Optimization Tests', False, str(e))
    
    async def test_integration(self):
        """Test integration between components"""
        self.print_header("7. INTEGRATION TESTS")
        
        try:
            from trading_bot.brokers import MockBrokerAdapter
            from trading_bot.risk.position_sizer import PositionSizer
            from trading_bot.execution.fill_tracker import FillTracker
            from trading_bot.brokers.broker_adapter import OrderSide, OrderType
            
            # Test 1: Complete Trading Flow
            broker = MockBrokerAdapter({'initial_balance': 10000})
            await broker.connect()
            
            sizer = PositionSizer()
            tracker = FillTracker(broker)
            
            # Calculate position size
            position_size = sizer.calculate_position_size(
                symbol='EURUSD',
                account_equity=10000,
                risk_pct=0.02,
                stop_loss_pips=50,
                entry_price=1.1000
            )
            
            # Place order
            order = await broker.place_order(
                symbol='EURUSD',
                side=OrderSide.BUY,
                order_type=OrderType.MARKET,
                quantity=position_size
            )
            
            # Track fill
            if order:
                fill_record = await tracker.track_order(
                    order_id=order.order_id,
                    symbol='EURUSD',
                    side='BUY',
                    quantity=position_size,
                    expected_price=1.1000
                )
                await asyncio.sleep(0.1)
                success = fill_record is not None
            else:
                success = False
            
            self.record_test('integration_tests', 'Complete Trading Flow', 
                           success,
                           f"Size: {position_size:,.0f}, Order: {order.order_id if order else 'None'}")
            
            await broker.disconnect()
            
        except Exception as e:
            self.record_test('integration_tests', 'Integration Tests', False, str(e))
    
    async def test_stress(self):
        """Stress test the system"""
        self.print_header("8. STRESS TESTS")
        
        try:
            from trading_bot.brokers import MockBrokerAdapter
            from trading_bot.brokers.broker_adapter import OrderSide, OrderType
            
            broker = MockBrokerAdapter({'initial_balance': 100000})
            await broker.connect()
            
            # Test 1: Multiple Orders
            num_orders = 100
            start_time = datetime.now()
            
            orders_placed = 0
            for i in range(num_orders):
                order = await broker.place_order(
                    symbol='EURUSD',
                    side=OrderSide.BUY if i % 2 == 0 else OrderSide.SELL,
                    order_type=OrderType.MARKET,
                    quantity=1000
                )
                if order:
                    orders_placed += 1
            
            duration = (datetime.now() - start_time).total_seconds()
            orders_per_second = orders_placed / duration if duration > 0 else 0
            
            self.record_test('stress_tests', 'Multiple Orders Stress Test', 
                           orders_placed == num_orders,
                           f"{orders_placed}/{num_orders} orders, {orders_per_second:.1f} orders/sec")
            
            await broker.disconnect()
            
        except Exception as e:
            self.record_test('stress_tests', 'Stress Tests', False, str(e))
    
    async def run_all_tests(self):
        """Run all test suites"""
        print("\n" + "="*70)
        print("  COMPREHENSIVE TEST SUITE - ALPHAALGO TRADING BOT")
        print("="*70)
        print(f"  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*70)
        
        # Run all test categories
        await self.test_broker_adapter()
        await self.test_position_sizer()
        await self.test_fill_tracker()
        await self.test_correlation_persistence()
        await self.test_health_endpoints()
        await self.test_performance_optimization()
        await self.test_integration()
        await self.test_stress()
        
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        self.print_header("TEST SUMMARY")
        
        print(f"\nTotal Tests: {self.total_tests}")
        print(f"Passed: {self.passed_tests}")
        print(f"Failed: {self.failed_tests}")
        print(f"Success Rate: {(self.passed_tests/self.total_tests*100):.1f}%")
        
        print(f"\nBreakdown by Category:")
        for category, results in self.test_results.items():
            if results:
                passed = sum(1 for r in results if r['passed'])
                total = len(results)
                print(f"  {category.replace('_', ' ').title()}: {passed}/{total}")
        
        print("\n" + "="*70)
        if self.failed_tests == 0:
            print("  [SUCCESS] ALL TESTS PASSED!")
            print("  Your bot is fully tested and ready!")
        else:
            print(f"  [WARNING] {self.failed_tests} test(s) failed")
            print("  Review the output above for details")
        print("="*70 + "\n")
        
        return self.failed_tests == 0


async def main():
    """Main test function"""
    suite = ComprehensiveTestSuite()
    success = await suite.run_all_tests()
    return 0 if success else 1


if __name__ == '__main__':
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
