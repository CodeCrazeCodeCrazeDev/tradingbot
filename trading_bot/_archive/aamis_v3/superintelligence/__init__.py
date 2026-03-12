"""
superintelligence package
"""

try:
    from .memory_systems import (
        LongTermMemory,
        MarketLesson,
        MemoryConsolidation,
        MemoryImportance,
        MemorySystem,
        MemoryType,
        ShortTermMemory
    )
    from .multi_brain_ensemble import (
        AgentOpinion,
        AgentRole,
        CollectiveDecision,
        MultiBrainEnsemble,
        SpecializedAgent,
        VoteWeight
    )
    from .regime_strategy_engine import (
        MarketRegime,
        RegimeCharacteristics,
        RegimeDetector,
        RegimeStrategyEngine,
        StrategyActivation,
        StrategyPerformance,
        StrategySelector,
        StrategyType
    )
    from .self_optimizing_core import (
        Hypothesis,
        KnowledgeAtom,
        LearningExperience,
        LearningSource,
        OptimizationObjective,
        SelfOptimizingCore,
        StrategyGene
    )
    from .self_regulation_engine import (
        BehaviorAnalyzer,
        DrawdownMonitor,
        HealthStatus,
        OvertradingDetector,
        RegulationAction,
        RegulationLevel,
        RegulationRule,
        SelfRegulationEngine,
        SystemHealth,
        TradingBehavior,
        ViolationType
    )
    from .superintelligence_orchestrator import (
        SuperintelligenceDecision,
        SuperintelligenceOrchestrator,
        SuperintelligenceReport,
        main,
        retry
    )
except ImportError as e:
    import logging
    logging.getLogger(__name__).debug(f'Optional import failed in superintelligence: {e}')

__all__ = [
    'AgentOpinion',
    'AgentRole',
    'BehaviorAnalyzer',
    'CollectiveDecision',
    'DrawdownMonitor',
    'HealthStatus',
    'Hypothesis',
    'KnowledgeAtom',
    'LearningExperience',
    'LearningSource',
    'LongTermMemory',
    'MarketLesson',
    'MarketRegime',
    'MemoryConsolidation',
    'MemoryImportance',
    'MemorySystem',
    'MemoryType',
    'MultiBrainEnsemble',
    'OptimizationObjective',
    'OvertradingDetector',
    'RegimeCharacteristics',
    'RegimeDetector',
    'RegimeStrategyEngine',
    'RegulationAction',
    'RegulationLevel',
    'RegulationRule',
    'SelfOptimizingCore',
    'SelfRegulationEngine',
    'ShortTermMemory',
    'SpecializedAgent',
    'StrategyActivation',
    'StrategyGene',
    'StrategyPerformance',
    'StrategySelector',
    'StrategyType',
    'SuperintelligenceDecision',
    'SuperintelligenceOrchestrator',
    'SuperintelligenceReport',
    'SystemHealth',
    'TradingBehavior',
    'ViolationType',
    'VoteWeight',
    'main',
    'retry',
]