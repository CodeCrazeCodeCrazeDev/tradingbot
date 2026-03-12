"""
sentient_core package
"""

try:
    from .ai_learner import (
        AILearner,
        AISystemAnalysis,
        LearnedTechnique,
        LearningSource
    )
    from .code_evolver import (
        CodeChange,
        CodeEvolver,
        DataSourceConfig,
        EvolutionStatus,
        EvolutionType,
        StrategyTemplate
    )
    from .introspector import (
        CodeQualityReport,
        DetectedFlaw,
        FlawSeverity,
        FlawType,
        Introspector,
        PerformanceMetric
    )
    from .knowledge_harvester import (
        KnowledgeHarvester,
        KnowledgeItem,
        KnowledgeType,
        SentimentData
    )
    from .network_sentinel import (
        ConnectionEvent,
        ConnectionState,
        NetworkMetrics,
        NetworkSentinel,
        TradingMode,
        get_network_sentinel
    )
    from .profit_maximizer import (
        MarketCondition,
        OptimizationResult,
        PerformanceMetrics,
        ProfitMaximizer,
        TradeResult,
        TradingMode,
        retry
    )
    from .self_defender import (
        SecurityConfig,
        SecurityEvent,
        SelfDefender,
        ThreatLevel,
        ThreatType
    )
    from .sentient_orchestrator import (
        SentientOrchestrator,
        SystemState,
        SystemStatus,
        create_sentient_system,
        quick_start
    )
    from .institutional_github_scout import (
        InstitutionalGitHubScout,
        RepoAnalysis,
        RepoCategory,
        ExpectedROI,
        RiskLevel,
        Recommendation,
        create_github_scout,
    )
except ImportError as e:
    import logging
    logging.getLogger(__name__).debug(f'Optional import failed in sentient_core: {e}')

__all__ = [
    'AILearner',
    'AISystemAnalysis',
    'CodeChange',
    'CodeEvolver',
    'CodeQualityReport',
    'ConnectionEvent',
    'ConnectionState',
    'DataSourceConfig',
    'DetectedFlaw',
    'EvolutionStatus',
    'EvolutionType',
    'FlawSeverity',
    'FlawType',
    'Introspector',
    'KnowledgeHarvester',
    'KnowledgeItem',
    'KnowledgeType',
    'LearnedTechnique',
    'LearningSource',
    'MarketCondition',
    'NetworkMetrics',
    'NetworkSentinel',
    'OptimizationResult',
    'PerformanceMetric',
    'PerformanceMetrics',
    'ProfitMaximizer',
    'SecurityConfig',
    'SecurityEvent',
    'SelfDefender',
    'SentientOrchestrator',
    'SentimentData',
    'StrategyTemplate',
    'SystemState',
    'SystemStatus',
    'ThreatLevel',
    'ThreatType',
    'TradeResult',
    'TradingMode',
    'create_sentient_system',
    'get_network_sentinel',
    'quick_start',
    'retry',
    'InstitutionalGitHubScout',
    'RepoAnalysis',
    'RepoCategory',
    'ExpectedROI',
    'RiskLevel',
    'Recommendation',
    'create_github_scout',
]
