"""
orchestrator package
"""

try:
    from .agent_orchestrator import AgentOrchestrator, create_agent_orchestrator
    from .execution_engine import (
        ExecutionAlgorithm,
        ExecutionEngine,
        ExecutionResult,
        OrderType,
        SmartOrderRouter,
        retry
    )
    from .master_orchestrator import (
        MasterOrchestrator,
        TradingDecision,
        TradingMode,
        retry
    )
    from .ml_predictor import (
        MLFeatureExtractor,
        ModelEnsemble,
        OpportunityPredictor,
        PredictionResult,
        ProbabilityCalibrator,
        SuccessPredictor,
        retry
    )
    from .performance_tracker import (
        AutoOptimizer,
        BacktestEngine,
        MetricsCalculator,
        PerformanceMetrics,
        PerformanceTracker
    )
    from .position_rotator import (
        CloseReason,
        Position,
        PositionRotator,
        RotationDecision
    )
    from .risk_manager import (
        DrawdownController,
        HedgeCalculator,
        PortfolioRiskManager,
        PositionSizer,
        RiskLevel,
        RiskMetrics
    )
except ImportError as e:
    import logging
    logging.getLogger(__name__).debug(f'Optional import failed in orchestrator: {e}')

__all__ = [
    'AgentOrchestrator',
    'AutoOptimizer',
    'BacktestEngine',
    'CloseReason',
    'DrawdownController',
    'ExecutionAlgorithm',
    'ExecutionEngine',
    'ExecutionResult',
    'HedgeCalculator',
    'MLFeatureExtractor',
    'MasterOrchestrator',
    'MetricsCalculator',
    'ModelEnsemble',
    'OpportunityPredictor',
    'OrderType',
    'PerformanceMetrics',
    'PerformanceTracker',
    'PortfolioRiskManager',
    'Position',
    'PositionRotator',
    'PositionSizer',
    'PredictionResult',
    'ProbabilityCalibrator',
    'RiskLevel',
    'RiskMetrics',
    'RotationDecision',
    'SmartOrderRouter',
    'SuccessPredictor',
    'TradingDecision',
    'TradingMode',
    'create_agent_orchestrator',
    'retry',
]