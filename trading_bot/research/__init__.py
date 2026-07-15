"""
Quantitative Research Operating System (Research OS) for AlphaAlgo.
A first-class evidence-driven platform managing the complete quantitative research lifecycle.
"""

# Core Interfaces & Base Classes
from .core.interfaces import (
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
    ResearchOrchestrator,

    # Phase 2 additions
    ResearchProposal,
    SchedulingPolicy,
    ResearchPrioritizationPolicy,
    ExperimentScheduler,
    ReviewerOpinion,
    ReviewAgent,
    CausalDiscoveryEngine,
    ActiveLearningPolicy,
    WorldModel,
    DigitalTwin,
    DecisionRecord,
    MetaResearchEngine
)

# Literature, Opportunity and Duplicate Detection Subsystems
from .literature.embedding import (
    TFIDFEmbeddingProvider,
    BM25EmbeddingProvider,
    SentenceTransformersEmbeddingProvider
)
from .literature.duplicate_detection import (
    LevenshteinDuplicateDetector,
    CosineDuplicateDetector,
    HybridEnsembleDuplicateDetector
)
from .discovery.providers import (
    ArxivDiscoveryProvider,
    SemanticScholarDiscoveryProvider,
    LocalArchiveDiscoveryProvider
)

# Hypothesis Subsystem
from .hypothesis.generator import HypothesisGenerator

# Data Discovery & Validation Subsystem
from .data.providers import LocalCSVDataProvider, YahooFinanceDataProvider
from .data.validator import StandardDatasetValidator
from .data.registry import StandardDatasetRegistry
from .data.active_learning import RegimeGapActiveLearning

# Feature Subsystem
from .features.engine import FeatureDiscoveryEngine
from .features.registry import StandardFeatureRegistry

# Statistics Subsystem
from .statistics.tests import (
    ADFStationarityTest,
    LjungBoxAutocorrelationTest,
    GrangerCausalityTest,
    FDRCorrection
)
from .statistics.causality import LinearStructuralCausalModel

# Alpha Subsystem
from .alpha.generators import QuantitativeAlphaGenerator

# Strategy Subsystem
from .strategy.synthesizer import StandardResearchStrategy, StrategySynthesizer
from .strategy.registry import StandardStrategyRegistry

# Experimentation & Model Subsystem
from .experimentation.registry import StandardExperimentRegistry
from .experimentation.model_registry import StandardModelRegistry
from .experimentation.scheduler import (
    SovereignExperimentScheduler,
    FIFOSchedulingPolicy,
    ExpectedInformationGainSchedulingPolicy,
    MultiArmedBanditSchedulingPolicy
)
from .experimentation.prioritization import (
    BayesianEVIPrioritizationPolicy,
    ResearchEconomicsAllocationOptimizer
)

# Knowledge base Subsystem
from .knowledge.registry import StandardKnowledgeRegistry

# Graph Cognitive Memory Subsystem
from .graph.store import NetworkXGraphStore

# Validation & Realistic Backtesting Subsystem
from .validation.backtest import RealisticResearchBacktester
from .validation.robustness import RobustnessTester

# Portfolio Subsystem
from .portfolio.optimizer import PortfolioResearchOptimizer

# Governance Subsystem
from .governance.gates import PromotionPipelineGatekeeper

# Monitoring Subsystem
from .monitoring.drift import ProductionResearchMonitor

# Core Orchestration Kernel
from .orchestration.kernel import SovereignResearchOrchestrator
from .orchestration.cli import run_cli

# Phase 2 World Model & Digital Twin Subsystems
from .world_model.model import MarkovRegimeSwitchingWorldModel
from .twin.simulator import AdversarialMarketDigitalTwin

# Phase 2 Meta-Research & Decision Intelligence Subsystems
from .meta_research.engine import AdaptiveMetaResearchEngine
from .decision_intelligence.auditor import SovereignDecisionAuditor

# Phase 2 Marketplace Subsystem
from .marketplace.agents import (
    StatisticianReviewer,
    EconometricianReviewer,
    PortfolioManagerReviewer,
    RiskManagerReviewer,
    ExecutionSpecialistReviewer,
    SkepticalReviewer
)
from .marketplace.debate import ScientificDebateEngine

# Preserve legacy fallback exports if other legacy parts of AlphaAlgo load them
try:
    from .free_research_lab import (
        FreeABTesting,
        FreeBacktester,
        FreePaperTrading,
        FreeResearchLab,
        FreeStrategy,
        FreeStrategyLibrary
    )
    from .innovation_lab import (
        ABTestVariant,
        ABTestingFramework,
        AdvancedBacktester,
        BacktestResult,
        ExperimentalStrategy,
        ExperimentalStrategyLab,
        PaperTrade,
        PaperTradingSimulator,
        ResearchInnovationHub,
        retry
    )
except ImportError:
    pass

__all__ = [
    # Core Interfaces
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
    'ResearchOrchestrator',
    
    # Phase 2 Abstractions
    'ResearchProposal',
    'SchedulingPolicy',
    'ResearchPrioritizationPolicy',
    'ExperimentScheduler',
    'ReviewerOpinion',
    'ReviewAgent',
    'CausalDiscoveryEngine',
    'ActiveLearningPolicy',
    'WorldModel',
    'DigitalTwin',
    'DecisionRecord',
    'MetaResearchEngine',
    
    # Subsystem Implementations
    'TFIDFEmbeddingProvider',
    'BM25EmbeddingProvider',
    'SentenceTransformersEmbeddingProvider',
    'LevenshteinDuplicateDetector',
    'CosineDuplicateDetector',
    'HybridEnsembleDuplicateDetector',
    'ArxivDiscoveryProvider',
    'SemanticScholarDiscoveryProvider',
    'LocalArchiveDiscoveryProvider',
    'HypothesisGenerator',
    'LocalCSVDataProvider',
    'YahooFinanceDataProvider',
    'StandardDatasetValidator',
    'StandardDatasetRegistry',
    'RegimeGapActiveLearning',
    'FeatureDiscoveryEngine',
    'StandardFeatureRegistry',
    'ADFStationarityTest',
    'LjungBoxAutocorrelationTest',
    'GrangerCausalityTest',
    'FDRCorrection',
    'LinearStructuralCausalModel',
    'QuantitativeAlphaGenerator',
    'StandardResearchStrategy',
    'StrategySynthesizer',
    'StandardStrategyRegistry',
    'StandardExperimentRegistry',
    'StandardModelRegistry',
    'SovereignExperimentScheduler',
    'FIFOSchedulingPolicy',
    'ExpectedInformationGainSchedulingPolicy',
    'MultiArmedBanditSchedulingPolicy',
    'BayesianEVIPrioritizationPolicy',
    'ResearchEconomicsAllocationOptimizer',
    'StandardKnowledgeRegistry',
    'NetworkXGraphStore',
    'RealisticResearchBacktester',
    'RobustnessTester',
    'PortfolioResearchOptimizer',
    'PromotionPipelineGatekeeper',
    'ProductionResearchMonitor',
    'SovereignResearchOrchestrator',
    'run_cli',
    
    # Phase 2 Implementations
    'MarkovRegimeSwitchingWorldModel',
    'AdversarialMarketDigitalTwin',
    'AdaptiveMetaResearchEngine',
    'SovereignDecisionAuditor',
    
    # Phase 2 Marketplace
    'StatisticianReviewer',
    'EconometricianReviewer',
    'PortfolioManagerReviewer',
    'RiskManagerReviewer',
    'ExecutionSpecialistReviewer',
    'SkepticalReviewer',
    'ScientificDebateEngine',
]
