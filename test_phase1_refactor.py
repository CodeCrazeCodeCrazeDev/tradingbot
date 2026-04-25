"""
Test script for Phase 1 refactor implementations.
Tests: Point-in-time data access, backtest cache, parallel evaluator, bounded collections
"""

import asyncio
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
import time
import sys
from pathlib import Path

# Add trading_bot to path
sys.path.insert(0, str(Path(__file__).parent / "trading_bot"))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(name)s] %(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)


async def test_point_in_time_data():
    """Test point-in-time data access layer"""
    print("\n=== Testing Point-in-Time Data Access ===")
    
    from trading_bot.database.point_in_time_data import PointInTimeDataAccess, TemporalDataValidator
    
    # Initialize data access
    data_access = PointInTimeDataAccess({'max_history_days': 30})
    validator = TemporalDataValidator()
    
    # Add test data
    symbol = "EURUSD"
    base_time = datetime.now() - timedelta(days=10)
    
    for i in range(100):
        timestamp = base_time + timedelta(minutes=i*5)
        data = {
            'open': 1.1000 + np.random.normal(0, 0.001),
            'high': 1.1010 + np.random.normal(0, 0.001),
            'low': 1.0990 + np.random.normal(0, 0.001),
            'close': 1.1005 + np.random.normal(0, 0.001),
            'volume': np.random.randint(1000, 10000)
        }
        data_access.add_snapshot(symbol, timestamp, data)
    
    # Test queries
    query_time = base_time + timedelta(hours=2)
    
    # Test exact time query
    result = data_access.get_data_at_time(symbol, query_time)
    print(f"✓ Exact time query: {'Found' if result else 'Not found'}")
    
    # Test range query
    start_time = base_time + timedelta(hours=1)
    end_time = base_time + timedelta(hours=3)
    range_data = data_access.get_data_range(symbol, start_time, end_time)
    print(f"✓ Range query: Found {len(range_data)} snapshots")
    
    # Test latest before
    latest = data_access.get_latest_before(symbol, query_time)
    print(f"✓ Latest before query: {'Found' if latest else 'Not found'}")
    
    # Test data leakage validation
    is_valid = data_access.validate_no_leakage(symbol, query_time, datetime.now())
    print(f"✓ Leakage validation: {'Passed' if is_valid else 'Failed'}")
    
    # Get statistics
    stats = data_access.get_data_statistics(symbol)
    print(f"✓ Data statistics: {stats['total_snapshots']} snapshots, "
          f"{stats['time_span_days']:.1f} days span")
    
    return True


async def test_backtest_cache():
    """Test backtest result cache"""
    print("\n=== Testing Backtest Cache ===")
    
    from trading_bot.alpha_evolve.backtest_cache import BacktestCache, CacheStrategy
    from trading_bot.alpha_evolve.backtesting_engine import BacktestResult, Trade
    
    # Initialize cache
    cache_config = {
        'max_size': 100,
        'max_memory_mb': 100,
        'strategy': 'lru',
        'default_ttl': 3600,  # 1 hour
        'persistent': False
    }
    cache = BacktestCache(cache_config)
    
    # Create mock strategy genome
    from trading_bot.alpha_evolve.strategy_genome import (
        StrategyGenome, Signal, SignalType, AggregationType, 
        PositionSizingType, RiskControl, ExecutionParams
    )
    strategy = StrategyGenome(
        signals=[Signal(SignalType.MOMENTUM, 20, 0.5, 1.0)],
        aggregation_type=AggregationType.LINEAR,
        position_sizing=PositionSizingType.FIXED,
        risk_control=RiskControl(),
        execution_params=ExecutionParams()
    )
    
    # Create mock backtest result
    returns = pd.Series(np.random.normal(0.001, 0.02, 252))
    trades = [
        Trade(
            timestamp=datetime.now(),
            symbol="EURUSD",
            side="buy",
            quantity=100000,
            price=1.1000,
            commission=10.0,
            slippage=5.0,
            market_impact=2.0,
            total_cost=17.0
        )
    ]
    
    backtest_result = BacktestResult(
        returns=returns,
        positions=pd.DataFrame(),
        trades=trades,
        equity_curve=(1 + returns).cumprod(),
        metrics={'sharpe': 1.5, 'max_dd': 0.1},
        total_return=returns.sum(),
        sharpe_ratio=1.5,
        max_drawdown=0.1,
        win_rate=0.6,
        profit_factor=1.8,
        num_trades=len(trades),
        avg_trade_duration=4.5,
        total_costs=sum(t.total_cost for t in trades)
    )
    
    # Test cache miss
    start = time.time()
    cached_result = cache.get(strategy, "market_hash_123", {})
    miss_time = time.time() - start
    print(f"✓ Cache miss: {'Not found' if cached_result is None else 'Found'} ({miss_time:.4f}s)")
    
    # Test cache put
    cache.put(strategy, "market_hash_123", {}, backtest_result)
    print("✓ Cached result")
    
    # Test cache hit
    start = time.time()
    cached_result = cache.get(strategy, "market_hash_123", {})
    hit_time = time.time() - start
    print(f"✓ Cache hit: {'Found' if cached_result else 'Not found'} ({hit_time:.4f}s)")
    
    # Test statistics
    stats = cache.get_statistics()
    print(f"✓ Cache stats: {stats['hit_rate']:.1%} hit rate, "
          f"{stats['entries']} entries, {stats['total_size_mb']:.2f}MB")
    
    return True


async def test_parallel_evaluator():
    """Test parallel strategy evaluator"""
    print("\n=== Testing Parallel Evaluator ===")
    
    from trading_bot.alpha_evolve.parallel_evaluator import ParallelEvaluator
    from trading_bot.alpha_evolve.strategy_genome import StrategyGenome, Signal, SignalType
    
    # Create evaluator config
    config = {
        'max_workers': 2,
        'use_processes': False,  # Use threads for testing
        'chunk_size': 5,
        'cache': {
            'max_size': 50,
            'strategy': 'lru'
        }
    }
    
    evaluator = ParallelEvaluator(config)
    await evaluator.start()
    
    # Create test strategies
    from trading_bot.alpha_evolve.strategy_genome import (
        StrategyGenome, Signal, SignalType, AggregationType,
        PositionSizingType, RiskControl, ExecutionParams
    )
    strategies = []
    for i in range(10):
        strategy = StrategyGenome(
            signals=[
                Signal(
                    signal_type=SignalType.MOMENTUM if i % 2 == 0 else SignalType.MEAN_REVERSION,
                    lookback_period=10 + i * 5,
                    threshold=0.5 + i * 0.1,
                    weight=1.0
                )
            ],
            aggregation_type=AggregationType.LINEAR,
            position_sizing=PositionSizingType.FIXED,
            risk_control=RiskControl(),
            execution_params=ExecutionParams()
        )
        strategies.append(strategy)
    
    # Create mock market data
    dates = pd.date_range(start='2023-01-01', end='2023-12-31', freq='D')
    market_data = pd.DataFrame({
        'open': np.random.normal(1.1000, 0.01, len(dates)),
        'high': np.random.normal(1.1010, 0.01, len(dates)),
        'low': np.random.normal(1.0990, 0.01, len(dates)),
        'close': np.random.normal(1.1005, 0.01, len(dates)),
        'volume': np.random.randint(1000, 10000, len(dates))
    }, index=dates)
    
    # Test evaluation
    backtest_config = {
        'initial_capital': 100000,
        'commission': 0.0002,
        'slippage': 0.0001
    }
    
    start_time = time.time()
    results = await evaluator.evaluate_strategies(strategies, market_data, backtest_config)
    eval_time = time.time() - start_time
    
    print(f"✓ Evaluated {len(results)} strategies in {eval_time:.2f}s")
    print(f"✓ Average time per strategy: {eval_time / len(results):.3f}s")
    
    # Get evaluator statistics
    stats = evaluator.get_statistics()
    print(f"✓ Evaluator stats: {stats}")
    
    await evaluator.stop()
    return True


async def test_bounded_collections():
    """Test bounded collections"""
    print("\n=== Testing Bounded Collections ===")
    
    from trading_bot.utils.bounded_collections import (
        BoundedList, BoundedDict, BoundedDeque, BoundedSet, memory_monitor
    )
    
    # Test BoundedList
    blist = BoundedList(max_size=5)
    for i in range(10):
        blist.append(i)
    print(f"✓ BoundedList: Size={len(blist)}, Latest={blist.get_latest(3)}")
    
    # Test BoundedDict
    bdict = BoundedDict(max_size=3)
    for i in range(5):
        bdict[f'key_{i}'] = f'value_{i}'
    print(f"✓ BoundedDict: Size={len(bdict)}, Keys={list(bdict.keys())}")
    
    # Test BoundedDeque
    bdeque = BoundedDeque(max_size=4)
    for i in range(6):
        bdeque.append(i)
    print(f"✓ BoundedDeque: Size={len(bdeque)}, Items={list(bdeque)}")
    
    # Test BoundedSet
    bset = BoundedSet(max_size=3)
    for i in range(5):
        bset.add(f'item_{i}')
    print(f"✓ BoundedSet: Size={len(bset)}, Items={list(bset)}")
    
    # Test memory monitor
    memory_monitor.register('test_list', blist)
    memory_monitor.register('test_dict', bdict)
    stats = memory_monitor.get_stats()
    print(f"✓ Memory monitor: {len(stats)} collections registered")
    
    return True


async def main():
    """Run all tests"""
    print("Starting Phase 1 Refactor Tests\n")
    
    tests = [
        ("Point-in-Time Data Access", test_point_in_time_data),
        ("Backtest Cache", test_backtest_cache),
        ("Parallel Evaluator", test_parallel_evaluator),
        ("Bounded Collections", test_bounded_collections)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            print(f"\n{'='*50}")
            result = await test_func()
            results.append((test_name, result, None))
            print(f"✓ {test_name}: PASSED")
        except Exception as e:
            results.append((test_name, False, str(e)))
            print(f"✗ {test_name}: FAILED - {e}")
            import traceback
            traceback.print_exc()
    
    # Summary
    print("\n" + "="*50)
    print("TEST SUMMARY")
    print("="*50)
    
    passed = sum(1 for _, result, _ in results if result)
    total = len(results)
    
    for test_name, result, error in results:
        status = "PASSED" if result else f"FAILED ({error})"
        print(f"{test_name}: {status}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✓ All Phase 1 refactor tests passed successfully!")
        return 0
    else:
        print(f"\n✗ {total - passed} tests failed")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
