"""
detection package
"""

try:
    from .market_detection import (
        AdvancedMarketDetectionSystem,
        Anticipation,
        AnticipatoryThinkingEngine,
        ConsensusFracture,
        ConsensusFractureDetector,
        EmotionReading,
        LieDetectionResult,
        MarketEmotion,
        MarketLieDetector,
        RealTimeEmotionMapper,
        RiftSyncCoordinator,
        SignalTruth,
        StateShift,
        StateShiftDetector,
        StateShiftType
    )
except ImportError as e:
    import logging
    logging.getLogger(__name__).debug(f'Optional import failed in detection: {e}')

__all__ = [
    'AdvancedMarketDetectionSystem',
    'Anticipation',
    'AnticipatoryThinkingEngine',
    'ConsensusFracture',
    'ConsensusFractureDetector',
    'EmotionReading',
    'LieDetectionResult',
    'MarketEmotion',
    'MarketLieDetector',
    'RealTimeEmotionMapper',
    'RiftSyncCoordinator',
    'SignalTruth',
    'StateShift',
    'StateShiftDetector',
    'StateShiftType',
]