"""
risk_management package
"""

try:
    from .component_var import ComponentVaRDecomposer, ComponentVaRResult
    from .contagion_monitor import ContagionResult, ContagionRiskMonitor
    from .copula_dependency import CopulaBasedDependency, CopulaResult
    from .correlation_regime import CorrelationRegimeDetector, CorrelationRegimeResult
    from .drawdown_tracker import DrawdownDurationTracker, DrawdownResult
    from .dynamic_hedging import DynamicHedgingEngine, DynamicHedgingResult, HedgeRecommendation
    from .expected_shortfall import ExpectedShortfall, ExpectedShortfallResult
    from .extreme_value_theory import EVTResult, ExtremeValueTheory
    from .greeks_calculator import GreeksCalculator, GreeksResult
    from .incremental_var import IncrementalVaRCalculator, IncrementalVaRResult
    from .liquidity_var import LiquidityAdjustedVaR, LiquidityVaRResult
    from .margin_predictor import MarginCallPredictor, MarginCallResult
    from .recovery_estimator import RecoveryResult, RecoveryTimeEstimator
    from .scenario_generator import Scenario, ScenarioGenerator, ScenarioResult
    from .stress_tester import PortfolioStressTester, StressTestResult
except ImportError as e:
    import logging
    logging.getLogger(__name__).debug(f'Optional import failed in risk_management: {e}')

__all__ = [
    'ComponentVaRDecomposer',
    'ComponentVaRResult',
    'ContagionResult',
    'ContagionRiskMonitor',
    'CopulaBasedDependency',
    'CopulaResult',
    'CorrelationRegimeDetector',
    'CorrelationRegimeResult',
    'DrawdownDurationTracker',
    'DrawdownResult',
    'DynamicHedgingEngine',
    'DynamicHedgingResult',
    'EVTResult',
    'ExpectedShortfall',
    'ExpectedShortfallResult',
    'ExtremeValueTheory',
    'GreeksCalculator',
    'GreeksResult',
    'HedgeRecommendation',
    'IncrementalVaRCalculator',
    'IncrementalVaRResult',
    'LiquidityAdjustedVaR',
    'LiquidityVaRResult',
    'MarginCallPredictor',
    'MarginCallResult',
    'PortfolioStressTester',
    'RecoveryResult',
    'RecoveryTimeEstimator',
    'Scenario',
    'ScenarioGenerator',
    'ScenarioResult',
    'StressTestResult',
]