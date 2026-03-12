"""
optimization package
"""

try:
    from .bayesian_optimizer import (
        BayesianOptimizer,
        ParameterSpace,
        StrategyOptimizer,
        retry
    )
    from .hyperparameter_tuner import FeatureSelector, HyperparameterTuner
    from .quantum_portfolio import (
        OptimizationObjective,
        PortfolioAllocation,
        QuantumPortfolio,
        RiskMetrics,
        create_quantum_portfolio
    )
    from .quantum_portfolio_optimizer import (
        AdvancedPortfolioOptimizer,
        BlackLittermanOptimizer,
        HierarchicalRiskParityOptimizer,
        PortfolioConstraints,
        QuantumInspiredOptimizer,
        QuantumMLForecaster,
        QuantumSecureEncryption,
        RiskParityOptimizer
    )
    from .strategy_optimizer_v2 import (
        BacktestResult,
        OptimizationMethod,
        OptimizationResult,
        ParameterSpace,
        StrategyBacktester,
        StrategyOptimizer,
        momentum_strategy,
        rsi_strategy,
        run_optimization_demo,
        sma_crossover_strategy
    )
except ImportError as e:
    import logging
    logging.getLogger(__name__).debug(f'Optional import failed in optimization: {e}')

__all__ = [
    'AdvancedPortfolioOptimizer',
    'BacktestResult',
    'BayesianOptimizer',
    'BlackLittermanOptimizer',
    'FeatureSelector',
    'HierarchicalRiskParityOptimizer',
    'HyperparameterTuner',
    'OptimizationMethod',
    'OptimizationObjective',
    'OptimizationResult',
    'ParameterSpace',
    'PortfolioAllocation',
    'PortfolioConstraints',
    'QuantumInspiredOptimizer',
    'QuantumMLForecaster',
    'QuantumPortfolio',
    'QuantumSecureEncryption',
    'RiskMetrics',
    'RiskParityOptimizer',
    'StrategyBacktester',
    'StrategyOptimizer',
    'create_quantum_portfolio',
    'momentum_strategy',
    'retry',
    'rsi_strategy',
    'run_optimization_demo',
    'sma_crossover_strategy',
]