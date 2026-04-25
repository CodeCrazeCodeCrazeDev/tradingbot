"""
Comprehensive Test Suite for Phases 2, 3, and 4
Tests all implemented components for evolution enhancements, evaluation improvements, and execution optimization.
"""

import asyncio
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "trading_bot"))

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(name)s] %(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


# ==================== PHASE 2: EVOLUTION ENHANCEMENTS ====================

async def test_speciated_evolution_engine():
    """Test speciated evolution engine with diversity preservation"""
    print("\n=== Testing SpeciatedEvolutionEngine ===")
    
    from trading_bot.alpha_evolve.speciated_evolution_engine import (
        SpeciatedEvolutionEngine, Species, SpeciationConfig
    )
    from trading_bot.alpha_evolve.strategy_genome import (
        StrategyGenome, Signal, SignalType, AggregationType,
        PositionSizingType, RiskControl, ExecutionParams, SearchSpace
    )
    from trading_bot.alpha_evolve.genetic_operators import GeneticOperators
    from trading_bot.alpha_evolve.fitness_evaluator import MultiObjectiveFitness
    from trading_bot.alpha_evolve.backtesting_engine import LeakageFreeBacktester
    
    # Create search space
    search_space = SearchSpace()
    
    # Create genetic operators
    genetic_ops = GeneticOperators(search_space, mutation_rate=0.1)
    
    # Create mock backtester
    dates = pd.date_range(start='2023-01-01', end='2023-03-01', freq='D')
    mock_data = pd.DataFrame({
        'open': np.random.normal(1.1000, 0.01, len(dates)),
        'high': np.random.normal(1.1010, 0.01, len(dates)),
        'low': np.random.normal(1.0990, 0.01, len(dates)),
        'close': np.random.normal(1.1005, 0.01, len(dates)),
        'volume': np.random.randint(1000, 10000, len(dates))
    }, index=dates)
    
    backtester = LeakageFreeBacktester(mock_data)
    fitness_evaluator = MultiObjectiveFitness()
    
    # Create speciated evolution engine
    from trading_bot.alpha_evolve.evolution_engine import EvolutionConfig
    config = EvolutionConfig(
        population_size=20,
        mutation_rate=0.1,
        elite_size=2,
        crossover_rate=0.7
    )
    
    engine = SpeciatedEvolutionEngine(
        search_space=search_space,
        backtester=backtester,
        fitness_evaluator=fitness_evaluator,
        genetic_operators=genetic_ops,
        config=config
    )
    
    # Create initial population
    population = []
    for i in range(20):
        strategy = StrategyGenome(
            signals=[Signal(
                signal_type=np.random.choice(list(SignalType)),
                lookback_period=np.random.randint(5, 50),
                threshold=np.random.uniform(-1, 1),
                weight=np.random.uniform(0.5, 1.5)
            )],
            aggregation_type=AggregationType.LINEAR,
            position_sizing=PositionSizingType.FIXED,
            risk_control=RiskControl(),
            execution_params=ExecutionParams()
        )
        from trading_bot.alpha_evolve.evolution_engine import Individual
        population.append(Individual(genome=strategy, generation=0))
    
    engine.population = population
    
    # Test speciation
    engine._speciate_population(population, generation=0)
    
    print(f"✓ Speciation: Created {len(engine.species)} species from {len(population)} individuals")
    
    # Test species info
    info = engine.get_species_info()
    print(f"✓ Species info: {info['species_count']} species, {info['total_population']} total population")
    
    # Test compatibility distance
    if len(population) >= 2:
        dist = engine._compatibility_distance(population[0].genome, population[1].genome)
        print(f"✓ Compatibility distance: {dist:.4f}")
    
    return True


async def test_diversity_selector():
    """Test diversity-aware selection mechanisms"""
    print("\n=== Testing DiversitySelector ===")
    
    from trading_bot.alpha_evolve.diversity_selection import (
        DiversitySelector, DiversityMetrics, AgeBasedSelector, MultiObjectiveSelector
    )
    from trading_bot.alpha_evolve.evolution_engine import Individual
    from trading_bot.alpha_evolve.fitness_evaluator import FitnessScore
    from trading_bot.alpha_evolve.strategy_genome import (
        StrategyGenome, Signal, SignalType, AggregationType,
        PositionSizingType, RiskControl, ExecutionParams
    )
    
    # Create test population
    population = []
    for i in range(10):
        strategy = StrategyGenome(
            signals=[Signal(
                signal_type=SignalType.MOMENTUM if i % 2 == 0 else SignalType.MEAN_REVERSION,
                lookback_period=10 + i * 5,
                threshold=0.5 + i * 0.1,
                weight=1.0
            )],
            aggregation_type=AggregationType.LINEAR,
            position_sizing=PositionSizingType.FIXED,
            risk_control=RiskControl(),
            execution_params=ExecutionParams()
        )
        ind = Individual(genome=strategy, generation=i)
        ind.fitness = FitnessScore(
            sharpe_ratio=1.0 + i * 0.1,
            max_drawdown=-0.1 - i * 0.01,
            regime_stability=0.8,
            tail_risk=0.05,
            complexity_penalty=0.01,
            total_fitness=1.0 + i * 0.1,
            metrics={'sharpe': 1.0 + i * 0.1}
        )
        population.append(ind)
    
    # Test DiversitySelector
    selector = DiversitySelector(diversity_threshold=0.3, diversity_weight=0.3)
    selected = selector.select_with_diversity(population, 5)
    print(f"✓ Diversity selection: Selected {len(selected)} individuals from {len(population)}")
    
    # Test diversity metrics
    metrics = selector._calculate_diversity_metrics(population)
    print(f"✓ Diversity metrics: phenotypic={metrics.phenotypic_diversity:.3f}, "
          f"genotypic={metrics.genotypic_diversity:.3f}")
    
    # Test AgeBasedSelector
    age_selector = AgeBasedSelector(max_age=10, age_fitness_decay=0.95)
    survivors = age_selector.select_survivors(population, 5)
    print(f"✓ Age-based selection: {len(survivors)} survivors")
    
    # Test MultiObjectiveSelector
    mo_selector = MultiObjectiveSelector(
        objectives=['sharpe_ratio', 'max_drawdown', 'regime_stability'],
        objective_weights=[0.5, 0.3, 0.2]
    )
    pareto = mo_selector.get_pareto_frontier(population)
    print(f"✓ Pareto frontier: {len(pareto)} non-dominated individuals")
    
    return True


# ==================== PHASE 3: EVALUATION IMPROVEMENTS ====================

async def test_regime_aware_backtester():
    """Test regime-aware backtesting with market regime detection"""
    print("\n=== Testing RegimeAwareBacktester ===")
    
    from trading_bot.alpha_evolve.regime_aware_backtester import (
        RegimeAwareBacktester, RegimeClassifier, MarketRegime,
        RegimeDetectionConfig, MonteCarloValidator
    )
    
    # Create test data with different regimes
    dates = pd.date_range(start='2023-01-01', end='2023-12-31', freq='D')
    
    # Create trending data for first 3 months
    trend_returns = np.random.normal(0.001, 0.01, 90)
    trend_cum = np.cumprod(1 + trend_returns)
    
    # Create volatile data for next 3 months
    volatile_returns = np.random.normal(0, 0.03, 90)
    volatile_cum = np.cumprod(1 + volatile_returns) * trend_cum[-1]
    
    # Create ranging data for last 6 months
    ranging_returns = np.random.normal(0, 0.008, 185)
    ranging_cum = np.cumprod(1 + ranging_returns) * volatile_cum[-1]
    
    prices = np.concatenate([trend_cum, volatile_cum, ranging_cum])
    
    mock_data = pd.DataFrame({
        'open': prices * 0.999,
        'high': prices * 1.002,
        'low': prices * 0.998,
        'close': prices,
        'volume': np.random.randint(1000, 10000, len(dates))
    }, index=dates)
    
    # Test regime classifier
    classifier = RegimeClassifier(RegimeDetectionConfig(lookback_period=20))
    regime = classifier.classify_regime(mock_data)
    print(f"✓ Regime classification: {regime.value}")
    
    # Test regime changes
    regime_changes = classifier.detect_regime_changes(mock_data)
    print(f"✓ Regime changes detected: {len(regime_changes)} changes")
    
    # Test Monte Carlo validator
    from trading_bot.alpha_evolve.backtesting_engine import BacktestResult, Trade
    
    returns = pd.Series(np.random.normal(0.001, 0.02, 252))
    result = BacktestResult(
        returns=returns,
        positions=pd.DataFrame(),
        trades=[Trade(
            timestamp=datetime.now(),
            symbol="EURUSD",
            side="buy",
            quantity=100000,
            price=1.1000,
            commission=10.0,
            slippage=5.0,
            market_impact=2.0,
            total_cost=17.0
        )],
        equity_curve=(1 + returns).cumprod(),
        metrics={'sharpe': 1.5},
        total_return=returns.sum(),
        sharpe_ratio=1.5,
        max_drawdown=0.1,
        win_rate=0.6,
        profit_factor=1.8,
        num_trades=10,
        avg_trade_duration=4.5,
        total_costs=17.0
    )
    
    mc_validator = MonteCarloValidator(num_simulations=100, confidence_level=0.95)
    mc_results = mc_validator.validate(result)
    print(f"✓ Monte Carlo validation: {mc_results['num_simulations']} simulations")
    print(f"  - Prob. of profit: {mc_results['prob_profit']:.1%}")
    print(f"  - Sharpe mean: {mc_results['sharpe_mean']:.3f}")
    
    return True


async def test_enhanced_fitness():
    """Test enhanced fitness evaluator with tail risk metrics"""
    print("\n=== Testing EnhancedFitnessEvaluator ===")
    
    from trading_bot.alpha_evolve.enhanced_fitness import (
        EnhancedFitnessEvaluator, EnhancedFitnessScore
    )
    from trading_bot.alpha_evolve.backtesting_engine import BacktestResult, Trade
    
    # Create backtest result with tail risk
    returns = pd.Series(np.concatenate([
        np.random.normal(0.001, 0.015, 240),  # Normal returns
        np.random.normal(-0.05, 0.02, 5),      # Tail events (crashes)
        np.random.normal(0.001, 0.015, 7)      # Recovery
    ]))
    
    result = BacktestResult(
        returns=returns,
        positions=pd.DataFrame(),
        trades=[],
        equity_curve=(1 + returns).cumprod(),
        metrics={'sharpe': 0.8},
        total_return=returns.sum(),
        sharpe_ratio=0.8,
        max_drawdown=0.25,
        win_rate=0.55,
        profit_factor=1.3,
        num_trades=50,
        avg_trade_duration=3.0,
        total_costs=100.0
    )
    
    # Test enhanced fitness evaluation
    evaluator = EnhancedFitnessEvaluator(
        risk_free_rate=0.02,
        target_sharpe=1.5,
        tail_risk_weight=0.25
    )
    
    fitness = evaluator.evaluate(result, complexity=5, regime_stability=0.7)
    print(f"✓ Enhanced fitness evaluation:")
    print(f"  - Total fitness: {fitness.total_fitness:.3f}")
    print(f"  - Sharpe: {fitness.sharpe_ratio:.3f}")
    print(f"  - VaR 95%: {fitness.var_95:.4f}")
    print(f"  - CVaR 95%: {fitness.cvar_95:.4f}")
    print(f"  - Sortino: {fitness.sortino_ratio:.3f}")
    print(f"  - Omega: {fitness.omega_ratio:.3f}")
    
    # Test tail risk report
    report = evaluator.get_tail_risk_report(result)
    print(f"✓ Tail risk report:")
    print(f"  - Skewness: {report['distribution']['skewness']:.3f}")
    print(f"  - Kurtosis: {report['distribution']['kurtosis']:.3f}")
    print(f"  - Tail events (99%): {report['tail_events']['count_99']}")
    
    return True


# ==================== PHASE 4: EXECUTION OPTIMIZATION ====================

async def test_liquidity_aware_sizer():
    """Test liquidity-aware position sizing"""
    print("\n=== Testing LiquidityAwareSizer ===")
    
    from trading_bot.execution.liquidity_aware_sizer import (
        LiquidityAwareSizer, MarketDepth, OrderBookLevel, ImpactModel
    )
    
    # Create order book
    bids = [
        OrderBookLevel(price=1.1000, size=100000, side='bid'),
        OrderBookLevel(price=1.0998, size=200000, side='bid'),
        OrderBookLevel(price=1.0995, size=300000, side='bid'),
    ]
    asks = [
        OrderBookLevel(price=1.1002, size=100000, side='ask'),
        OrderBookLevel(price=1.1005, size=200000, side='ask'),
        OrderBookLevel(price=1.1008, size=300000, side='ask'),
    ]
    
    market_depth = MarketDepth(
        symbol="EURUSD",
        timestamp=datetime.now(),
        bids=bids,
        asks=asks,
        spread=0.0002,
        mid_price=1.1001
    )
    
    # Test liquidity calculations
    liquidity = market_depth.get_liquidity_at_price(1.1000, 'buy')
    print(f"✓ Available liquidity at 1.1000: {liquidity:,.0f}")
    
    avg_price, slippage = market_depth.get_average_price_for_size(150000, 'buy')
    print(f"✓ Avg price for 150k: {avg_price:.4f} (slippage: {slippage:.2f} bps)")
    
    # Test liquidity-aware sizer
    sizer = LiquidityAwareSizer(
        max_participation_rate=0.05,
        max_impact_bps=10.0
    )
    
    decision = sizer.calculate_position_size(
        target_size=500000,
        symbol="EURUSD",
        market_depth=market_depth,
        daily_volume=10000000,
        volatility=0.02,
        side='buy'
    )
    
    print(f"✓ Sizing decision:")
    print(f"  - Target size: {decision['target_size']:,.0f}")
    print(f"  - Final size: {decision['final_size']:,.0f}")
    print(f"  - Constraints applied: {len(decision['constraints'])}")
    print(f"  - Participation rate: {decision['impact']['participation_rate']:.2%}")
    
    # Test impact model
    impact_model = ImpactModel()
    impact = impact_model.estimate_impact(500000, 10000000, 0.02)
    print(f"✓ Market impact estimate:")
    print(f"  - Temporary: {impact['temporary']:.4f}")
    print(f"  - Permanent: {impact['permanent']:.4f}")
    
    return True


async def test_advanced_execution_algorithms():
    """Test advanced execution algorithms with slippage minimization"""
    print("\n=== Testing Advanced Execution Algorithms ===")
    
    from trading_bot.execution.advanced_execution_algorithms import (
        SlippageMinimizer, AdaptiveExecutionEngine, DynamicParameterAdjuster,
        OrderType, ExecutionSlice
    )
    from trading_bot.execution.liquidity_aware_sizer import ExecutionTimingOptimizer
    
    # Test slippage minimizer
    minimizer = SlippageMinimizer(max_slices=5, toxicity_threshold=0.7)
    
    market_data = {
        'mid_price': 1.1000,
        'volume': 1000000,
        'volume_imbalance': 100000,
        'volatility': 0.02
    }
    
    slices = minimizer.calculate_optimal_slices(
        total_size=500000,
        time_horizon=timedelta(minutes=30),
        market_data=market_data
    )
    
    print(f"✓ Slippage minimizer: Created {len(slices)} order slices")
    print(f"  - First slice: {slices[0].size:,.0f} @ {slices[0].order_type.value}")
    
    # Test VPIN estimation
    vpin = minimizer._estimate_vpin(market_data)
    print(f"✓ VPIN estimate: {vpin:.3f}")
    
    # Test adaptive execution engine
    engine = AdaptiveExecutionEngine(benchmark='vwap', participation_cap=0.05)
    
    result = engine.execute(
        symbol="EURUSD",
        size=100000,
        side="buy",
        urgency="normal",
        market_conditions={
            'mid_price': 1.1000,
            'vwap': 1.1001,
            'volatility': 0.015,
            'daily_volume': 5000000,
            'spread': 0.0002
        }
    )
    
    print(f"✓ Adaptive execution:")
    print(f"  - Strategy: {result['strategy']}")
    print(f"  - Participation rate: {result['participation_rate']:.2%}")
    print(f"  - Target price: {result['target_price']:.4f}")
    
    # Test dynamic parameter adjuster
    adjuster = DynamicParameterAdjuster(learning_rate=0.1, exploration_rate=0.2)
    
    params = adjuster.get_parameters({'volatility': 0.02, 'spread': 0.0003})
    print(f"✓ Dynamic parameters:")
    print(f"  - Slices: {params['slices']}")
    print(f"  - Participation: {params['participation_rate']:.2%}")
    print(f"  - Limit order %: {params['limit_order_pct']:.1%}")
    
    # Test execution timing optimizer
    timing_opt = ExecutionTimingOptimizer()
    
    is_optimal, score = timing_opt.is_optimal_execution_time(
        current_volatility=0.015,
        current_hour=10,
        symbol="EURUSD"
    )
    
    print(f"✓ Execution timing:")
    print(f"  - Is optimal: {is_optimal}")
    print(f"  - Score: {score:.3f}")
    
    return True


# ==================== MAIN TEST RUNNER ====================

async def main():
    """Run all tests for Phases 2, 3, and 4"""
    print("="*70)
    print("PHASES 2, 3, 4 COMPREHENSIVE TEST SUITE")
    print("="*70)
    
    tests = [
        ("Phase 2 - Speciated Evolution Engine", test_speciated_evolution_engine),
        ("Phase 2 - Diversity Selection", test_diversity_selector),
        ("Phase 3 - Regime-Aware Backtester", test_regime_aware_backtester),
        ("Phase 3 - Enhanced Fitness", test_enhanced_fitness),
        ("Phase 4 - Liquidity-Aware Sizer", test_liquidity_aware_sizer),
        ("Phase 4 - Advanced Execution Algorithms", test_advanced_execution_algorithms),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            print(f"\n{'='*70}")
            result = await test_func()
            results.append((test_name, result, None))
            print(f"✓ {test_name}: PASSED")
        except Exception as e:
            results.append((test_name, False, str(e)))
            print(f"✗ {test_name}: FAILED - {e}")
            import traceback
            traceback.print_exc()
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    passed = sum(1 for _, result, _ in results if result)
    total = len(results)
    
    for test_name, result, error in results:
        status = "PASSED" if result else f"FAILED ({error})"
        symbol = "✓" if result else "✗"
        print(f"{symbol} {test_name}: {status}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n" + "="*70)
        print("✓ ALL PHASES 2, 3, 4 TESTS PASSED SUCCESSFULLY!")
        print("="*70)
        return 0
    else:
        print(f"\n✗ {total - passed} tests failed")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
