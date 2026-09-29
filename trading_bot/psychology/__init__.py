"""Psychology Module - Behavioral and Psychological Features."""

try:
    from .behavioral_features import (
        BehavioralAnalyzer,
        EmotionalStateTracker,
        CognitiveBiasDetector,
        TiltDetector,
        DisciplineTracker,
        EmotionalState,
        CognitiveBias,
        TiltLevel,
        DisciplineArea,
        TradeRecord,
        PsychologicalProfile,
        TiltAssessment,
        DisciplineReport,
        assess_trading_readiness,
        detect_cognitive_biases
    )
except ImportError:
    BehavioralAnalyzer = None

__all__ = [
    'BehavioralAnalyzer',
    'EmotionalStateTracker',
    'CognitiveBiasDetector',
    'TiltDetector',
    'DisciplineTracker',
    'EmotionalState',
    'CognitiveBias',
    'TiltLevel',
    'DisciplineArea',
    'TradeRecord',
    'PsychologicalProfile',
    'TiltAssessment',
    'DisciplineReport',
    'assess_trading_readiness',
    'detect_cognitive_biases',
]


class PsychologyOrchestrator:
    """Auto-generated stub orchestrator for psychology."""
    
    def __init__(self, config=None):
        self.config = config or {}
        import warnings
        warnings.warn(
            "PsychologyOrchestrator is a merge-generated stub and is deprecated. "
            "Route orchestration through CognitiveSystemController "
            "(trading_bot.core.csc.controller).",
            DeprecationWarning, stacklevel=2,
        )
        self.running = False
        self._initialized = True
    
    async def start(self):
        self.running = True
    
    async def stop(self):
        self.running = False
    
    def get_status(self):
        return {"running": self.running, "initialized": self._initialized}
