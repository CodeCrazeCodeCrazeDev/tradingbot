"""
ultimate_system package
"""

try:
    from .alpha_discovery_engine import (
        AlphaDiscoveryEngine,
        AlphaResearchResult,
        AlphaSignal,
        AlphaStatus,
        AlphaType
    )
    from .deep_agent_system import (
        AgentDecision,
        AgentPerformance,
        AgentState,
        AgentType,
        AutoMLAgent,
        BaseAgent,
        DeepAgentSystem,
        MomentumAgent,
        RLAgent,
        TrendFollowerAgent,
        retry
    )
    from .elite_trader_brain import (
        EliteTraderBrain,
        MarketRegime,
        TradeDecision,
        TradeQuality,
        TradingRules,
        TradingStyle
    )
    from .global_micro_analyzer import (
        GlobalForceAnalysis,
        GlobalMicroAnalyzer,
        MarketForce,
        MarketIntelligence,
        MicroPatternAnalysis,
        PatternType,
        TimeFrame,
        retry
    )
    from .hardware_optimizer import (
        HardwareOptimizer,
        HardwareProfile,
        PerformanceMetrics,
        PerformanceMode,
        ResourceAllocation,
        ResourceType
    )
    from .internet_research_engine import (
        InternetResearchEngine,
        ResearchQuery,
        ResearchResult,
        ResearchType,
        SourceQuality
    )
    from .self_evolving_core import (
        EvolutionProposal,
        EvolutionState,
        LearningEvent,
        LearningMode,
        PerformanceSnapshot,
        SelfEvolvingCore,
        retry
    )
    from .ultimate_orchestrator import (
        SystemState,
        SystemStatus,
        TradingMode,
        TradingSignal,
        UltimateOrchestrator,
        create_ultimate_system,
        quick_start
    )
except ImportError as e:
    import logging
    logging.getLogger(__name__).debug(f'Optional import failed in ultimate_system: {e}')

__all__ = [
    'AgentDecision',
    'AgentPerformance',
    'AgentState',
    'AgentType',
    'AlphaDiscoveryEngine',
    'AlphaResearchResult',
    'AlphaSignal',
    'AlphaStatus',
    'AlphaType',
    'AutoMLAgent',
    'BaseAgent',
    'DeepAgentSystem',
    'EliteTraderBrain',
    'EvolutionProposal',
    'EvolutionState',
    'GlobalForceAnalysis',
    'GlobalMicroAnalyzer',
    'HardwareOptimizer',
    'HardwareProfile',
    'InternetResearchEngine',
    'LearningEvent',
    'LearningMode',
    'MarketForce',
    'MarketIntelligence',
    'MarketRegime',
    'MicroPatternAnalysis',
    'MomentumAgent',
    'PatternType',
    'PerformanceMetrics',
    'PerformanceMode',
    'PerformanceSnapshot',
    'RLAgent',
    'ResearchQuery',
    'ResearchResult',
    'ResearchType',
    'ResourceAllocation',
    'ResourceType',
    'SelfEvolvingCore',
    'SourceQuality',
    'SystemState',
    'SystemStatus',
    'TimeFrame',
    'TradeDecision',
    'TradeQuality',
    'TradingMode',
    'TradingRules',
    'TradingSignal',
    'TradingStyle',
    'TrendFollowerAgent',
    'UltimateOrchestrator',
    'create_ultimate_system',
    'quick_start',
    'retry',
]