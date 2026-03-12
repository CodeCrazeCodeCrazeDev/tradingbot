"""
analysis package
"""

try:
    from .advanced_analysis import (
        AdvancedAnalysisSystem,
        ChaosLevel,
        ChaosResistantSignal,
        ChaosResistantSignalEngine,
        Dimension,
        DimensionalAnomalyDetector,
        DimensionalState,
        DimensionalStateAnalyzer,
        EmotionalRadarReading,
        EnhancedMicrostructureAnalyzer,
        MarketEmotionalRadar,
        MicrostructureAnalysis,
        MultiTimescaleAnalyzer,
        ProbabilityCollapse,
        ProbabilityCollapser,
        Timeframe
    )
except ImportError as e:
    import logging
    logging.getLogger(__name__).debug(f'Optional import failed in analysis: {e}')

__all__ = [
    'AdvancedAnalysisSystem',
    'ChaosLevel',
    'ChaosResistantSignal',
    'ChaosResistantSignalEngine',
    'Dimension',
    'DimensionalAnomalyDetector',
    'DimensionalState',
    'DimensionalStateAnalyzer',
    'EmotionalRadarReading',
    'EnhancedMicrostructureAnalyzer',
    'MarketEmotionalRadar',
    'MicrostructureAnalysis',
    'MultiTimescaleAnalyzer',
    'ProbabilityCollapse',
    'ProbabilityCollapser',
    'Timeframe',
]