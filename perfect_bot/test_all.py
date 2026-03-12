"""
Perfect Bot - Comprehensive Test Suite
Tests all components and validates system readiness
"""

import asyncio
import sys
from pathlib import Path

# Set UTF-8 encoding for console output
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')


class PerfectBotTester:
    """Comprehensive testing suite for Perfect Bot"""
    
    def __init__(self):
        self.tests_passed = 0
        self.tests_failed = 0
        self.results = []
    
    def test(self, name: str, func):
        """Run a test and record result"""
        print(f"\n{'='*70}")
        print(f"TEST: {name}")
        print(f"{'='*70}")
        
        try:
            result = func()
            if result:
                print(f"✅ PASS: {name}")
                self.tests_passed += 1
                self.results.append((name, 'PASS', None))
            else:
                print(f"❌ FAIL: {name}")
                self.tests_failed += 1
                self.results.append((name, 'FAIL', 'Test returned False'))
        except Exception as e:
            print(f"❌ FAIL: {name}")
            print(f"Error: {e}")
            self.tests_failed += 1
            self.results.append((name, 'FAIL', str(e)))
    
    async def test_async(self, name: str, func):
        """Run an async test"""
        print(f"\n{'='*70}")
        print(f"TEST: {name}")
        print(f"{'='*70}")
        
        try:
            result = await func()
            if result:
                print(f"✅ PASS: {name}")
                self.tests_passed += 1
                self.results.append((name, 'PASS', None))
            else:
                print(f"❌ FAIL: {name}")
                self.tests_failed += 1
                self.results.append((name, 'FAIL', 'Test returned False'))
        except Exception as e:
            print(f"❌ FAIL: {name}")
            print(f"Error: {e}")
            self.tests_failed += 1
            self.results.append((name, 'FAIL', str(e)))
    
    def print_summary(self):
        """Print test summary"""
        print(f"\n{'='*70}")
        print("TEST SUMMARY")
        print(f"{'='*70}")
        
        total = self.tests_passed + self.tests_failed
        pass_rate = (self.tests_passed / total * 100) if total > 0 else 0
        
        print(f"\nTotal Tests:  {total}")
        print(f"Passed:       {self.tests_passed} ✅")
        print(f"Failed:       {self.tests_failed} ❌")
        print(f"Pass Rate:    {pass_rate:.1f}%")
        
        if self.tests_failed > 0:
            print(f"\n❌ FAILED TESTS:")
            for name, status, error in self.results:
                if status == 'FAIL':
                    print(f"  - {name}")
                    if error:
                        print(f"    Error: {error}")
        
        print(f"\n{'='*70}")
        
        if self.tests_failed == 0:
            print("🎉 ALL TESTS PASSED! Perfect Bot is ready!")
        else:
            print("⚠️  Some tests failed. Please review and fix.")
        
        print(f"{'='*70}")


# Test Functions

def test_imports():
    """Test that all required modules can be imported"""
    try:
        import pandas
        import numpy
        import sklearn
        import aiohttp
        from dotenv import load_dotenv
        print("✅ All core imports successful")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False


def test_advanced_ml_imports():
    """Test advanced ML library imports"""
    try:
        import xgboost
        import lightgbm
        print("✅ XGBoost and LightGBM available")
        return True
    except ImportError as e:
        print(f"⚠️  Advanced ML libraries not available: {e}")
        print("Install with: py -m pip install xgboost lightgbm")
        return False


def test_env_file():
    """Test that .env file exists and has API keys"""
    env_file = Path('../.env')
    if not env_file.exists():
        print("❌ .env file not found")
        return False
    
    from dotenv import load_dotenv
    import os
    load_dotenv(env_file)
    
    av_key = os.getenv('ALPHA_VANTAGE_KEY')
    fred_key = os.getenv('FRED_API_KEY')
    
    if not av_key:
        print("❌ ALPHA_VANTAGE_KEY not set in .env")
        return False
    
    if not fred_key:
        print("❌ FRED_API_KEY not set in .env")
        return False
    
    print(f"✅ API keys configured")
    print(f"   Alpha Vantage: {av_key[:10]}...")
    print(f"   FRED: {fred_key[:10]}...")
    return True


async def test_data_fetcher():
    """Test data fetcher"""
    from data_fetcher import EnhancedDataFetcher
    
    async with EnhancedDataFetcher() as fetcher:
        data = await fetcher.fetch_forex_data('EURUSD')
        
        if data is None:
            print("❌ Failed to fetch data")
            return False
        
        if len(data) < 100:
            print(f"⚠️  Only {len(data)} data points (expected 100+)")
            return False
        
        print(f"✅ Fetched {len(data)} data points")
        print(f"   Latest: {data.index[-1].date()} - Close: {data['close'].iloc[-1]:.5f}")
        return True


def test_strategy():
    """Test optimized strategy"""
    from optimized_strategy import OptimizedStrategy
    import pandas as pd
    import numpy as np
    
    # Generate sample data
    np.random.seed(42)
    dates = pd.date_range(start='2023-01-01', periods=252, freq='D')
    prices = 100 * (1 + np.random.randn(252) * 0.015).cumprod()
    
    data = pd.DataFrame({
        'open': prices,
        'high': prices * 1.01,
        'low': prices * 0.99,
        'close': prices,
        'volume': np.random.randint(1000, 10000, 252)
    }, index=dates)
    
    strategy = OptimizedStrategy()
    signals = strategy.generate_signals(data)
    
    if signals is None or len(signals) == 0:
        print("❌ Strategy failed to generate signals")
        return False
    
    buy_signals = (signals == 1).sum()
    sell_signals = (signals == -1).sum()
    
    print(f"✅ Strategy generated signals")
    print(f"   Buy signals: {buy_signals}")
    print(f"   Sell signals: {sell_signals}")
    return True


def test_ml_models():
    """Test ML models"""
    from advanced_ml_models import AdvancedMLEnsemble
    import pandas as pd
    import numpy as np
    
    # Generate sample data
    np.random.seed(42)
    dates = pd.date_range(start='2023-01-01', periods=252, freq='D')
    prices = 100 * (1 + np.random.randn(252) * 0.015).cumprod()
    
    data = pd.DataFrame({
        'open': prices,
        'high': prices * 1.01,
        'low': prices * 0.99,
        'close': prices,
        'volume': np.random.randint(1000, 10000, 252)
    }, index=dates)
    
    ensemble = AdvancedMLEnsemble()
    X, y, features = ensemble.prepare_data(data)
    
    if len(X) == 0:
        print("❌ Failed to create features")
        return False
    
    print(f"✅ Created {len(features)} features")
    print(f"   Dataset size: {len(X)} samples")
    
    # Train models
    split_idx = int(len(X) * 0.8)
    ensemble.train_ensemble(X.iloc[:split_idx], y.iloc[:split_idx])
    
    print(f"✅ Trained {len(ensemble.models)} models")
    return True


def test_file_structure():
    """Test that all required files exist"""
    required_files = [
        'data_fetcher.py',
        'optimized_strategy.py',
        'advanced_ml_models.py',
        'perfect_bot.py',
        'README.md',
        'requirements.txt'
    ]
    
    missing = []
    for file in required_files:
        if not Path(file).exists():
            missing.append(file)
    
    if missing:
        print(f"❌ Missing files: {', '.join(missing)}")
        return False
    
    print(f"✅ All required files present")
    return True


def test_logs_directory():
    """Test logs directory"""
    logs_dir = Path('logs')
    
    if not logs_dir.exists():
        logs_dir.mkdir()
        print("✅ Created logs directory")
    else:
        print("✅ Logs directory exists")
    
    return True


async def run_all_tests():
    """Run all tests"""
    tester = PerfectBotTester()
    
    print("="*70)
    print("PERFECT BOT - COMPREHENSIVE TEST SUITE")
    print("="*70)
    print("\nTesting all components...")
    
    # Synchronous tests
    tester.test("File Structure", test_file_structure)
    tester.test("Core Imports", test_imports)
    tester.test("Advanced ML Imports", test_advanced_ml_imports)
    tester.test("Environment Configuration", test_env_file)
    tester.test("Logs Directory", test_logs_directory)
    tester.test("Optimized Strategy", test_strategy)
    tester.test("ML Models", test_ml_models)
    
    # Async tests
    await tester.test_async("Data Fetcher", test_data_fetcher)
    
    # Print summary
    tester.print_summary()
    
    return tester.tests_failed == 0


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
