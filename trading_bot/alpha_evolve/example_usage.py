"""
AlphaEvolve Example Usage: Complete demonstration of the self-evolving
edge discovery and capital allocation engine.

This example shows how to:
1. Set up the evolution engine
2. Run strategy discovery
3. Monitor edge decay
4. Deploy strategies to production
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import logging

from strategy_genome import StrategyGenome, SearchSpace
from genetic_operators import GeneticOperators
from backtesting_engine import LeakageFreeBacktester
from fitness_evaluator import MultiObjectiveFitness
from walk_forward import WalkForwardValidator
from evolution_engine import EvolutionEngine, EvolutionConfig
from edge_monitor import EdgeDecayMonitor
from distributed_compute import DistributedComputeOrchestrator


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def generate_sample_market_data(days: int = 1000) -> pd.DataFrame:
    """
    Generate sample market data for demonstration.
    
    In production, replace this with real market data from your data provider.
    """
    logger.info(f"Generating {days} days of sample market data...")
    
    dates = pd.date_range(end=datetime.now(), periods=days, freq='D')
    
    np.random.seed(42)
    returns = np.random.normal(0.0005, 0.02, days)
    
    prices = 100 * np.exp(np.cumsum(returns))
    
    volatility = np.random.uniform(0.8, 1.2, days)
    
    data = pd.DataFrame({
        'open': prices * np.random.uniform(0.99, 1.01, days),
        'high': prices * np.random.uniform(1.00, 1.02, days),
        'low': prices * np.random.uniform(0.98, 1.00, days),
        'close': prices,
        'volume': np.random.uniform(1e6, 5e6, days),
    }, index=dates)
    
    data['returns'] = data['close'].pct_change()
    
    logger.info("Sample data generated successfully")
    return data


def example_basic_evolution():
    """
    Example 1: Basic evolution with default settings.
    
    This demonstrates the simplest way to discover trading strategies.
    """
    logger.info("\n" + "="*80)
    logger.info("EXAMPLE 1: Basic Evolution")
    logger.info("="*80)
    
    market_data = generate_sample_market_data(days=1000)
    
    config = EvolutionConfig(
        population_size=50,
        elite_size=5,
        max_generations=20,
        parallel_workers=4,
        save_directory="results/basic_evolution"
    )
    
    search_space = SearchSpace()
    
    engine = EvolutionEngine(
        config=config,
        search_space=search_space,
        market_data=market_data
    )
    
    best_strategy = engine.evolve()
    
    logger.info("\n" + "-"*80)
    logger.info("EVOLUTION COMPLETE")
    logger.info("-"*80)
    logger.info(f"Best Strategy ID: {best_strategy.get_id()}")
    logger.info(f"Best Fitness: {best_strategy.fitness.total_fitness:.4f}")
    logger.info(f"Sharpe Ratio: {best_strategy.fitness.sharpe_ratio:.4f}")
    logger.info(f"Max Drawdown: {best_strategy.fitness.max_drawdown:.4f}")
    logger.info(f"Number of Signals: {len(best_strategy.genome.signals)}")
    
    return best_strategy


def example_advanced_evolution():
    """
    Example 2: Advanced evolution with walk-forward validation.
    
    This demonstrates rigorous out-of-sample testing.
    """
    logger.info("\n" + "="*80)
    logger.info("EXAMPLE 2: Advanced Evolution with Walk-Forward Validation")
    logger.info("="*80)
    
    market_data = generate_sample_market_data(days=2000)
    
    config = EvolutionConfig(
        population_size=100,
        elite_size=10,
        tournament_size=5,
        mutation_rate=0.2,
        crossover_rate=0.8,
        max_generations=50,
        use_walkforward=True,
        walkforward_frequency=5,
        parallel_workers=8,
        save_directory="results/advanced_evolution"
    )
    
    search_space = SearchSpace()
    
    engine = EvolutionEngine(
        config=config,
        search_space=search_space,
        market_data=market_data
    )
    
    best_strategy = engine.evolve()
    
    logger.info("\n" + "-"*80)
    logger.info("WALK-FORWARD VALIDATION RESULTS")
    logger.info("-"*80)
    
    if best_strategy.walkforward_result:
        wf = best_strategy.walkforward_result
        logger.info(f"Train Fitness: {wf.avg_train_fitness:.4f}")
        logger.info(f"Test Fitness: {wf.avg_test_fitness:.4f}")
        logger.info(f"Fitness Degradation: {wf.fitness_degradation:.2%}")
        logger.info(f"Overfitting Score: {wf.overfitting_score:.4f}")
        logger.info(f"Statistically Significant: {wf.is_statistically_significant}")
        logger.info(f"P-value: {wf.p_value:.4f}")
    
    return best_strategy


def example_edge_monitoring():
    """
    Example 3: Monitor strategy edges for decay.
    
    This demonstrates how to detect when strategies stop working.
    """
    logger.info("\n" + "="*80)
    logger.info("EXAMPLE 3: Edge Decay Monitoring")
    logger.info("="*80)
    
    market_data = generate_sample_market_data(days=1000)
    
    search_space = SearchSpace()
    genome = search_space.random_genome()
    
    backtester = LeakageFreeBacktester(market_data)
    result = backtester.backtest(genome)
    
    baseline_performance = pd.DataFrame({
        'returns': result.returns,
        'pnl': result.returns * 100000
    })
    
    recent_data = generate_sample_market_data(days=90)
    recent_backtester = LeakageFreeBacktester(recent_data)
    recent_result = recent_backtester.backtest(genome)
    
    recent_performance = pd.DataFrame({
        'returns': recent_result.returns,
        'pnl': recent_result.returns * 100000
    })
    
    monitor = EdgeDecayMonitor(
        lookback_days=90,
        decay_threshold=0.3,
        significance_level=0.05
    )
    
    edge_status = monitor.monitor_strategy(
        genome_id=genome.get_genome_id(),
        recent_performance=recent_performance,
        baseline_performance=baseline_performance
    )
    
    logger.info("\n" + "-"*80)
    logger.info("EDGE MONITORING RESULTS")
    logger.info("-"*80)
    logger.info(f"Strategy ID: {edge_status.genome_id}")
    logger.info(f"Is Active: {edge_status.is_active}")
    logger.info(f"Days Since Deployment: {edge_status.days_since_deployment}")
    logger.info(f"Performance Trend: {edge_status.performance_trend}")
    logger.info(f"Recommendation: {edge_status.recommendation}")
    
    logger.info(f"\nBaseline Sharpe: {edge_status.baseline_metrics.sharpe_ratio:.4f}")
    logger.info(f"Current Sharpe: {edge_status.current_metrics.sharpe_ratio:.4f}")
    
    if edge_status.decay_signals:
        logger.info(f"\nDecay Signals Detected: {len(edge_status.decay_signals)}")
        for signal in edge_status.decay_signals:
            logger.info(f"  - {signal.signal_type}: {signal.description} (severity: {signal.severity:.2f})")
    
    return edge_status


def example_distributed_evolution():
    """
    Example 4: Distributed evolution for massive parallel search.
    
    This demonstrates scaling evolution across multiple workers.
    """
    logger.info("\n" + "="*80)
    logger.info("EXAMPLE 4: Distributed Evolution")
    logger.info("="*80)
    
    market_data = generate_sample_market_data(days=1500)
    
    def evaluation_function(genome: StrategyGenome, market_data: pd.DataFrame):
        """Custom evaluation function for distributed execution"""
        backtester = LeakageFreeBacktester(market_data)
        backtest_result = backtester.backtest(genome)
        
        fitness_evaluator = MultiObjectiveFitness()
        fitness = fitness_evaluator.evaluate(
            backtest_result,
            genome.get_complexity(),
            market_data
        )
        
        return {
            'fitness': fitness,
            'backtest_result': backtest_result
        }
    
    orchestrator = DistributedComputeOrchestrator(num_workers=8)
    
    search_space = SearchSpace()
    genomes = [search_space.random_genome() for _ in range(100)]
    
    logger.info(f"Evaluating {len(genomes)} strategies in parallel...")
    
    results = orchestrator.execute_parallel(
        genomes=genomes,
        evaluation_func=evaluation_function,
        market_data=market_data
    )
    
    valid_results = [r for r in results if r is not None]
    
    logger.info("\n" + "-"*80)
    logger.info("DISTRIBUTED EVALUATION RESULTS")
    logger.info("-"*80)
    logger.info(f"Total Strategies Evaluated: {len(genomes)}")
    logger.info(f"Successful Evaluations: {len(valid_results)}")
    
    if valid_results:
        fitnesses = [r['fitness'].total_fitness for r in valid_results]
        logger.info(f"Best Fitness: {max(fitnesses):.4f}")
        logger.info(f"Average Fitness: {np.mean(fitnesses):.4f}")
        logger.info(f"Worst Fitness: {min(fitnesses):.4f}")
    
    cluster_status = orchestrator.get_cluster_status()
    logger.info(f"\nCluster Throughput: {cluster_status.throughput:.2f} evaluations/hour")
    logger.info(f"Active Workers: {cluster_status.active_workers}/{cluster_status.total_capacity}")
    
    orchestrator.shutdown()
    
    return valid_results


def example_complete_workflow():
    """
    Example 5: Complete workflow from discovery to deployment.
    
    This demonstrates the full pipeline:
    1. Discover strategies through evolution
    2. Validate with walk-forward
    3. Monitor for edge decay
    4. Re-evolve when edges decay
    """
    logger.info("\n" + "="*80)
    logger.info("EXAMPLE 5: Complete Workflow")
    logger.info("="*80)
    
    market_data = generate_sample_market_data(days=2000)
    
    logger.info("\nSTEP 1: Initial Strategy Discovery")
    logger.info("-" * 40)
    
    config = EvolutionConfig(
        population_size=80,
        elite_size=8,
        max_generations=30,
        use_walkforward=True,
        parallel_workers=6,
        save_directory="results/complete_workflow"
    )
    
    search_space = SearchSpace()
    engine = EvolutionEngine(config, search_space, market_data)
    
    best_strategy = engine.evolve()
    
    logger.info(f"\nDiscovered Strategy:")
    logger.info(f"  Fitness: {best_strategy.fitness.total_fitness:.4f}")
    logger.info(f"  Sharpe: {best_strategy.fitness.sharpe_ratio:.4f}")
    
    logger.info("\nSTEP 2: Walk-Forward Validation")
    logger.info("-" * 40)
    
    validator = WalkForwardValidator(
        train_period_days=252,
        test_period_days=63,
        step_days=21
    )
    
    fitness_evaluator = MultiObjectiveFitness()
    wf_result = validator.validate(
        best_strategy.genome,
        market_data,
        fitness_evaluator
    )
    
    logger.info(f"  Out-of-Sample Sharpe: {wf_result.test_sharpe:.4f}")
    logger.info(f"  Overfitting Score: {wf_result.overfitting_score:.4f}")
    logger.info(f"  Consistency: {wf_result.consistency_score:.4f}")
    
    if wf_result.overfitting_score > 0.5:
        logger.warning("  WARNING: High overfitting detected!")
    
    logger.info("\nSTEP 3: Simulate Production Deployment")
    logger.info("-" * 40)
    
    deployment_data = market_data.iloc[-252:]
    backtester = LeakageFreeBacktester(deployment_data)
    deployment_result = backtester.backtest(best_strategy.genome)
    
    logger.info(f"  Production Sharpe: {deployment_result.sharpe_ratio:.4f}")
    logger.info(f"  Production Drawdown: {deployment_result.max_drawdown:.4f}")
    logger.info(f"  Total Trades: {deployment_result.num_trades}")
    
    logger.info("\nSTEP 4: Edge Decay Monitoring")
    logger.info("-" * 40)
    
    monitor = EdgeDecayMonitor()
    
    baseline_perf = pd.DataFrame({
        'returns': deployment_result.returns,
        'pnl': deployment_result.returns * 100000
    })
    
    recent_data = market_data.iloc[-90:]
    recent_backtester = LeakageFreeBacktester(recent_data)
    recent_result = recent_backtester.backtest(best_strategy.genome)
    
    recent_perf = pd.DataFrame({
        'returns': recent_result.returns,
        'pnl': recent_result.returns * 100000
    })
    
    edge_status = monitor.monitor_strategy(
        genome_id=best_strategy.get_id(),
        recent_performance=recent_perf,
        baseline_performance=baseline_perf
    )
    
    logger.info(f"  Edge Status: {edge_status.recommendation}")
    logger.info(f"  Decay Signals: {len(edge_status.decay_signals)}")
    
    if "RETIRE" in edge_status.recommendation or "REDUCE" in edge_status.recommendation:
        logger.info("\nSTEP 5: Re-Evolution Triggered")
        logger.info("-" * 40)
        logger.info("  Edge decay detected - starting new evolution cycle...")
        
    logger.info("\n" + "="*80)
    logger.info("COMPLETE WORKFLOW FINISHED")
    logger.info("="*80)
    
    return {
        'strategy': best_strategy,
        'walkforward': wf_result,
        'edge_status': edge_status
    }


if __name__ == "__main__":
    logger.info("\n" + "="*80)
    logger.info("AlphaEvolve: Self-Evolving Edge Discovery Engine")
    logger.info("="*80)
    
    try:
        logger.info("\nRunning Example 1: Basic Evolution...")
        example_basic_evolution()
        
        logger.info("\nRunning Example 2: Advanced Evolution...")
        example_advanced_evolution()
        
        logger.info("\nRunning Example 3: Edge Monitoring...")
        example_edge_monitoring()
        
        logger.info("\nRunning Example 4: Distributed Evolution...")
        example_distributed_evolution()
        
        logger.info("\nRunning Example 5: Complete Workflow...")
        example_complete_workflow()
        
        logger.info("\n" + "="*80)
        logger.info("ALL EXAMPLES COMPLETED SUCCESSFULLY")
        logger.info("="*80)
        
    except Exception as e:
        logger.error(f"\nError running examples: {e}", exc_info=True)
