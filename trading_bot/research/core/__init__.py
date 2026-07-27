"""
Research OS Core Module
Contains primary domain-driven interfaces and abstract base classes.
"""

from .interfaces import (
    ResearchPaper,
    EmbeddingProvider,
    DuplicateDetectionProvider,
    LiteratureDiscoveryProvider,
    HypothesisObject,
    StandardizedDataset,
    DataProvider,
    DatasetValidator,
    EngineeredFeature,
    FeatureScorer,
    StatisticalTest,
    AlphaSignal,
    AlphaGenerator,
    ResearchStrategy,
    ExperimentRegistry,
    DatasetRegistry,
    FeatureRegistry,
    ModelRegistry,
    StrategyRegistry,
    KnowledgeRegistry,
    GraphStore,
    ResearchEvent,
    ResearchOrchestrator
)

__all__ = [
    'ResearchPaper',
    'EmbeddingProvider',
    'DuplicateDetectionProvider',
    'LiteratureDiscoveryProvider',
    'HypothesisObject',
    'StandardizedDataset',
    'DataProvider',
    'DatasetValidator',
    'EngineeredFeature',
    'FeatureScorer',
    'StatisticalTest',
    'AlphaSignal',
    'AlphaGenerator',
    'ResearchStrategy',
    'ExperimentRegistry',
    'DatasetRegistry',
    'FeatureRegistry',
    'ModelRegistry',
    'StrategyRegistry',
    'KnowledgeRegistry',
    'GraphStore',
    'ResearchEvent',
    'ResearchOrchestrator'
]
