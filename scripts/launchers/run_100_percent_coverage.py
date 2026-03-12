"""
100% COVERAGE TEST RUNNER
=========================

Runs all tests with coverage measurement and generates detailed reports.
Targets 100% coverage on critical modules.
"""

import subprocess
import sys
import os
from pathlib import Path
from datetime import datetime

# Configuration
CRITICAL_MODULES = [
    'trading_bot.risk.position_size_calculator',
    'trading_bot.risk.kelly_criterion',
    'trading_bot.risk.var_engine',
    'trading_bot.risk.circuit_breaker',
    'trading_bot.risk.drawdown_protector',
    'trading_bot.execution.trade_executor',
    'trading_bot.execution.fill_tracker',
    'trading_bot.execution.idempotent_executor',
    'trading_bot.validation.data_validator',
    'trading_bot.signals.signal_lifecycle',
]

IMPORTANT_MODULES = [
    'trading_bot.ml.ensemble_models',
    'trading_bot.ml.online_learning',
    'trading_bot.analysis.technical_indicators',
    'trading_bot.analysis.market_regime',
    'trading_bot.execution.algorithms',
    'trading_bot.execution.market_impact',
    'trading_bot.database.timeseries_db',
]

TEST_FILES = [
    'tests/test_critical_100_percent_coverage.py',
    'tests/test_critical_validation_signals_coverage.py',
    'tests/test_critical_execution_ml_coverage.py',
    'tests/test_realtime_data_integration.py',
    'tests/test_edge_cases_integration.py',
    'tests/test_mutation_quality.py',
]


def run_coverage_tests():
    """Run tests with coverage measurement"""
    print("=" * 80)
    print("100% COVERAGE TEST SUITE")
    print("=" * 80)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Check if pytest and coverage are installed
    try:
        import pytest
        import coverage
    except ImportError as e:
        print(f"Missing dependency: {e}")
        print("Installing required packages...")
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'pytest', 'pytest-cov', 'coverage'])
    
    # Build test command
    test_files = ' '.join(TEST_FILES)
    
    # Run tests with coverage
    cmd = [
        sys.executable, '-m', 'pytest',
        *TEST_FILES,
        '-v',
        '--tb=short',
        '--timeout=120',
        f'--cov=trading_bot',
        '--cov-report=term-missing',
        '--cov-report=html:coverage_html',
        '--cov-fail-under=0',  # Don't fail on coverage threshold
    ]
    
    print("Running command:")
    print(' '.join(cmd))
    print()
    
    result = subprocess.run(cmd, cwd=os.path.dirname(os.path.abspath(__file__)))
    
    return result.returncode


def run_critical_module_coverage():
    """Run coverage specifically for critical modules"""
    print()
    print("=" * 80)
    print("CRITICAL MODULE COVERAGE ANALYSIS")
    print("=" * 80)
    
    # Build source filter for critical modules
    source_filter = ','.join(CRITICAL_MODULES)
    
    cmd = [
        sys.executable, '-m', 'pytest',
        *TEST_FILES,
        '-v',
        '--tb=short',
        '--timeout=120',
        f'--cov=trading_bot.risk',
        f'--cov=trading_bot.execution',
        f'--cov=trading_bot.validation',
        f'--cov=trading_bot.signals',
        '--cov-report=term-missing',
    ]
    
    result = subprocess.run(cmd, cwd=os.path.dirname(os.path.abspath(__file__)))
    
    return result.returncode


def generate_coverage_report():
    """Generate detailed coverage report"""
    print()
    print("=" * 80)
    print("GENERATING COVERAGE REPORT")
    print("=" * 80)
    
    # Generate HTML report
    cmd = [
        sys.executable, '-m', 'coverage', 'html',
        '-d', 'coverage_html',
        '--title', '100% Coverage Report'
    ]
    
    subprocess.run(cmd, cwd=os.path.dirname(os.path.abspath(__file__)))
    
    # Generate XML report for CI/CD
    cmd = [
        sys.executable, '-m', 'coverage', 'xml',
        '-o', 'coverage.xml'
    ]
    
    subprocess.run(cmd, cwd=os.path.dirname(os.path.abspath(__file__)))
    
    print()
    print("Coverage reports generated:")
    print("  - HTML: coverage_html/index.html")
    print("  - XML: coverage.xml")


def print_coverage_summary():
    """Print coverage summary"""
    print()
    print("=" * 80)
    print("COVERAGE SUMMARY")
    print("=" * 80)
    
    cmd = [
        sys.executable, '-m', 'coverage', 'report',
        '--include=trading_bot/risk/*,trading_bot/execution/*,trading_bot/validation/*,trading_bot/signals/*'
    ]
    
    subprocess.run(cmd, cwd=os.path.dirname(os.path.abspath(__file__)))


def main():
    """Main entry point"""
    print()
    print("╔" + "═" * 78 + "╗")
    print("║" + " 100% COVERAGE TEST SUITE ".center(78) + "║")
    print("║" + " Trading Bot Critical Module Testing ".center(78) + "║")
    print("╚" + "═" * 78 + "╝")
    print()
    
    # Run tests
    exit_code = run_coverage_tests()
    
    # Generate reports
    generate_coverage_report()
    
    # Print summary
    print_coverage_summary()
    
    print()
    print("=" * 80)
    print("TEST RUN COMPLETE")
    print("=" * 80)
    print(f"Finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Exit code: {exit_code}")
    
    if exit_code == 0:
        print("✅ All tests passed!")
    else:
        print("❌ Some tests failed. Check the output above.")
    
    return exit_code


if __name__ == '__main__':
    sys.exit(main())
