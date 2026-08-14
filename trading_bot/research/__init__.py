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

try:
    from .quant_pipeline import (
        Hypothesis,
        ResearchLab,
        IngestionPipeline,
        FeatureFactory,
        AlphaSignal,
        AlphaDiscoveryEngine,
        StrategyBuilder,
        ValidationLab,
        PortfolioOptimizer,
        SimulatedPaperEnvironment,
        StrategyMetricsSnapshot,
        ProductionMonitor,
        LiteratureReviewBacklog,
        RegimeAndMicrostructureAnalyzer,
        FeatureSelectionSuite,
        AlphaValidatorAndOrthogonality,
        AdvancedStatisticalValidation,
        CapacityAnalyzer,
        ShadowTradingEnvironment,
        PerformanceAttribution,
        AdvancedDriftDetection,
    )
except ImportError as e:
    import logging
    logging.getLogger(__name__).debug(f'Optional import failed in research.quant_pipeline: {e}')

try:
    from .research_os import (
        QuantitativeIdea,
        IdeaRegistry,
        QuantExperiment,
        ExperimentRegistry,
        ReproducibilityAssurer,
        ReviewVerdict,
        PeerReviewBoard,
        FailedIdeaRecord,
        KnowledgeArchive,
        ProductionAnomalyAlert,
        ProductionFeedbackLoop,
        DatasetVersionNode,
        DataLineageRegistry,
        CausalityAndStructuralBreakTester,
        ExplainabilityAndAttributionEngine,
        UncertaintyEstimator,
        StrategyEvolutionEngine,
        ResearchProject,
        ResearchQuestion,
        FeatureSet,
        ValidationReport,
        Deployment,
        PerformanceReport,
        KnowledgeEntry,
        ResearchWorkspace,
    )
except ImportError as e:
    import logging
    logging.getLogger(__name__).debug(f'Optional import failed in research.research_os: {e}')

try:
    from .research_os_v2 import ResearchWorkspaceV2
except ImportError as e:
    import logging
    logging.getLogger(__name__).debug(f'Optional import failed in research.research_os_v2: {e}')

try:
    from .seal_adapter import (
        SEALSelfEdit,
        SEALInnerLoop,
        SEALOuterLoop,
        SEALSystem
    )
except ImportError as e:
    import logging
    logging.getLogger(__name__).debug(f'Optional import failed in research.seal_adapter: {e}')

try:
    from .seal_discovery import (
        SEALDiscoveryCandidate,
        SEALSelfEditProposal,
        SEALDiscoveryEngine
    )
except ImportError as e:
    import logging
    logging.getLogger(__name__).debug(f'Optional import failed in research.seal_discovery: {e}')

try:
    from .research_governance import (
        StrategicMandate,
        ResearchStrategy,
        ResourceAllocation,
        ResearchPortfolioManager,
        ScienceExperimentDesign,
        ExperimentDesigner,
        DecisionRecord,
        DecisionManager,
        AuditTrace,
        GovernanceAuditTrail,
        MetaLearningEngine,
        AlphaAlgoQuantitativePlatform,
    )
except ImportError as e:
    import logging
    logging.getLogger(__name__).debug(f'Optional import failed in research.research_governance: {e}')

try:
    from .discovery_platform import (
        Observation,
        Question,
        HypothesisObject,
        Evidence,
        Theory,
        Decision,
        Action,
        ResearchCase,
        KnowledgeGraph,
        Belief,
        BeliefManagementSystem,
        ScientificJudgmentEngine,
        ResearchBalanceSheet,
        QuantitativeDiscoveryPlatform,
        ConstitutionViolation,
        ConstitutionalLayer,
    )
except ImportError as e:
    import logging
    logging.getLogger(__name__).debug(f'Optional import failed in research.discovery_platform: {e}')

try:
    from .research_organization import (
        PhilosophySpecification,
        ScientificPhilosophy,
        ResearchProgram,
        ResearchProgramManager,
        ScientificReviewVerdict,
        ScientificReviewer,
        KnowledgeIntegrationHub,
        ProductionPackage,
        TechnologyTransferOfficer,
        MetaResearchEngine,
        AlphaAlgoResearchOrganization,
    )
except ImportError as e:
    import logging
    logging.getLogger(__name__).debug(f'Optional import failed in research.research_organization: {e}')

try:
    from .research_kernel import (
        LifecycleState,
        StateTransition,
        ImmutabilityViolation,
        ResearchObject,
        ResearchDependencyGraph,
        ResearchCost,
        ResearchEconomicsEngine,
        ResearchKernel,
    )
except ImportError as e:
    import logging
    logging.getLogger(__name__).debug(f'Optional import failed in research.research_kernel: {e}')

try:
    from .research_computer import (
        EpistemicInstruction,
        CPUCycleTrace,
        EpistemicMetrics,
        EpistemicObjectiveFunction,
        CompiledPipeline,
        ResearchCompiler,
        ResearchMemory,
        ResearchScheduler,
        ResearchCPU,
        QuantitativeResearchComputer,
    )
except ImportError as e:
    import logging
    logging.getLogger(__name__).debug(f'Optional import failed in research.research_computer: {e}')

try:
    from .institution import (
        ResearchOS,
        KnowledgeOS,
        ExperimentOS,
        GovernanceOS,
        EvolutionOS,
        TradingResearchDivision,
        PortfolioResearchDivision,
        MarketMicrostructureDivision,
        RiskScienceDivision,
        AIResearchDivision,
        ProductionDeploymentDivision,
        QuantitativeResearchInstitution,
        MultimodalDataPlane,
        AgentBrain,
        AgentTool,
        AgentExecutor,
        MinuteRecord,
        MinutesLedger,
        OntologyAgent,
        OntologyAgentTask,
        AIPOrchestrator,
        AgentSDK,
        AgentBuilder,
        AIPLogicFunction,
        AI_FDE,
        LivingDigitalTwin,
        ContinuousArchitectureParser,
        WorldStateEngine,
        MultiAgentConsensusEngine,
        ConsensusRole,
        StrategicPlanningLayer,
        ResourceAwareScheduler,
        FormalVerificationModelChecker,
        CausalInferenceEngine,
        BayesianUncertaintyEstimator,
        FailureResearchMemory,
        EconomicEngineeringOptimizer,
        CapabilityGovernance,
        PromptCompressor,
        AntiRewardHackingGate,
        RSILadder,
        AIDE2_InnerLoop,
        AIDE2_OuterLoop,
    )
except ImportError as e:
    import logging
    logging.getLogger(__name__).debug(f'Optional import failed in research.institution: {e}')

__all__ = [
    'ResearchWorkspaceV2',
    'SEALSelfEdit',
    'SEALInnerLoop',
    'SEALOuterLoop',
    'SEALSystem',
    'SEALDiscoveryCandidate',
    'SEALSelfEditProposal',
    'SEALDiscoveryEngine',
    'Hypothesis',
    'ResearchLab',
    'IngestionPipeline',
    'FeatureFactory',
    'AlphaSignal',
    'AlphaDiscoveryEngine',
    'StrategyBuilder',
    'ValidationLab',
    'PortfolioOptimizer',
    'SimulatedPaperEnvironment',
    'StrategyMetricsSnapshot',
    'ProductionMonitor',
    'LiteratureReviewBacklog',
    'RegimeAndMicrostructureAnalyzer',
    'FeatureSelectionSuite',
    'AlphaValidatorAndOrthogonality',
    'AdvancedStatisticalValidation',
    'CapacityAnalyzer',
    'ShadowTradingEnvironment',
    'PerformanceAttribution',
    'AdvancedDriftDetection',
    'QuantitativeIdea',
    'IdeaRegistry',
    'QuantExperiment',
    'ExperimentRegistry',
    'ReproducibilityAssurer',
    'ReviewVerdict',
    'PeerReviewBoard',
    'FailedIdeaRecord',
    'KnowledgeArchive',
    'ProductionAnomalyAlert',
    'ProductionFeedbackLoop',
    'DatasetVersionNode',
    'DataLineageRegistry',
    'CausalityAndStructuralBreakTester',
    'ExplainabilityAndAttributionEngine',
    'UncertaintyEstimator',
    'StrategyEvolutionEngine',
    'ResearchProject',
    'ResearchQuestion',
    'FeatureSet',
    'ValidationReport',
    'Deployment',
    'PerformanceReport',
    'KnowledgeEntry',
    'ResearchWorkspace',
    'StrategicMandate',
    'ResearchStrategy',
    'ResourceAllocation',
    'ResearchPortfolioManager',
    'ScienceExperimentDesign',
    'ExperimentDesigner',
    'DecisionRecord',
    'DecisionManager',
    'AuditTrace',
    'GovernanceAuditTrail',
    'MetaLearningEngine',
    'AlphaAlgoQuantitativePlatform',
    'Observation',
    'Question',
    'HypothesisObject',
    'Evidence',
    'Theory',
    'Decision',
    'Action',
    'ResearchCase',
    'KnowledgeGraph',
    'Belief',
    'BeliefManagementSystem',
    'ScientificJudgmentEngine',
    'ResearchBalanceSheet',
    'QuantitativeDiscoveryPlatform',
    'ConstitutionViolation',
    'ConstitutionalLayer',
    'PhilosophySpecification',
    'ScientificPhilosophy',
    'ResearchProgram',
    'ResearchProgramManager',
    'ScientificReviewVerdict',
    'ScientificReviewer',
    'KnowledgeIntegrationHub',
    'ProductionPackage',
    'TechnologyTransferOfficer',
    'MetaResearchEngine',
    'AlphaAlgoResearchOrganization',
    'LifecycleState',
    'StateTransition',
    'ImmutabilityViolation',
    'ResearchObject',
    'ResearchDependencyGraph',
    'ResearchCost',
    'ResearchEconomicsEngine',
    'ResearchKernel',
    'EpistemicInstruction',
    'CPUCycleTrace',
    'EpistemicMetrics',
    'EpistemicObjectiveFunction',
    'CompiledPipeline',
    'ResearchCompiler',
    'ResearchMemory',
    'ResearchScheduler',
    'ResearchCPU',
    'QuantitativeResearchComputer',
    'ABTestVariant',
    'ABTestingFramework',
    'AdvancedBacktester',
    'BacktestResult',
    'BoundedExperiment',
    'ExtractedClaim',
    'ExperimentalStrategy',
    'ExperimentalStrategyLab',
    'FreeABTesting',
    'FreeBacktester',
    'FreePaperTrading',
    'FreeResearchLab',
    'FreeStrategy',
    'FreeStrategyLibrary',
    'PaperTrade',
    'PaperTradingSimulator',
    'ResearchInnovationHub',
    'ResearchIngestionPipeline',
    'PipelineStage',
    'SourceType',
    'RelevanceCategory',
    'FeasibilityLevel',
    'ResearchSource',
    'retry',
    'ResearchOS',
    'KnowledgeOS',
    'ExperimentOS',
    'GovernanceOS',
    'EvolutionOS',
    'TradingResearchDivision',
    'PortfolioResearchDivision',
    'MarketMicrostructureDivision',
    'RiskScienceDivision',
    'AIResearchDivision',
    'ProductionDeploymentDivision',
    'QuantitativeResearchInstitution',
    'MultimodalDataPlane',
    'AgentBrain',
    'AgentTool',
    'AgentExecutor',
    'MinuteRecord',
    'MinutesLedger',
    'OntologyAgent',
    'OntologyAgentTask',
    'AIPOrchestrator',
    'AgentSDK',
    'AgentBuilder',
    'AIPLogicFunction',
    'AI_FDE',
    'LivingDigitalTwin',
    'ContinuousArchitectureParser',
    'WorldStateEngine',
    'MultiAgentConsensusEngine',
    'ConsensusRole',
    'StrategicPlanningLayer',
    'ResourceAwareScheduler',
    'FormalVerificationModelChecker',
    'CausalInferenceEngine',
    'BayesianUncertaintyEstimator',
    'FailureResearchMemory',
    'EconomicEngineeringOptimizer',
    'CapabilityGovernance',
    'PromptCompressor',
    'AntiRewardHackingGate',
    'RSILadder',
    'AIDE2_InnerLoop',
    'AIDE2_OuterLoop',
]

class ResearchOrchestrator:
    """Auto-generated stub orchestrator for research."""
    pass
