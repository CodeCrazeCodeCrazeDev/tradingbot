"""
NEUROS-FI Evolution: Autonomous Financial Intelligence Infrastructure

This module extends NEUROS-FI with autonomous research agents, self-rewiring networks,
and continuous evolution capabilities.
"""

from .research_agents import (
    QuantResearchAgent,
    MLResearchAgent,
    MicrostructureExpert,
    CrossDomainDiscoveryAgent,
    ResearchCoordinator,
)

from .adaptive_network import (
    AdaptiveRoutingNetwork,
    ResourceAllocationEngine,
    TopologyEvolutionEngine,
    LoadBalancingIntelligence,
)

from .autonomous_org import (
    AIProjectManager,
    PerformanceMonitor,
    ResourceEconomist,
    StrategyPortfolioManager,
)

from .evolution_engine import (
    ArchitectureEvolution,
    KnowledgeSynthesis,
    MetaLearningEngine,
    SelfImprovementEngine,
)

from .neuros_orchestrator import (
    NeurosEvolutionOrchestrator,
    quick_start,
)

from .capability_distillation import (
    CapabilityDistillationSystem,
    FrontierObserver,
    TaskBenchmarker,
    BehaviorExtractor,
    WeaknessInverter,
    SandboxValidator,
    SelectiveDeployer,
    PerformanceMonitor,
    CapabilityPackage,
    create_distillation_system,
)

from .capability_registry import (
    CapabilityRegistry,
    CapabilityRecord,
    RoutingDecision,
    create_registry,
)

from .task_router import (
    TaskRouter,
    TaskRequest,
    RoutingResult,
    ExecutionResult,
    RoutingStrategy,
    create_router,
)

from .behavior_synthesis import (
    BehaviorSynthesizer,
    SynthesizedCapability,
    SynthesisResult,
    SynthesisMode,
    create_synthesizer,
)

from .meta_learning_loop import (
    MetaLearningLoop,
    LearningCycle,
    create_meta_learner,
)

from .meta_intelligence_orchestrator import (
    MetaIntelligenceOrchestrator,
    TaskOutput,
    SystemHealth,
    create_meta_intelligence_layer,
)

from .universal_model_connector import (
    UniversalModelConnector,
    ModelConfig,
    ModelProvider,
    ModelRequest,
    ModelResponse,
    create_universal_connector,
)

from .economic_objectives import (
    EconomicObjectiveLibrary,
    ObjectiveOptimizer,
    TradingMetrics,
    get_objective,
    create_trading_metrics_from_dict,
)

from .fast_router import (
    FastRouter,
    FastRoutingResult,
    AdaptiveFastRouter,
    create_fast_router,
)

from .generic_categories import (
    GenericCategoryManager,
    TaskCategory,
    TaskPattern,
    get_category_manager,
    detect_category,
    register_category,
)

from .unified_meta_intelligence import (
    UnifiedMetaIntelligence,
    MillisecondTaskRequest,
    MillisecondTaskResult,
    create_meta_intelligence,
)

__all__ = [
    # Research Agents
    'QuantResearchAgent',
    'MLResearchAgent',
    'MicrostructureExpert',
    'CrossDomainDiscoveryAgent',
    'ResearchCoordinator',
    
    # Adaptive Network
    'AdaptiveRoutingNetwork',
    'ResourceAllocationEngine',
    'TopologyEvolutionEngine',
    'LoadBalancingIntelligence',
    
    # Autonomous Organization
    'AIProjectManager',
    'PerformanceMonitor',
    'ResourceEconomist',
    'StrategyPortfolioManager',
    
    # Evolution Engine
    'ArchitectureEvolution',
    'KnowledgeSynthesis',
    'MetaLearningEngine',
    'SelfImprovementEngine',
    
    # Orchestrator
    'NeurosEvolutionOrchestrator',
    'quick_start',
    
    # Capability Distillation
    'CapabilityDistillationSystem',
    'FrontierObserver',
    'TaskBenchmarker',
    'BehaviorExtractor',
    'WeaknessInverter',
    'SandboxValidator',
    'SelectiveDeployer',
    'PerformanceMonitor',
    'CapabilityPackage',
    'create_distillation_system',
    
    # Capability Registry
    'CapabilityRegistry',
    'CapabilityRecord',
    'RoutingDecision',
    'create_registry',
    
    # Task Router
    'TaskRouter',
    'TaskRequest',
    'RoutingResult',
    'ExecutionResult',
    'RoutingStrategy',
    'create_router',
    
    # Behavior Synthesis
    'BehaviorSynthesizer',
    'SynthesizedCapability',
    'SynthesisResult',
    'SynthesisMode',
    'create_synthesizer',
    
    # Meta-Learning
    'MetaLearningLoop',
    'LearningCycle',
    'create_meta_learner',
    
    # Meta-Intelligence Orchestrator
    'MetaIntelligenceOrchestrator',
    'TaskOutput',
    'SystemHealth',
    'create_meta_intelligence_layer',
    
    # Universal Model Connector (ANY frontier model)
    'UniversalModelConnector',
    'ModelConfig',
    'ModelProvider',
    'ModelRequest',
    'ModelResponse',
    'create_universal_connector',
    
    # Economic Objectives (PNL, Sharpe, latency, throughput)
    'EconomicObjectiveLibrary',
    'ObjectiveOptimizer',
    'TradingMetrics',
    'get_objective',
    'create_trading_metrics_from_dict',
    
    # Fast Router (millisecond latency)
    'FastRouter',
    'FastRoutingResult',
    'AdaptiveFastRouter',
    'create_fast_router',
    
    # Generic Categories (any task type)
    'GenericCategoryManager',
    'TaskCategory',
    'TaskPattern',
    'get_category_manager',
    'detect_category',
    'register_category',
    
    # Unified Meta-Intelligence
    'UnifiedMetaIntelligence',
    'MillisecondTaskRequest',
    'MillisecondTaskResult',
    'create_meta_intelligence',
]

__version__ = '1.0.0'
