"""
Decision Layer Module
============================================================

Auto-generated integration file.
"""

# Stub class for graceful degradation
class DecisionLayerOrchestrator:
    def __init__(self, config=None):
        self.config = config or {}
    async def start(self):
        pass
    async def stop(self):
        pass

# Core types
from .core_types import (
    DecisionCategory,
    DecisionAction,
    DecisionUrgency,
    DecisionContext,
    DecisionResult,
    AggregatedDecision,
    DecisionConcept,
)

# concepts_10_meta
try:
    from .concepts_10_meta import (
        MetaDecisionOrchestratorDecision,
    )
except ImportError as e:
    # concepts_10_meta not available
    pass

# innovative_decision_engine
try:
    from .innovative_decision_engine import (
        InnovativeDecisionEngine,
        create_decision_engine,
        quick_decide,
    )
except ImportError as e:
    # innovative_decision_engine not available
    pass

# EXPANDED: Research Orchestrator (ASI-Evolve inspired)
try:
    from .research_orchestrator import (
        ResearchOrchestrator,
        ExperimentStatus,
        SamplingPolicy,
        ResearchMotivation,
        ExperimentNode,
        CognitionEntry,
        AnalysisResult,
        ResearcherAgent,
        EngineerAgent,
        AnalyzerAgent,
        CognitionStore as ResearchCognitionStore,
        create_research_orchestrator,
    )
except ImportError as e:
    # research_orchestrator not available
    pass

# EXPANDED: 12th Category - Research-Informed Concepts
try:
    from .concepts_12_research_informed import (
        ExperimentBackedStrategy,
        CrossDomainAnalogy,
        ResearchConsensus,
        NovelPatternRecognition,
        KnowledgeGraphPath,
        TransferredStrategy,
        ValidatedHypothesis,
        CognitiveStoreMatch,
        ResearchDebateOutcome,
        MetaLearningTransfer,
        RESEARCH_INFORMED_CONCEPTS,
    )
except ImportError as e:
    # concepts_12_research_informed not available
    pass

__all__ = [
    # Core types
    'DecisionLayerOrchestrator',
    'DecisionCategory',
    'DecisionAction',
    'DecisionUrgency',
    'DecisionContext',
    'DecisionResult',
    'AggregatedDecision',
    'DecisionConcept',
    
    # Decision Engine
    'InnovativeDecisionEngine',
    'create_decision_engine',
    'quick_decide',
    
    # Meta
    'MetaDecisionOrchestratorDecision',
    
    # EXPANDED: Research Orchestrator
    'ResearchOrchestrator',
    'ExperimentStatus',
    'SamplingPolicy',
    'ResearchMotivation',
    'ExperimentNode',
    'AnalysisResult',
    'ResearcherAgent',
    'EngineerAgent',
    'AnalyzerAgent',
    'create_research_orchestrator',
    
    # EXPANDED: Research-Informed Concepts
    'ExperimentBackedStrategy',
    'CrossDomainAnalogy',
    'ResearchConsensus',
    'NovelPatternRecognition',
    'KnowledgeGraphPath',
    'TransferredStrategy',
    'ValidatedHypothesis',
    'CognitiveStoreMatch',
    'ResearchDebateOutcome',
    'MetaLearningTransfer',
    'RESEARCH_INFORMED_CONCEPTS',
]
