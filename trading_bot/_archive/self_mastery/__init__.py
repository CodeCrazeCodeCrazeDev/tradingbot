"""
self_mastery package
"""

try:
    from .code_evolver import (
        CodeEvolver,
        CodeModification,
        EvolutionResult,
        EvolutionType,
        SafetyCheck,
        SafetyLevel
    )
    from .experience_memory import (
        DecisionContext,
        ExperienceMemory,
        ExperienceType,
        OutcomeAnalysis,
        OutcomeQuality,
        TradeExperience
    )
    from .knowledge_consolidator import (
        ConsolidationResult,
        KnowledgeConsolidator,
        KnowledgeLevel,
        MasteredSkill,
        SkillCategory
    )
    from .mastery_orchestrator import (
        MasteryConfig,
        MasteryOrchestrator,
        MasteryPhase,
        MasteryStatus,
        quick_start
    )
    from .self_reflection import (
        FailureAnalysis,
        InsightType,
        PatternType,
        PerformancePattern,
        ReflectionInsight,
        SelfReflector,
        SuccessPattern
    )
except ImportError as e:
    import logging
    logging.getLogger(__name__).debug(f'Optional import failed in self_mastery: {e}')

__all__ = [
    'CodeEvolver',
    'CodeModification',
    'ConsolidationResult',
    'DecisionContext',
    'EvolutionResult',
    'EvolutionType',
    'ExperienceMemory',
    'ExperienceType',
    'FailureAnalysis',
    'InsightType',
    'KnowledgeConsolidator',
    'KnowledgeLevel',
    'MasteredSkill',
    'MasteryConfig',
    'MasteryOrchestrator',
    'MasteryPhase',
    'MasteryStatus',
    'OutcomeAnalysis',
    'OutcomeQuality',
    'PatternType',
    'PerformancePattern',
    'ReflectionInsight',
    'SafetyCheck',
    'SafetyLevel',
    'SelfReflector',
    'SkillCategory',
    'SuccessPattern',
    'TradeExperience',
    'quick_start',
]