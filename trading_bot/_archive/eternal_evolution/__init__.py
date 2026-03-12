"""
eternal_evolution package
"""

try:
    from .architecture_evolution import (
        ArchitectureEvolutionEngine,
        ArchitectureEvolutionResult,
        ArchitecturePattern,
        StabilityMetric,
        SystemHealthSnapshot,
        retry
    )
    from .autonomous_evolution import (
        AutonomousEvolutionEngine,
        EvolutionCandidate,
        EvolutionCheckpoint,
        EvolutionSafetyLevel,
        HarmfulEvolutionDetector,
        RollbackReason,
        SafetyGuardrail,
        retry
    )
    from .data_evolution import (
        AlternativeDataEvolver,
        AlternativeDataPoint,
        DataEvolutionEngine,
        DataQualityMetric,
        DataQualityScore,
        DataSourceType,
        Level2DataProcessor,
        Level2Snapshot,
        retry
    )
    from .eternal_orchestrator import (
        EternalEvolutionOrchestrator,
        EvolutionCycle,
        EvolutionDimension,
        TradingSignal,
        create_eternal_evolution_system,
        quick_start
    )
    from .immutable_core import (
        CorePrinciple,
        EvolvableWrapper,
        ImmutableTradingCore,
        SecurityError,
        TradingIdentity,
        TradingPurpose,
        get_immutable_core
    )
    from .reward_model import (
        EvolutionOutcome,
        PenaltyType,
        RewardComponent,
        RewardSignal,
        TradingRewardModel
    )
    from .risk_evolution import (
        EvolvableRiskParam,
        RiskEvolutionEngine,
        RiskEvolutionResult,
        RiskPerformanceMetrics,
        RiskStrategy,
        retry
    )
    from .security_evolution import (
        SecurityEvent,
        SecurityEvolutionEngine,
        SecurityLayer,
        SecurityRule,
        ThreatIntelligence,
        ThreatType,
        retry
    )
except ImportError as e:
    import logging
    logging.getLogger(__name__).debug(f'Optional import failed in eternal_evolution: {e}')

__all__ = [
    'AlternativeDataEvolver',
    'AlternativeDataPoint',
    'ArchitectureEvolutionEngine',
    'ArchitectureEvolutionResult',
    'ArchitecturePattern',
    'AutonomousEvolutionEngine',
    'CorePrinciple',
    'DataEvolutionEngine',
    'DataQualityMetric',
    'DataQualityScore',
    'DataSourceType',
    'EternalEvolutionOrchestrator',
    'EvolutionCandidate',
    'EvolutionCheckpoint',
    'EvolutionCycle',
    'EvolutionDimension',
    'EvolutionOutcome',
    'EvolutionSafetyLevel',
    'EvolvableRiskParam',
    'EvolvableWrapper',
    'HarmfulEvolutionDetector',
    'ImmutableTradingCore',
    'Level2DataProcessor',
    'Level2Snapshot',
    'PenaltyType',
    'RewardComponent',
    'RewardSignal',
    'RiskEvolutionEngine',
    'RiskEvolutionResult',
    'RiskPerformanceMetrics',
    'RiskStrategy',
    'RollbackReason',
    'SafetyGuardrail',
    'SecurityError',
    'SecurityEvent',
    'SecurityEvolutionEngine',
    'SecurityLayer',
    'SecurityRule',
    'StabilityMetric',
    'SystemHealthSnapshot',
    'ThreatIntelligence',
    'ThreatType',
    'TradingIdentity',
    'TradingPurpose',
    'TradingRewardModel',
    'TradingSignal',
    'create_eternal_evolution_system',
    'get_immutable_core',
    'quick_start',
    'retry',
]