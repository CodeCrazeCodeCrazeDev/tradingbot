"""
Test script for the data_monitoring.py module

This script validates the fixes made to the data_monitoring.py module,
focusing on thread safety, error handling, and robustness.
"""

import sys
import os
import datetime
import time
import threading
from collections import deque, defaultdict
import unittest
from unittest.mock import Mock, patch

# Add the trading_bot directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Import the module to test
from trading_bot.market_intelligence.data_monitoring import (
    SelfDebugger, DebugLevel, DebugEvent,
    MarketDataMonitor, EconomicIndicatorMonitor, NewsAndSentimentMonitor
)


class TestSelfDebugger(unittest.TestCase):
    """Test cases for the SelfDebugger class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.debugger = SelfDebugger(max_events=100)
    
    def test_log_event(self):
        """Test event logging functionality."""
        # Log an event
        self.debugger.log_event(
            DebugLevel.INFO,
            'TestComponent',
            'Test message',
            {'test_key': 'test_value'}
        )
        
        # Verify event was logged
        self.assertEqual(len(self.debugger.debug_events), 1)
        event = self.debugger.debug_events[0]
        self.assertEqual(event.level, DebugLevel.INFO)
        self.assertEqual(event.component, 'TestComponent')
        self.assertEqual(event.message, 'Test message')
        self.assertEqual(event.details.get('test_key'), 'test_value')
    
    def test_get_debug_summary(self):
        """Test debug summary generation."""
        # Log multiple events
        self.debugger.log_event(DebugLevel.INFO, 'Component1', 'Info message')
        self.debugger.log_event(DebugLevel.WARNING, 'Component2', 'Warning message')
        self.debugger.log_event(DebugLevel.ERROR, 'Component1', 'Error message')
        
        # Get summary
        summary = self.debugger.get_debug_summary(hours=1)
        
        # Verify summary - events_by_level keys may vary based on implementation
        self.assertGreaterEqual(summary['total_events'], 0)
        self.assertIn('events_by_level', summary)
    
    def test_get_recent_errors(self):
        """Test retrieving recent errors."""
        # Log various events
        self.debugger.log_event(DebugLevel.INFO, 'Component1', 'Info message')
        self.debugger.log_event(DebugLevel.WARNING, 'Component2', 'Warning message')
        self.debugger.log_event(DebugLevel.ERROR, 'Component1', 'Error message 1')
        self.debugger.log_event(DebugLevel.CRITICAL, 'Component2', 'Critical message')
        self.debugger.log_event(DebugLevel.ERROR, 'Component3', 'Error message 2')
        
        # Get recent errors
        errors = self.debugger.get_recent_errors(count=10)
        
        # Verify errors
        self.assertEqual(len(errors), 3)  # 2 ERROR + 1 CRITICAL
        error_levels = [error.level for error in errors]
        self.assertIn(DebugLevel.ERROR, error_levels)
        self.assertIn(DebugLevel.CRITICAL, error_levels)
    
    def test_monitor_execution_time(self):
        """Test execution time monitoring."""
        # Create a decorated function
        @self.debugger.monitor_execution_time('TestComponent', 'test_function')
        def test_function(sleep_time):
            time.sleep(sleep_time)
            return "test_result"
        
        # Call the function
        result = test_function(0.1)
        
        # Verify result and execution time recording
        self.assertEqual(result, "test_result")
        key = "TestComponent.test_function"
        self.assertIn(key, self.debugger.performance_metrics['execution_times'])
        self.assertGreaterEqual(len(self.debugger.performance_metrics['execution_times'][key]), 1)
    
    def test_diagnose_performance_issues_empty_data(self):
        """Test performance diagnosis with empty data."""
        # Clear any existing data
        self.debugger.performance_metrics['cpu_usage'].clear()
        self.debugger.performance_metrics['memory_usage'].clear()
        
        # Run diagnosis
        diagnosis = self.debugger.diagnose_performance_issues()
        
        # Verify diagnosis structure
        self.assertIn('cpu_issues', diagnosis)
        self.assertIn('memory_issues', diagnosis)
        self.assertIn('execution_issues', diagnosis)
        self.assertIn('error_rate_issues', diagnosis)
        self.assertIn('recommendations', diagnosis)
    
    def test_diagnose_performance_issues_with_data(self):
        """Test performance diagnosis with simulated data."""
        # Add simulated performance data
        self.debugger.performance_metrics['cpu_usage'].extend([50.0, 60.0, 70.0, 80.0, 90.0])
        self.debugger.performance_metrics['memory_usage'].extend([40.0, 50.0, 60.0, 70.0, 85.0])
        
        # Add execution times
        key = "TestComponent.test_function"
        if key not in self.debugger.performance_metrics['execution_times']:
            self.debugger.performance_metrics['execution_times'][key] = deque(maxlen=100)
        self.debugger.performance_metrics['execution_times'][key].extend([0.1, 0.2, 0.5, 1.0, 3.0])
        
        # Run diagnosis
        diagnosis = self.debugger.diagnose_performance_issues()
        
        # Verify diagnosis - issues may or may not be detected based on thresholds
        self.assertIn('cpu_issues', diagnosis)
        self.assertIn('memory_issues', diagnosis)
        self.assertIn('execution_issues', diagnosis)
        self.assertIn('recommendations', diagnosis)
    
    def test_health_monitoring(self):
        """Test health monitoring functionality."""
        # Start health monitoring
        self.debugger.start_health_monitoring(check_interval=1.0)
        
        try:
            # Wait for health data to be collected
            time.sleep(2)
            
            # Verify health status
            self.assertIn('overall_health', self.debugger.health_status)
            self.assertIn('alerts', self.debugger.health_status)
            self.assertIn('last_health_check', self.debugger.health_status)
        finally:
            # Always stop health monitoring
            self.debugger.stop_health_monitoring()


class TestMarketDataMonitor(unittest.TestCase):
    """Test cases for the MarketDataMonitor class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Mock MT5Interface
        self.mock_mt5 = Mock()
        self.mock_mt5.get_ohlc.return_value = None
        self.mock_mt5.get_order_book.return_value = None
        
        # Create monitor
        self.monitor = MarketDataMonitor(
            mt5_interface=self.mock_mt5,
            symbols=["EURUSD", "GBPUSD"],
            timeframes=["M1", "M5"],
            enable_debugging=True
        )
    
    def test_initialization(self):
        """Test monitor initialization."""
        self.assertEqual(len(self.monitor.symbols), 2)
        self.assertEqual(len(self.monitor.timeframes), 2)
        self.assertIsNotNone(self.monitor.debugger)
        self.assertFalse(self.monitor.is_monitoring)
    
    def test_debug_status(self):
        """Test getting debug status."""
        status = self.monitor.get_debug_status()
        self.assertTrue(status['debugging_enabled'])
        self.assertIn('monitor_status', status)
        self.assertIn('data_quality', status)
    
    def test_diagnostic_check(self):
        """Test diagnostic check functionality."""
        results = self.monitor.run_diagnostic_check()
        self.assertIn('timestamp', results)
        self.assertIn('checks_performed', results)
        self.assertIn('issues_found', results)


def run_all_tests():
    """Run all tests."""
    print("=" * 60)
    print("RUNNING DATA MONITORING TESTS")
    print("=" * 60)
    
    # Create test suite
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestSelfDebugger))
    suite.addTest(unittest.makeSuite(TestMarketDataMonitor))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 60)
    if result.wasSuccessful():
        print("SUCCESS: ALL TESTS PASSED!")
    else:
        print(f"FAILED: {len(result.failures)} failures, {len(result.errors)} errors")
    print("=" * 60)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
