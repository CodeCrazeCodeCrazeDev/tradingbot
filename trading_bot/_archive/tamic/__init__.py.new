"""
TAMIC - Time-Aware Market Intelligence Core

A conservative, time-aware market intelligence system operating under real-world trading constraints.
Primary objective is long-term survival and capital compounding, not prediction accuracy or trade frequency.

Core principles:
- Time dominates price
- Survival > Profit
- Uncertainty is a signal
- Change slowly
"""

from .core import (
    TAMIC,
    TAMICConfig,
    TimeHorizon,
    MarketTimeState,
    SignalHalfLife,
    TAMICDecision,
    create_tamic,
    quick_start
)

from .horizon_segmentation import (
    HorizonSegmentation
)

from .signal_decay import (
    SignalDecay
)

from .market_time import (
    MarketTimeEngine
)

from .time_risk import (
    TimeBasedRiskManager,
    DrawdownSpeedMonitor,
    RecoveryDurationTracker,
    LossClusteringDetector,
    RiskAssessmentResult,
    DrawdownSpeed,
    DrawdownMetrics
)

from .institutional_time import (
    InstitutionalTimeEngine,
    InstitutionalTimeResult,
    FlowType,
    FlowDirection,
    FlowStrength,
    InstitutionalFlow
)

from .optionality import (
    OptionalityPreservationEngine,
    OptionalityResult,
    OptionalityMetrics,
    OptionalityValue,
    IrreversibilityLevel,
    OpportunityState
)

from .confidence_control import (
    ConfidenceHumilityControl,
    ConfidenceResult,
    ConfidenceMetrics,
    ConfidenceCalibration,
    UncertaintyLevel
)

from .forbidden_behaviors import (
    ForbiddenBehaviorGuard,
    ForbiddenBehaviorResult,
    ForbiddenBehaviorType
)

__all__ = [
    # Core
    'TAMIC',
    'TAMICConfig',
    'TimeHorizon',
    'MarketTimeState',
    'SignalHalfLife',
    'TAMICDecision',
    'create_tamic',
    'quick_start',
    
    # Horizon Segmentation
    'HorizonSegmentation',
    
    # Signal Decay
    'SignalDecay',
    
    # Market Time
    'MarketTimeEngine',
    
    # Time-Based Risk
    'TimeBasedRiskManager',
    'DrawdownSpeedMonitor',
    'RecoveryDurationTracker',
    'LossClusteringDetector',
    'RiskAssessmentResult',
    'DrawdownSpeed',
    'DrawdownMetrics',
    
    # Institutional Time
    'InstitutionalTimeEngine',
    'InstitutionalTimeResult',
    'FlowType',
    'FlowDirection',
    'FlowStrength',
    'InstitutionalFlow',
    
    # Optionality Preservation
    'OptionalityPreservationEngine',
    'OptionalityResult',
    'OptionalityMetrics',
    'OptionalityValue',
    'IrreversibilityLevel',
    'OpportunityState',
    
    # Confidence & Humility
    'ConfidenceHumilityControl',
    'ConfidenceResult',
    'ConfidenceMetrics',
    'ConfidenceCalibration',
    'UncertaintyLevel',
    
    # Forbidden Behaviors
    'ForbiddenBehaviorGuard',
    'ForbiddenBehaviorResult',
    'ForbiddenBehaviorType'
]
