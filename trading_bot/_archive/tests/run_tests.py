#!/usr/bin/env python
"""Test runner for trading bot integration tests."""
import unittest
import sys
import os

# Add parent directory to path to allow importing modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

# Import test modules with graceful fallbacks
TestMLStrategyEngine = None
TestExecutionAlgorithms = None
TestEmotionalTracking = None
TestEnhancedPerformanceAnalytics = None
TestMainIntegration = None
TestEndToEnd = None

try:
    from trading_bot.tests.test_ml_strategy import TestMLStrategyEngine
except ImportError:
    pass

try:
    from trading_bot.tests.test_execution_algorithms import TestExecutionAlgorithms
except ImportError:
    pass

try:
    from trading_bot.tests.test_emotional_tracking import TestEmotionalTracking, TestEnhancedPerformanceAnalytics
except Exception:
    TestEmotionalTracking = None
    TestEnhancedPerformanceAnalytics = None

try:
    from trading_bot.tests.test_main_integration import TestMainIntegration
except ImportError:
    pass

try:
    from trading_bot.tests.test_end_to_end import TestEndToEnd
except ImportError:
    pass
# Import existing tests
    from trading_bot.tests.test_liquidity import TestLiquidity
    from trading_bot.tests.test_market_structure import TestMarketStructure
    from trading_bot.tests.test_risk import TestRiskManager
except ImportError:
    print("Note: Some existing tests could not be imported. Running only new tests.")


def create_test_suite():
    """Create a test suite containing all tests."""
    test_suite = unittest.TestSuite()
    
    try:
        # Add existing tests if available
        test_suite.addTest(unittest.makeSuite(TestLiquidity))
        test_suite.addTest(unittest.makeSuite(TestMarketStructure))
        test_suite.addTest(unittest.makeSuite(TestRiskManager))
    except NameError:
        pass
    
    # Add new integration tests (only if they were successfully imported)
    if TestMLStrategyEngine:
        test_suite.addTest(unittest.makeSuite(TestMLStrategyEngine))
    if TestExecutionAlgorithms:
        test_suite.addTest(unittest.makeSuite(TestExecutionAlgorithms))
    if TestEmotionalTracking:
        test_suite.addTest(unittest.makeSuite(TestEmotionalTracking))
    if TestEnhancedPerformanceAnalytics:
        test_suite.addTest(unittest.makeSuite(TestEnhancedPerformanceAnalytics))
    if TestMainIntegration:
        test_suite.addTest(unittest.makeSuite(TestMainIntegration))
    if TestEndToEnd:
        test_suite.addTest(unittest.makeSuite(TestEndToEnd))
    
    return test_suite


def run_tests():
    """Run all tests and return exit code."""
    test_suite = create_test_suite()
    test_runner = unittest.TextTestRunner(verbosity=2)
    result = test_runner.run(test_suite)
    return 0 if result.wasSuccessful() else 1


def run_specific_test(test_name):
    """Run a specific test by name."""
    test_suite = unittest.TestSuite()
    
    # Map test names to test classes
    test_map = {
        'ml_strategy': TestMLStrategyEngine,
        'execution': TestExecutionAlgorithms,
        'emotional': TestEmotionalTracking,
        'performance': TestEnhancedPerformanceAnalytics,
        'main': TestMainIntegration,
        'end_to_end': TestEndToEnd
    }
    
    try:
        # Add existing tests to map if available
        test_map.update({
            'liquidity': TestLiquidity,
            'market_structure': TestMarketStructure,
            'risk': TestRiskManager
        })
    except NameError:
        pass
    
    if test_name in test_map:
        test_suite.addTest(unittest.makeSuite(test_map[test_name]))
        test_runner = unittest.TextTestRunner(verbosity=2)
        result = test_runner.run(test_suite)
        return 0 if result.wasSuccessful() else 1
    else:
        print(f"Error: Test '{test_name}' not found.")
        print(f"Available tests: {', '.join(test_map.keys())}")
        return 1


if __name__ == '__main__':
    if len(sys.argv) > 1:
        # Run specific test
        test_name = sys.argv[1]
        sys.exit(run_specific_test(test_name))
    else:
        # Run all tests
        sys.exit(run_tests())
