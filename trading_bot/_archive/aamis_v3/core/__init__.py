"""
core package
"""

try:
    from .metacognitive_awareness import (
        ConfidenceAssessment,
        ConfidenceEstimator,
        ConfidenceLevel,
        ContextRecognition,
        ContextRecognizer,
        KnowledgeGap,
        MetacognitiveAwareness,
        ModelValidity,
        SelfReflection,
        SelfReflectionEngine
    )
    from .multimodal_fusion import (
        AudioAnalyzer,
        FusedIntelligence,
        HandwritingRecognizer,
        ImageRestorer,
        Modality,
        ModalityData,
        MultiModalFusionEngine,
        TextAnalyzer,
        VideoAnalyzer
    )
    from .neuro_symbolic_engine import (
        CausalEdge,
        CausalGraph,
        LogicOperator,
        LogicalRule,
        ModalOperator,
        NeuralPatternExtractor,
        NeuroSymbolicEngine,
        Predicate,
        SymbolicReasoner
    )
    from .self_evolving_intelligence import (
        AlphaSignal,
        EvolutionMetrics,
        EvolutionPhase,
        FeatureEngineer,
        GeneticAlgorithm,
        SelfEvolvingIntelligence,
        StrategyGene,
        SymbolicRegressor,
        TradingStrategy
    )
except ImportError as e:
    import logging
    logging.getLogger(__name__).debug(f'Optional import failed in core: {e}')

__all__ = [
    'AlphaSignal',
    'AudioAnalyzer',
    'CausalEdge',
    'CausalGraph',
    'ConfidenceAssessment',
    'ConfidenceEstimator',
    'ConfidenceLevel',
    'ContextRecognition',
    'ContextRecognizer',
    'EvolutionMetrics',
    'EvolutionPhase',
    'FeatureEngineer',
    'FusedIntelligence',
    'GeneticAlgorithm',
    'HandwritingRecognizer',
    'ImageRestorer',
    'KnowledgeGap',
    'LogicOperator',
    'LogicalRule',
    'MetacognitiveAwareness',
    'ModalOperator',
    'Modality',
    'ModalityData',
    'ModelValidity',
    'MultiModalFusionEngine',
    'NeuralPatternExtractor',
    'NeuroSymbolicEngine',
    'Predicate',
    'SelfEvolvingIntelligence',
    'SelfReflection',
    'SelfReflectionEngine',
    'StrategyGene',
    'SymbolicReasoner',
    'SymbolicRegressor',
    'TextAnalyzer',
    'TradingStrategy',
    'VideoAnalyzer',
]