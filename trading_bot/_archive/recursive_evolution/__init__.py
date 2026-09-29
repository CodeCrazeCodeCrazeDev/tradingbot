"""
Recursive Self-Evolution System
=================================

A comprehensive meta-learning system that recursively improves ALL aspects of trading:
- Elite trader reasoning and decision-making
- Deep market intelligence and research
- Institutional-grade order flow analysis
- Multi-paradigm decision fusion
- Continuous self-improvement across all dimensions

COMPREHENSIVE EVOLUTION SYSTEM:
- Evolves strategies, risk management, execution, data processing, ML models
- Enforces immutable boundaries (what AI can and CANNOT evolve)
- Requires human approval for critical changes
- Recursive meta-learning (learns how to evolve better)

This system learns how to learn better, evolves its evolution strategies,
and continuously discovers better ways to trade like a professional elite trader.
"""

# Original recursive evolution components
try:
    from .recursive_meta_learner import (
        RecursiveMetaLearner,
        EvolutionDimension,
        ImprovementProposal,
        MetaLearningConfig
    )
    from .elite_reasoning_engine import (
        EliteReasoningEngine,
        ReasoningStep,
        TradeReasoning,
        ReasoningQuality
    )
    from .deep_market_intelligence import (
        DeepMarketIntelligence,
        MarketIntelligenceReport,
        InstitutionalSignal,
        LiquidityMap
    )
    from .institutional_orderflow import (
        InstitutionalOrderFlow,
        OrderFlowSignal,
        InstitutionalActivity,
        BlockTradeDetector
    )
    from .multi_paradigm_fusion import (
        MultiParadigmFusion,
        ParadigmType,
        FusedDecision,
        DecisionConfidence
    )
    from .recursive_orchestrator import (
        RecursiveEvolutionOrchestrator,
        EvolutionMetrics
    )
    _ORIGINAL_AVAILABLE = True
except ImportError:
    _ORIGINAL_AVAILABLE = False

# New comprehensive evolution system
from .evolution_boundaries import (
    EvolutionBoundaries,
    EvolutionPermission,
    ImmutableBoundary,
    verify_boundary_integrity,
    get_evolution_guide
)

from .comprehensive_evolution_engine import (
    RecursiveEvolutionEngine,
    EvolutionProposal,
    EvolutionResult,
    EvolutionArea,
    EvolutionStatus,
    StrategyEvolution,
    RiskEvolution,
    ExecutionEvolution,
    MLModelEvolution,
    DataProcessingEvolution
)

from .comprehensive_orchestrator import (
    ComprehensiveEvolutionOrchestrator,
    EvolutionConfig,
    SystemMetrics,
    quick_start
)

# Module-specific evolution
from .module_evolution_rules import (
    ModuleEvolutionBoundaries,
    ModuleEvolutionRules,
    ModuleName,
    get_module_evolution_guide
)

from .unified_module_evolution import (
    UnifiedModuleEvolution,
    ModuleEvolutionEngine,
    ModuleEvolutionProposal,
    quick_start_unified
)

__all__ = [
    # Comprehensive Evolution System (NEW)
    'ComprehensiveEvolutionOrchestrator',
    'RecursiveEvolutionEngine',
    'EvolutionBoundaries',
    'EvolutionPermission',
    'ImmutableBoundary',
    'EvolutionProposal',
    'EvolutionResult',
    'EvolutionArea',
    'EvolutionStatus',
    'EvolutionConfig',
    'SystemMetrics',
    'verify_boundary_integrity',
    'get_evolution_guide',
    'quick_start',
    
    # Area-specific evolution
    'StrategyEvolution',
    'RiskEvolution',
    'ExecutionEvolution',
    'MLModelEvolution',
    'DataProcessingEvolution',
    
    # Module-specific evolution (NEW)
    'UnifiedModuleEvolution',
    'ModuleEvolutionEngine',
    'ModuleEvolutionProposal',
    'ModuleEvolutionBoundaries',
    'ModuleEvolutionRules',
    'ModuleName',
    'get_module_evolution_guide',
    'quick_start_unified',
]

# Add original components if available
if _ORIGINAL_AVAILABLE:
    __all__.extend([
        'RecursiveMetaLearner',
        'EvolutionDimension',
        'ImprovementProposal',
        'MetaLearningConfig',
        'EliteReasoningEngine',
        'ReasoningStep',
        'TradeReasoning',
        'ReasoningQuality',
        'DeepMarketIntelligence',
        'MarketIntelligenceReport',
        'InstitutionalSignal',
        'LiquidityMap',
        'InstitutionalOrderFlow',
        'OrderFlowSignal',
        'InstitutionalActivity',
        'BlockTradeDetector',
        'MultiParadigmFusion',
        'ParadigmType',
        'FusedDecision',
        'DecisionConfidence',
        'RecursiveEvolutionOrchestrator',
        'EvolutionMetrics'
    ])
