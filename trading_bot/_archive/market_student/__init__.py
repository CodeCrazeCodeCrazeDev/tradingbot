"""
market_student package
"""

try:
    from .alphaalgo_identity import (
        AlphaAlgoIdentity,
        CORE_IDENTITY,
        EVOLUTION_CYCLE,
        EvolutionPhase,
        GROWTH_PRINCIPLES,
        GROWTH_SOURCES,
        IMPROVEMENT_PRINCIPLES,
        LEARNING_SOURCES,
        LearningRole,
        LearningSource,
        MARKET_EXAMINATION,
        MARKET_TEACHING_DESCRIPTIONS,
        MarketTeaching,
        RoleDefinition,
        SAFETY_RULES,
        STUDY_CURRICULUM,
        StudySubject,
        get_alphaalgo_identity,
        get_core_identity,
        get_improvement_principles,
        get_learning_role,
        get_safety_rules
    )
    from .evolution_engine import EvolutionProposal, EvolutionStatus, SafeEvolutionEngine
    from .learning_cycle import (
        AlphaLearningCycle,
        CyclePhase,
        CycleResult,
        retry
    )
    from .lesson_database import LessonDatabase, LessonQuery, StoredLesson
    from .market_student_orchestrator import (
        MarketStudentOrchestrator,
        OrchestratorConfig,
        main,
        quick_start,
        retry
    )
    from .market_teacher import (
        LessonSeverity,
        LessonType,
        MarketLesson,
        MarketTeacher
    )
    from .reward_system import (
        ImmutableRewardSystem,
        PenaltyCategory,
        PenaltySignal,
        RewardCategory,
        RewardSignal,
        get_reward_system
    )
    from .student_ai import (
        ImprovementProposal,
        LearningPhase,
        LearningState,
        ProposalPriority,
        ProposalStatus,
        ProposalType,
        StudentAI
    )
except ImportError as e:
    import logging
    logging.getLogger(__name__).debug(f'Optional import failed in market_student: {e}')

__all__ = [
    'AlphaAlgoIdentity',
    'AlphaLearningCycle',
    'CORE_IDENTITY',
    'CyclePhase',
    'CycleResult',
    'EVOLUTION_CYCLE',
    'EvolutionPhase',
    'EvolutionProposal',
    'EvolutionStatus',
    'GROWTH_PRINCIPLES',
    'GROWTH_SOURCES',
    'IMPROVEMENT_PRINCIPLES',
    'ImmutableRewardSystem',
    'ImprovementProposal',
    'LEARNING_SOURCES',
    'LearningPhase',
    'LearningRole',
    'LearningSource',
    'LearningState',
    'LessonDatabase',
    'LessonQuery',
    'LessonSeverity',
    'LessonType',
    'MARKET_EXAMINATION',
    'MARKET_TEACHING_DESCRIPTIONS',
    'MarketLesson',
    'MarketStudentOrchestrator',
    'MarketTeacher',
    'MarketTeaching',
    'OrchestratorConfig',
    'PenaltyCategory',
    'PenaltySignal',
    'ProposalPriority',
    'ProposalStatus',
    'ProposalType',
    'RewardCategory',
    'RewardSignal',
    'RoleDefinition',
    'SAFETY_RULES',
    'STUDY_CURRICULUM',
    'SafeEvolutionEngine',
    'StoredLesson',
    'StudentAI',
    'StudySubject',
    'get_alphaalgo_identity',
    'get_core_identity',
    'get_improvement_principles',
    'get_learning_role',
    'get_reward_system',
    'get_safety_rules',
    'main',
    'quick_start',
    'retry',
]