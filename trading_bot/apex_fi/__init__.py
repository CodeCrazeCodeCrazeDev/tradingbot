"""
APEX-FI: Adaptive Financial Intelligence Infrastructure

Genetic Parentage: Palantir Technologies × Two Sigma × Citadel
Architecture Class: Self-Improving · Self-Discovering · Self-Evolving
Constitutional Version: 4.0 · Immutable

A self-contained financial intelligence organism capable of sensing market reality,
building world models, generating hypotheses, deploying capital, learning from outcomes,
and recursively improving its own architecture.
"""

try:
    from .data_fabric import (
        DataFabric,
        KnowledgeGraph,
        DataAtom,
        Entity,
        Relationship,
        EntityType,
        RelationType,
        DataQuality,
        get_data_fabric,
    )
except ImportError:
    DataFabric = None
    KnowledgeGraph = None
    DataAtom = None
    Entity = None
    Relationship = None
    EntityType = None
    RelationType = None
    DataQuality = None
    get_data_fabric = None

try:
    from .alpha_mining import (
        AlphaMiningEngine,
        GeneticAlphaSearch,
        LivingFactorLibrary,
    )
except ImportError:
    AlphaMiningEngine = None
    GeneticAlphaSearch = None
    LivingFactorLibrary = None

try:
    from .model_parliament import (
        ModelParliament,
        MetaLearnerOracle,
    )
except ImportError:
    ModelParliament = None
    MetaLearnerOracle = None

try:
    from .portfolio_architect import (
        PortfolioArchitect,
    )
except ImportError:
    PortfolioArchitect = None

try:
    from .execution_intelligence import (
        ExecutionIntelligence,
    )
except ImportError:
    ExecutionIntelligence = None

try:
    from .risk_governance import (
        RiskGovernance,
    )
except ImportError:
    RiskGovernance = None

try:
    from .meta_intelligence import (
        MetaIntelligence,
        EvolutionLedger,
    )
except ImportError:
    MetaIntelligence = None
    EvolutionLedger = None

try:
    from .constitutional_layer import (
        ConstitutionalLayer,
        ConstitutionalConstraints,
        get_constitutional_layer,
    )
except ImportError:
    ConstitutionalLayer = None
    ConstitutionalConstraints = None
    get_constitutional_layer = None

try:
    from .apex_orchestrator import (
        APEXOrchestrator,
        quick_start,
    )
except ImportError:
    APEXOrchestrator = None
    quick_start = None

__all__ = [
    # Layer 1
    'DataFabric',
    'OntologyEngine',
    'SemanticKnowledgeGraph',
    'DataQualityScorer',
    'DataLineageTracker',
    'EntityNode',
    'RelationshipEdge',
    
    # Layer 2
    'AlphaMiningEngine',
    'GeneticAlphaSearch',
    'LLMHypothesisGenerator',
    'CausalDiscoveryEngine',
    'LivingFactorLibrary',
    'AlphaCandidate',
    'FactorMetadata',
    
    # Layer 3
    'ModelParliament',
    'MetaLearnerOracle',
    'NeuralArchitectureSearch',
    'UncertaintyQuantifier',
    'ModelCard',
    'ParliamentVote',
    
    # Layer 4
    'PortfolioArchitect',
    'HierarchicalRiskParity',
    'RegimeAwarePositionSizer',
    'MultiStrategyAllocator',
    'StressScenarioEngine',
    'PortfolioState',
    
    # Layer 5
    'ExecutionIntelligence',
    'RLOrderRouter',
    'AdversarialDefense',
    'TransactionCostEngine',
    'MicrostructureNavigator',
    'ExecutionPlan',
    
    # Layer 6
    'RiskGovernance',
    'TickByTickRiskDecomposer',
    'HierarchicalCircuitBreaker',
    'RegimeSurveillanceAI',
    'ComplianceEngine',
    'RiskState',
    
    # Layer 7
    'MetaIntelligence',
    'AutoPostMortem',
    'PerformanceTracker',
    'TransferLearner',
    'ArchitectureEvolver',
    'EvolutionLedger',
    'ImprovementProposal',
    
    # Constitutional
    'ConstitutionalLayer',
    'ImmutableConstraints',
    'SandboxProtocol',
    'HumanOversightBridge',
    'ConstitutionalBreach',
    
    # Orchestrator
    'APEXOrchestrator',
    'InitializationSequence',
    'PerformanceMetrics',
    'SystemState',
    'quick_start',
]

__version__ = '4.0.0'
__author__ = 'APEX-FI Development Team'
__license__ = 'Proprietary'
