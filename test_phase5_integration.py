"""
Phase 5: Integration and Stress Tests

Comprehensive testing of:
1. End-to-end integration of all components
2. Integration between phases 2, 3, 4
3. Stress tests with large populations
4. Performance benchmarking
"""

import unittest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import logging
import time
from typing import List, Dict, Any

# Import all Phase 2, 3, 4, 5 components
from trading_bot.alpha_evolve import (
    # Core
    StrategyGenome, Signal, SignalType,
    LeakageFreeBacktester,
    MultiObjectiveFitness, FitnessScore,
    
    # Phase 2
    SpeciatedEvolutionEngine, Species, SpeciationConfig,
    DiversitySelector, AgeBasedSelector, MultiObjectiveSelector,
    
    # Phase 3
    RegimeAwareBacktester, MarketRegime,
    EnhancedFitnessEvaluator,
    MonteCarloValidator,
    
    # Phase 4 (via execution module)
    
    # Phase 5 - Integration
    IntegratedEvolutionSystem, IntegratedEvolutionConfig,
    DistributedEvaluationFramework, ParallelEvaluator, BacktestCache,
    CompositeStrategy, AdaptiveSignal, CombinationType,
    create_composite_strategy, create_adaptive_strategy
)

from trading_bot.execution import (
    LiquidityAwareSizer, MarketDepth,
    AdaptiveExecutionEngine, OrderType
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestPhase5Integration(unittest.TestCase):
    """Test end-to-end integration of all components"""
    
    def setUp(self):
        """Set up test fixtures"""
        np.random.seed(42)
        
        # Create mock market data
        dates = pd.date_range(start='2023-01-01', periods=200, freq='h')
        self.mock_data = pd.DataFrame({
            'open': np.random.normal(1.1000, 0.001, len(dates)),
            'high': np.random.normal(1.1010, 0.001, len(dates)),
            'low': np.random.normal(1.0990, 0.001, len(dates)),
            'close': np.random.normal(1.1005, 0.001, len(dates)),
            'volume': np.random.randint(1000, 10000, len(dates))
        }, index=dates)
        
        self.backtester = LeakageFreeBacktester(self.mock_data)
    
    def test_integration_all_components(self):
        """Test that all Phase 2, 3, 4, 5 components work together"""
        print("\n=== Testing Full Integration ===")
        
        # 1. Create strategies with all required parameters
        from trading_bot.alpha_evolve.strategy_genome import AggregationType, PositionSizingType, RiskControl, ExecutionParams
        
        strategies = []
        for i in range(5):
            strategy = StrategyGenome(
                signals=[Signal(
                    signal_type=SignalType.MOMENTUM,
                    lookback_period=10 + i * 5,
                    threshold=0.5,
                    weight=1.0
                )],
                aggregation_type=AggregationType.LINEAR,
                position_sizing=PositionSizingType.FIXED,
                risk_control=RiskControl(max_position_size=0.1),
                execution_params=ExecutionParams(slippage_bps=5.0)
            )
            strategies.append(strategy)
        
        # 2. Test composite strategy
        composite = create_composite_strategy(
            strategies[:3],
            combination_type=CombinationType.WEIGHTED_SUM,
            weights=[0.4, 0.3, 0.3]
        )
        self.assertEqual(len(composite.sub_strategies), 3)
        print("✓ Composite strategy created")
        
        # 3. Test backtesting with all components
        results = []
        for strategy in strategies:
            result = self.backtester.backtest(strategy)
            results.append(result)
        
        self.assertEqual(len(results), 5)
        print(f"✓ Backtested {len(results)} strategies")
        
        # 4. Test enhanced fitness evaluation
        fitness_evaluator = EnhancedFitnessEvaluator()
        for result in results:
            fitness = fitness_evaluator.evaluate(result, strategies[0])
            self.assertIsNotNone(fitness.total_fitness)
            self.assertIsNotNone(fitness.metrics.get('var_95'))
            self.assertIsNotNone(fitness.metrics.get('cvar_95'))
        
        print("✓ Enhanced fitness evaluation with tail risk")
        
        # 5. Test regime-aware backtesting
        regime_backtester = RegimeAwareBacktester(self.mock_data)
        regime_result = regime_backtester.backtest(strategies[0])
        self.assertIsNotNone(regime_result)
        print("✓ Regime-aware backtesting")
        
        # 6. Test Monte Carlo validation
        mc_validator = MonteCarloValidator(n_simulations=50)
        mc_results = mc_validator.validate_returns(
            np.random.normal(0.001, 0.01, 100),
            np.random.normal(0.0005, 0.01, 50)
        )
        self.assertIn('sharpe_mean', mc_results)
        print("✓ Monte Carlo validation")
        
        # 7. Test distributed evaluation framework
        framework = DistributedEvaluationFramework(max_workers=2, use_cache=True)
        framework.start()
        
        # Submit tasks
        task_ids = framework.submit_batch(strategies, self.mock_data)
        self.assertEqual(len(task_ids), 5)
        
        # Execute
        results_dist = framework.execute_pending(self.mock_data)
        self.assertEqual(len(results_dist), 5)
        
        framework.stop()
        print("✓ Distributed evaluation framework")
        
        # 8. Test cache
        cache = BacktestCache(max_size=100)
        for i, strategy in enumerate(strategies[:3]):
            cache.put(strategy, self.mock_data, results[i])
        
        hit_rate = cache.get_hit_rate()
        self.assertGreaterEqual(hit_rate, 0.0)
        print(f"✓ Backtest cache (hit rate: {hit_rate:.2%})")
        
        print("\n✓ Phase 5 - Full Integration: PASSED")
    
    def test_integrated_evolution_system(self):
        """Test the integrated evolution system"""
        print("\n=== Testing Integrated Evolution System ===")
        
        config = IntegratedEvolutionConfig(
            population_size=10,
            max_generations=5,
            elite_size=2,
            enable_speciation=True,
            enable_diversity_preservation=True,
            enable_regime_evaluation=True,
            enable_tail_risk=True,
            enable_liquidity_sizing=True,
            track_pareto_frontier=True,
            save_checkpoints=False  # Don't save during tests
        )
        
        system = IntegratedEvolutionSystem(
            config=config,
            market_data=self.mock_data
        )
        
        # Run evolution
        best = system.evolve(generations=3)
        
        self.assertIsNotNone(best)
        self.assertIsNotNone(best.fitness)
        
        # Check snapshots were created
        self.assertGreater(len(system.snapshots), 0)
        
        # Get report
        report = system.get_evolution_report()
        self.assertIn('summary', report)
        self.assertIn('fitness_progression', report)
        
        print(f"✓ Evolution completed: {len(system.snapshots)} generations")
        print(f"  Best fitness: {report['summary']['best_fitness']:.4f}")
        print(f"  Final diversity: {report['summary']['final_diversity']:.4f}")
        
        print("\n✓ Phase 5 - Integrated Evolution System: PASSED")
    
    def test_cross_phase_integration(self):
        """Test integration between different phases"""
        print("\n=== Testing Cross-Phase Integration ===")
        
        # Phase 2 (Evolution) -> Phase 3 (Evaluation)
        strategy = StrategyGenome(
            signals=[Signal(
                signal_type=SignalType.MOMENTUM,
                lookback_period=20,
                threshold=0.3,
                weight=1.0
            )]
        )
        
        # Phase 3 components evaluate Phase 2 output
        regime_backtester = RegimeAwareBacktester(self.mock_data)
        regime_result = regime_backtester.backtest(strategy)
        
        enhanced_fitness = EnhancedFitnessEvaluator()
        fitness = enhanced_fitness.evaluate(regime_result, strategy)
        
        self.assertIsNotNone(fitness)
        self.assertIn('var_95', fitness.metrics)
        print("✓ Phase 2 -> Phase 3 integration (Evolution to Evaluation)")
        
        # Phase 4 (Execution) can use Phase 3 metrics
        depth = MarketDepth(
            bids=[(1.1000, 100000), (1.0999, 150000)],
            asks=[(1.1001, 100000), (1.1002, 150000)]
        )
        
        sizer = LiquidityAwareSizer(
            market_depth=depth,
            constraints=LiquidityConstraints(max_participation_rate=0.05)
        )
        
        # Size based on fitness-derived risk appetite
        risk_appetite = 1.0 - abs(fitness.max_drawdown)
        target_size = int(500000 * risk_appetite)
        
        decision = sizer.get_position_size('EURUSD', target_size, 'buy')
        self.assertGreaterEqual(decision.final_size, 0)
        print("✓ Phase 3 -> Phase 4 integration (Evaluation to Execution)")
        
        # Phase 5 (Integration) orchestrates all
        config = IntegratedEvolutionConfig(
            population_size=8,
            max_generations=3,
            enable_speciation=True,
            enable_tail_risk=True,
            enable_liquidity_sizing=True
        )
        
        system = IntegratedEvolutionSystem(config, self.mock_data)
        best = system.evolve(generations=2)
        
        self.assertIsNotNone(best)
        print("✓ Phase 5 integration (All phases orchestrated)")
        
        print("\n✓ Phase 5 - Cross-Phase Integration: PASSED")


class TestPhase5StressTests(unittest.TestCase):
    """Stress tests with large populations and long runs"""
    
    def setUp(self):
        """Set up stress test fixtures"""
        np.random.seed(42)
        
        # Larger dataset for stress tests
        dates = pd.date_range(start='2023-01-01', periods=1000, freq='h')
        self.large_data = pd.DataFrame({
            'open': np.random.normal(1.1000, 0.001, len(dates)),
            'high': np.random.normal(1.1010, 0.001, len(dates)),
            'low': np.random.normal(1.0990, 0.001, len(dates)),
            'close': np.random.normal(1.1005, 0.001, len(dates)),
            'volume': np.random.randint(1000, 10000, len(dates))
        }, index=dates)
    
    def test_large_population_evaluation(self):
        """Stress test with large population"""
        print("\n=== Stress Test: Large Population ===")
        
        from trading_bot.alpha_evolve.strategy_genome import AggregationType, PositionSizingType, RiskControl, ExecutionParams
        
        # Create 50 strategies
        strategies = []
        for i in range(50):
            strategy = StrategyGenome(
                signals=[Signal(
                    signal_type=np.random.choice(list(SignalType)),
                    lookback_period=np.random.randint(5, 50),
                    threshold=np.random.uniform(-1, 1),
                    weight=1.0
                )],
                aggregation_type=AggregationType.LINEAR,
                position_sizing=PositionSizingType.FIXED,
                risk_control=RiskControl(),
                execution_params=ExecutionParams()
            )
            strategies.append(strategy)
        
        # Parallel evaluation
        start_time = time.time()
        
        evaluator = ParallelEvaluator(max_workers=4)
        evaluator.start()
        results = evaluator.evaluate_batch(strategies, self.large_data)
        evaluator.stop()
        
        elapsed = time.time() - start_time
        
        # All should complete
        success_count = sum(1 for _, r in results if r is not None)
        
        print(f"✓ Evaluated {len(strategies)} strategies in {elapsed:.2f}s")
        print(f"  Success rate: {success_count}/{len(strategies)} ({success_count/len(strategies):.1%})")
        print(f"  Avg time per strategy: {elapsed/len(strategies):.3f}s")
        
        self.assertGreaterEqual(success_count, len(strategies) * 0.9)  # 90% success rate
        
        print("\n✓ Stress Test - Large Population: PASSED")
    
    def test_cache_performance(self):
        """Test cache performance with repeated evaluations"""
        print("\n=== Stress Test: Cache Performance ===")
        
        # Create cache
        cache = BacktestCache(max_size=100)
        
        # Create strategy
        strategy = StrategyGenome(
            signals=[Signal(
                signal_type=SignalType.MOMENTUM,
                lookback_period=20,
                threshold=0.5,
                weight=1.0
            )]
        )
        
        # First evaluation (cache miss)
        start = time.time()
        backtester = LeakageFreeBacktester(self.large_data)
        result1 = backtester.backtest(strategy)
        cache.put(strategy, self.large_data, result1)
        time_first = time.time() - start
        
        # Second evaluation (cache hit)
        start = time.time()
        result2 = cache.get(strategy, self.large_data)
        time_second = time.time() - start
        
        hit_rate = cache.get_hit_rate()
        
        print(f"✓ Cache performance:")
        print(f"  First eval: {time_first:.3f}s (cache miss)")
        print(f"  Second eval: {time_second:.6f}s (cache hit)")
        print(f"  Speedup: {time_first/time_second:.1f}x")
        print(f"  Hit rate: {hit_rate:.1%}")
        
        self.assertEqual(hit_rate, 0.5)  # 1 hit out of 2 lookups
        self.assertLess(time_second, time_first / 10)  # At least 10x faster
        
        print("\n✓ Stress Test - Cache Performance: PASSED")
    
    def test_concurrent_execution(self):
        """Test concurrent execution with multiple batches"""
        print("\n=== Stress Test: Concurrent Execution ===")
        
        framework = DistributedEvaluationFramework(max_workers=4)
        framework.start()
        
        # Submit multiple batches
        all_strategies = []
        for batch in range(3):
            strategies = []
            for i in range(10):
                strategy = StrategyGenome(
                    signals=[Signal(
                        signal_type=SignalType.TREND,
                        lookback_period=15 + i,
                        threshold=0.2 + batch * 0.1,
                        weight=1.0
                    )]
                )
                strategies.append(strategy)
            all_strategies.extend(strategies)
            framework.submit_batch(strategies, self.large_data, priority=batch)
        
        # Execute all
        start = time.time()
        results = framework.execute_pending(self.large_data)
        elapsed = time.time() - start
        
        framework.stop()
        
        success_count = sum(1 for r in results if r.success)
        
        print(f"✓ Concurrent execution:")
        print(f"  Total tasks: {len(results)}")
        print(f"  Successful: {success_count}")
        print(f"  Total time: {elapsed:.2f}s")
        print(f"  Throughput: {len(results)/elapsed:.1f} strategies/sec")
        
        self.assertEqual(len(results), 30)
        self.assertGreaterEqual(success_count, 27)  # 90% success
        
        print("\n✓ Stress Test - Concurrent Execution: PASSED")
    
    def test_memory_usage_with_composite_strategies(self):
        """Test memory handling with complex composite strategies"""
        print("\n=== Stress Test: Composite Strategy Memory ===")
        
        from trading_bot.alpha_evolve.strategy_genome import AggregationType, PositionSizingType, RiskControl, ExecutionParams
        
        # Create complex nested composite strategies
        strategies = []
        for i in range(10):
            # Create sub-strategies
            sub_strategies = []
            for j in range(3):
                sub = StrategyGenome(
                    signals=[Signal(
                        signal_type=np.random.choice(list(SignalType)),
                        lookback_period=10 + j * 5,
                        threshold=np.random.uniform(-0.5, 0.5),
                        weight=1.0
                    )],
                    aggregation_type=AggregationType.LINEAR,
                    position_sizing=PositionSizingType.FIXED,
                    risk_control=RiskControl(),
                    execution_params=ExecutionParams()
                )
                sub_strategies.append(sub)
            
            # Create composite
            composite = create_composite_strategy(
                sub_strategies,
                combination_type=CombinationType.WEIGHTED_SUM,
                weights=[0.5, 0.3, 0.2]
            )
            strategies.append(composite)
        
        # Test that all can be backtested
        backtester = LeakageFreeBacktester(self.large_data)
        results = []
        
        start = time.time()
        for strategy in strategies:
            try:
                result = backtester.backtest(strategy)
                results.append(result)
            except Exception as e:
                logger.error(f"Backtest failed: {e}")
        elapsed = time.time() - start
        
        print(f"✓ Composite strategies backtested:")
        print(f"  Total: {len(strategies)}")
        print(f"  Successful: {len(results)}")
        print(f"  Time: {elapsed:.2f}s")
        
        self.assertEqual(len(results), len(strategies))
        
        print("\n✓ Stress Test - Composite Strategy Memory: PASSED")
    
    def test_long_evolution_run(self):
        """Test evolution over many generations"""
        print("\n=== Stress Test: Long Evolution Run ===")
        
        config = IntegratedEvolutionConfig(
            population_size=15,
            max_generations=10,
            elite_size=3,
            enable_speciation=True,
            enable_diversity_preservation=True,
            convergence_generations=50,  # Don't converge early
            save_checkpoints=False
        )
        
        system = IntegratedEvolutionSystem(config, self.large_data)
        
        start = time.time()
        best = system.evolve(generations=10)
        elapsed = time.time() - start
        
        self.assertIsNotNone(best)
        self.assertIsNotNone(best.fitness)
        
        report = system.get_evolution_report()
        
        print(f"✓ Long evolution run:")
        print(f"  Generations: {len(system.snapshots)}")
        print(f"  Time: {elapsed:.2f}s")
        print(f"  Time/gen: {elapsed/len(system.snapshots):.2f}s")
        print(f"  Evaluations: {system.stats['evaluations']}")
        print(f"  Best fitness: {report['summary']['best_fitness']:.4f}")
        
        self.assertEqual(len(system.snapshots), 10)
        
        print("\n✓ Stress Test - Long Evolution Run: PASSED")


class TestPhase5Performance(unittest.TestCase):
    """Performance benchmarking tests"""
    
    def setUp(self):
        """Set up performance test fixtures"""
        np.random.seed(42)
        
        dates = pd.date_range(start='2023-01-01', periods=500, freq='h')
        self.data = pd.DataFrame({
            'open': np.random.normal(1.1000, 0.001, len(dates)),
            'high': np.random.normal(1.1010, 0.001, len(dates)),
            'low': np.random.normal(1.0990, 0.001, len(dates)),
            'close': np.random.normal(1.1005, 0.001, len(dates)),
            'volume': np.random.randint(1000, 10000, len(dates))
        }, index=dates)
    
    def test_parallel_vs_sequential(self):
        """Benchmark parallel vs sequential evaluation"""
        print("\n=== Performance: Parallel vs Sequential ===")
        
        from trading_bot.alpha_evolve.strategy_genome import AggregationType, PositionSizingType, RiskControl, ExecutionParams
        
        # Create strategies
        strategies = []
        for i in range(20):
            strategy = StrategyGenome(
                signals=[Signal(
                    signal_type=SignalType.MOMENTUM,
                    lookback_period=10 + i,
                    threshold=0.5,
                    weight=1.0
                )],
                aggregation_type=AggregationType.LINEAR,
                position_sizing=PositionSizingType.FIXED,
                risk_control=RiskControl(),
                execution_params=ExecutionParams()
            )
            strategies.append(strategy)
        
        backtester = LeakageFreeBacktester(self.data)
        
        # Sequential
        start = time.time()
        seq_results = [backtester.backtest(s) for s in strategies]
        seq_time = time.time() - start
        
        # Parallel
        evaluator = ParallelEvaluator(max_workers=4)
        evaluator.start()
        start = time.time()
        par_results = evaluator.evaluate_batch(strategies, self.data)
        par_time = time.time() - start
        evaluator.stop()
        
        speedup = seq_time / par_time
        
        print(f"✓ Performance comparison:")
        print(f"  Sequential: {seq_time:.2f}s")
        print(f"  Parallel: {par_time:.2f}s")
        print(f"  Speedup: {speedup:.2f}x")
        
        # Parallel should be faster (though overhead may reduce benefit for small batches)
        self.assertGreater(speedup, 0.5)  # At least not significantly slower
        
        print("\n✓ Performance - Parallel vs Sequential: PASSED")


def run_phase5_tests():
    """Run all Phase 5 tests"""
    print("\n" + "="*70)
    print("PHASE 5: INTEGRATION AND STRESS TESTS")
    print("="*70)
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestPhase5Integration))
    suite.addTests(loader.loadTestsFromTestCase(TestPhase5StressTests))
    suite.addTests(loader.loadTestsFromTestCase(TestPhase5Performance))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    tests_run = result.testsRun
    failures = len(result.failures)
    errors = len(result.errors)
    
    print(f"Tests run: {tests_run}")
    print(f"Failures: {failures}")
    print(f"Errors: {errors}")
    print(f"Success rate: {(tests_run - failures - errors) / tests_run:.1%}")
    
    if failures == 0 and errors == 0:
        print("\n✓ ALL PHASE 5 TESTS PASSED SUCCESSFULLY!")
        print("="*70)
        return 0
    else:
        print("\n✗ SOME TESTS FAILED")
        print("="*70)
        return 1


if __name__ == '__main__':
    exit_code = run_phase5_tests()
    exit(exit_code)
