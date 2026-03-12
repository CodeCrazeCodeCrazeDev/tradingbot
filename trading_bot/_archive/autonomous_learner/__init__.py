"""
Autonomous Learner Module

A self-learning system that:
- Accesses the internet to learn trading
- Reads books, research papers, articles
- Learns from basic to advanced levels
- Tests itself with evolving difficulty
- Transfers knowledge to the trading bot
"""

from .internet_researcher import (
    InternetResearcher,
    ResourceType,
    DifficultyLevel,
    LearningResource,
    LearnedConcept,
)

from .knowledge_builder import (
    KnowledgeBuilder,
    ConceptCategory,
    TradingConcept,
    KnowledgeNode,
)

from .self_tester import (
    SelfTester,
    TestDifficulty,
    QuestionType,
    TestQuestion,
    TestResult,
    TestSession,
)

from .knowledge_transfer import (
    KnowledgeTransfer,
    TransferType,
    TransferableKnowledge,
)

from .learning_monitor import (
    LearningMonitor,
    LearningPhase,
    LearningMetrics,
    LearningEvent,
)

from .learning_orchestrator import (
    LearningOrchestrator,
    LearningMode,
    LearningSessionConfig,
    LearningSessionResult,
    run_2_hour_learning_session,
    quick_start,
)

__all__ = [
    # Internet Researcher
    'InternetResearcher',
    'ResourceType',
    'DifficultyLevel',
    'LearningResource',
    'LearnedConcept',
    
    # Knowledge Builder
    'KnowledgeBuilder',
    'ConceptCategory',
    'TradingConcept',
    'KnowledgeNode',
    
    # Self Tester
    'SelfTester',
    'TestDifficulty',
    'QuestionType',
    'TestQuestion',
    'TestResult',
    'TestSession',
    
    # Knowledge Transfer
    'KnowledgeTransfer',
    'TransferType',
    'TransferableKnowledge',
    
    # Learning Monitor
    'LearningMonitor',
    'LearningPhase',
    'LearningMetrics',
    'LearningEvent',
    
    # Learning Orchestrator
    'LearningOrchestrator',
    'LearningMode',
    'LearningSessionConfig',
    'LearningSessionResult',
    'run_2_hour_learning_session',
    'quick_start',
]
