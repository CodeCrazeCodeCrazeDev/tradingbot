"""
AlphaEvolve Launcher: Quick start script for self-evolving edge discovery.

This script provides a simple interface to run the AlphaEvolve system
with your trading bot's market data.
"""

import sys
import logging
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent / "trading_bot"))

from trading_bot.alpha_evolve import (
    EvolutionEngine,
    EvolutionConfig,
    SearchSpace,
    EdgeDecayMonitor
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'alpha_evolve_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


def load_market_data():
    """
    Load market data from your data source.
    
    Replace this with your actual data loading logic.
    """
    import pandas as pd
    import numpy as np
    
    logger.info("Loading market data...")
    
    try:
        data = pd.read_csv('market_data.csv', index_col='date', parse_dates=True)
        logger.info(f"Loaded {len(data)} rows of market data")
        return data
    
    except FileNotFoundError:
        logger.warning("market_data.csv not found - generating sample data")
        
        dates = pd.date_range(end=datetime.now(), periods=2000, freq='D')
        np.random.seed(42)
        returns = np.random.normal(0.0005, 0.02, 2000)
        prices = 100 * np.exp(np.cumsum(returns))
        
        data = pd.DataFrame({
            'open': prices * np.random.uniform(0.99, 1.01, 2000),
            'high': prices * np.random.uniform(1.00, 1.02, 2000),
            'low': prices * np.random.uniform(0.98, 1.00, 2000),
            'close': prices,
            'volume': np.random.uniform(1e6, 5e6, 2000),
        }, index=dates)
        
        data['returns'] = data['close'].pct_change()
        
        logger.info(f"Generated {len(data)} rows of sample data")
        return data


def run_evolution(market_data, config=None):
    """
    Run the evolution engine to discover trading strategies.
    
    Args:
        market_data: DataFrame with OHLCV data
        config: Optional EvolutionConfig (uses defaults if None)
    
    Returns:
        Best strategy found
    """
    if config is None:
        config = EvolutionConfig(
            population_size=100,
            elite_size=10,
            tournament_size=3,
            mutation_rate=0.15,
            crossover_rate=0.7,
            max_generations=50,
            use_walkforward=True,
            walkforward_frequency=5,
            parallel_workers=8,
            save_frequency=5,
            save_directory="alpha_evolve_results"
        )
    
    logger.info("Initializing evolution engine...")
    logger.info(f"  Population Size: {config.population_size}")
    logger.info(f"  Max Generations: {config.max_generations}")
    logger.info(f"  Parallel Workers: {config.parallel_workers}")
    logger.info(f"  Walk-Forward Validation: {config.use_walkforward}")
    
    search_space = SearchSpace()
    
    engine = EvolutionEngine(
        config=config,
        search_space=search_space,
        market_data=market_data
    )
    
    logger.info("\nStarting evolution...")
    logger.info("="*80)
    
    best_strategy = engine.evolve()
    
    logger.info("\n" + "="*80)
    logger.info("EVOLUTION COMPLETE")
    logger.info("="*80)
    logger.info(f"\nBest Strategy Found:")
    logger.info(f"  ID: {best_strategy.get_id()}")
    logger.info(f"  Total Fitness: {best_strategy.fitness.total_fitness:.4f}")
    logger.info(f"  Sharpe Ratio: {best_strategy.fitness.sharpe_ratio:.4f}")
    logger.info(f"  Max Drawdown: {best_strategy.fitness.max_drawdown:.4f}")
    logger.info(f"  Regime Stability: {best_strategy.fitness.regime_stability:.4f}")
    logger.info(f"  Tail Risk Score: {best_strategy.fitness.tail_risk:.4f}")
    logger.info(f"  Number of Signals: {len(best_strategy.genome.signals)}")
    logger.info(f"  Complexity: {best_strategy.genome.get_complexity()}")
    
    if best_strategy.walkforward_result:
        wf = best_strategy.walkforward_result
        logger.info(f"\nWalk-Forward Validation:")
        logger.info(f"  Train Sharpe: {wf.train_sharpe:.4f}")
        logger.info(f"  Test Sharpe: {wf.test_sharpe:.4f}")
        logger.info(f"  Fitness Degradation: {wf.fitness_degradation:.2%}")
        logger.info(f"  Overfitting Score: {wf.overfitting_score:.4f}")
        logger.info(f"  Statistically Significant: {wf.is_statistically_significant}")
        logger.info(f"  P-value: {wf.p_value:.4f}")
    
    logger.info(f"\nResults saved to: {config.save_directory}")
    
    return best_strategy


def main():
    """Main entry point"""
    logger.info("\n" + "="*80)
    logger.info("AlphaEvolve: Self-Evolving Edge Discovery Engine")
    logger.info("="*80)
    logger.info("\nA rigorous, statistically-grounded evolutionary search system")
    logger.info("for discovering, validating, and exploiting market edges.\n")
    
    try:
        market_data = load_market_data()
        
        config = EvolutionConfig(
            population_size=100,
            elite_size=10,
            max_generations=50,
            use_walkforward=True,
            parallel_workers=8,
            save_directory="alpha_evolve_results"
        )
        
        best_strategy = run_evolution(market_data, config)
        
        logger.info("\n" + "="*80)
        logger.info("SUCCESS: Strategy discovery complete!")
        logger.info("="*80)
        logger.info("\nNext Steps:")
        logger.info("  1. Review results in alpha_evolve_results/")
        logger.info("  2. Validate strategy on additional out-of-sample data")
        logger.info("  3. Deploy to paper trading for live validation")
        logger.info("  4. Monitor for edge decay using EdgeDecayMonitor")
        logger.info("  5. Re-run evolution quarterly or when edges decay")
        
        return 0
    
    except KeyboardInterrupt:
        logger.info("\n\nEvolution interrupted by user")
        return 1
    
    except Exception as e:
        logger.error(f"\n\nError during evolution: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
