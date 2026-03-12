"""
strategy_generation package
"""

try:
    from .alpha_decay import AlphaDecayForecaster, AlphaDecayResult
    from .capacity_estimator import CapacityResult, StrategyCapacityEstimator
    from .correlation_matrix import CorrelationMatrixResult, StrategyCorrelationMatrix
    from .cross_asset_adapter import AdaptationResult, CrossAssetStrategyAdapter
    from .crowding_detector import CrowdingDetector, CrowdingResult
    from .decay_detector import DecayResult, StrategyDecayDetector
    from .dynamic_weighting import DynamicStrategyWeighting, WeightingResult
    from .fingerprinting import FingerprintResult, StrategyFingerprinting
    from .genetic_evolver import GeneticResult, GeneticStrategyEvolver, Strategy
    from .paper_validator import PaperTradingResult, PaperTradingValidator
    from .purged_cv import CombinatorialPurgedCV, PurgedCVResult
    from .regime_selector import RegimeSelectorResult, RegimeSpecificStrategySelector
    from .strategy_cloner import ClonedStrategy, ClonerResult, StrategyCloner
    from .tournament_system import StrategyTournamentSystem, TournamentResult
    from .walk_forward import WalkForwardOptimizer, WalkForwardResult
except ImportError as e:
    import logging
    logging.getLogger(__name__).debug(f'Optional import failed in strategy_generation: {e}')

__all__ = [
    'AdaptationResult',
    'AlphaDecayForecaster',
    'AlphaDecayResult',
    'CapacityResult',
    'ClonedStrategy',
    'ClonerResult',
    'CombinatorialPurgedCV',
    'CorrelationMatrixResult',
    'CrossAssetStrategyAdapter',
    'CrowdingDetector',
    'CrowdingResult',
    'DecayResult',
    'DynamicStrategyWeighting',
    'FingerprintResult',
    'GeneticResult',
    'GeneticStrategyEvolver',
    'PaperTradingResult',
    'PaperTradingValidator',
    'PurgedCVResult',
    'RegimeSelectorResult',
    'RegimeSpecificStrategySelector',
    'Strategy',
    'StrategyCapacityEstimator',
    'StrategyCloner',
    'StrategyCorrelationMatrix',
    'StrategyDecayDetector',
    'StrategyFingerprinting',
    'StrategyTournamentSystem',
    'TournamentResult',
    'WalkForwardOptimizer',
    'WalkForwardResult',
    'WeightingResult',
]