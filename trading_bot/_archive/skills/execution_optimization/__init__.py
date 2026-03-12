"""
execution_optimization package
"""

try:
    from .adaptive_twap_vwap import AdaptiveTWAPVWAP, AdaptiveTWAPVWAPResult, TWAPVWAPSlice
    from .execution_quality import ExecutionQualityResult, ExecutionQualityScorer
    from .fill_probability import FillProbabilityPredictor, FillProbabilityResult
    from .implementation_shortfall import ImplementationShortfallMinimizer, ShortfallComponent, ShortfallResult
    from .latency_defense import LatencyArbitrageDefense, LatencyDefenseResult
    from .maker_taker import MakerTakerDecisionEngine, MakerTakerResult
    from .optimal_execution import (
        ExecutionSchedule,
        ExecutionSlice,
        OptimalExecutionResult,
        OptimalExecutionScheduler
    )
    from .order_anticipation import AnticipationResult, OrderAnticipationDetector
    from .order_fragmenter import FragmentationResult, OrderFragment, SmartOrderFragmenter
    from .participation_rate import ParticipationRateController, ParticipationResult
    from .queue_position import QueuePositionEstimator, QueuePositionResult
    from .slippage_predictor import SlippagePrediction, SlippagePredictor
    from .spread_capture import SpreadCaptureResult, SpreadCaptureStrategy
    from .urgency_classifier import UrgencyClassifier, UrgencyLevel, UrgencyResult
    from .venue_selection import VenueScore, VenueSelectionOptimizer, VenueSelectionResult
except ImportError as e:
    import logging
    logging.getLogger(__name__).debug(f'Optional import failed in execution_optimization: {e}')

__all__ = [
    'AdaptiveTWAPVWAP',
    'AdaptiveTWAPVWAPResult',
    'AnticipationResult',
    'ExecutionQualityResult',
    'ExecutionQualityScorer',
    'ExecutionSchedule',
    'ExecutionSlice',
    'FillProbabilityPredictor',
    'FillProbabilityResult',
    'FragmentationResult',
    'ImplementationShortfallMinimizer',
    'LatencyArbitrageDefense',
    'LatencyDefenseResult',
    'MakerTakerDecisionEngine',
    'MakerTakerResult',
    'OptimalExecutionResult',
    'OptimalExecutionScheduler',
    'OrderAnticipationDetector',
    'OrderFragment',
    'ParticipationRateController',
    'ParticipationResult',
    'QueuePositionEstimator',
    'QueuePositionResult',
    'ShortfallComponent',
    'ShortfallResult',
    'SlippagePrediction',
    'SlippagePredictor',
    'SmartOrderFragmenter',
    'SpreadCaptureResult',
    'SpreadCaptureStrategy',
    'TWAPVWAPSlice',
    'UrgencyClassifier',
    'UrgencyLevel',
    'UrgencyResult',
    'VenueScore',
    'VenueSelectionOptimizer',
    'VenueSelectionResult',
]