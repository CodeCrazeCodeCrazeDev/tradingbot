"""
Self-Assembly and Self-Managing AI System V2
=============================================

A self-assembling, self-managing AI with comprehensive capabilities:

CORE COMPONENTS (V1):
- ImmutableSafetyCore: Cryptographically verified safety boundaries
- RecursiveSelfImprovement: Safe evolution engine with constraints
- SelfAssemblyOrchestrator: Autonomous component management
- RiskMitigationMatrix: Multi-layer risk prevention
- EvolutionMonitor: Continuous safety verification

ADVANCED COMPONENTS (V2):
- CodeGenetics: DNA-like code evolution with mutation/crossover
- SwarmIntelligence: PSO, ACO, ABC collective optimization
- NeuralArchitectureSearch: Auto-designing neural networks
- EmergentBehavior: Complex patterns from simple rules
- StrategyFactory: Self-replicating trading strategies
- ComponentAutoWiring: Self-configuring dependency injection
- SelfAssemblyOrchestratorV2: Ultimate self-assembling system
"""

from .immutable_safety_core import (
    ImmutableSafetyCore,
    SafetyBoundary,
    SafetyViolation,
    verify_safety_integrity,
)

from .recursive_self_improvement import (
    RecursiveSelfImprovement,
    ImprovementProposal,
    ImprovementType,
    SafetyConstraint,
)

from .self_assembly_orchestrator import (
    SelfAssemblyOrchestrator,
    ComponentType,
    AssemblyStatus,
    quick_start_self_assembly,
)

from .risk_mitigation_matrix import (
    RiskMitigationMatrix,
    RiskCategory,
    MitigationStrategy,
    RiskLevel,
)

from .evolution_monitor import (
    EvolutionMonitor,
    EvolutionMetrics,
    SafetyCheckpoint,
    rollback_to_checkpoint,
)

from .advanced_ai_capabilities import (
    AdvancedAICapability,
    get_default_advanced_ai_capabilities,
    summarize_capabilities_by_category,
)

from .master_orchestrator import (
    MasterSelfAssemblyOrchestrator,
    SystemStatus,
    quick_start_self_assembly_ai,
    run_self_assembly_ai,
)

# V2 Components - Code Genetics
from .code_genetics import (
    CodeGenetics,
    Gene,
    GeneType,
    Chromosome,
    GenePool,
    create_code_genetics,
)

# V2 Components - Swarm Intelligence
from .swarm_intelligence import (
    SwarmIntelligence,
    SwarmAgent,
    ParticleAgent,
    AntAgent,
    BeeAgent,
    Position,
    Pheromone,
    create_swarm_intelligence,
)

# V2 Components - Neural Architecture Search
from .neural_architecture_search import (
    NeuralArchitectureSearch,
    Architecture,
    LayerConfig,
    LayerType,
    SearchSpace,
    PerformancePredictor,
    create_nas_engine,
)

# V2 Components - Emergent Behavior
from .emergent_behavior import (
    EmergentBehaviorEngine,
    CellularAutomata,
    SelfOrganizingMap,
    Autopoiesis,
    HomeostasisController,
    EmergentPattern,
    create_emergent_behavior_engine,
)

# V2 Components - Strategy Factory
from .strategy_factory import (
    StrategyFactory,
    Strategy,
    StrategyDNA,
    StrategyBlueprint,
    StrategyType,
    StrategyState,
    create_strategy_factory,
)

# V2 Components - Component Auto-Wiring
from .component_autowiring import (
    AutoWiringContainer,
    ComponentRegistry,
    DependencyResolver,
    ComponentScanner,
    ComponentMetadata,
    ComponentScope,
    component,
    autowired,
    create_autowiring_container,
)

# V2 Master Orchestrator
from .self_assembly_orchestrator_v2 import (
    SelfAssemblyOrchestratorV2,
    AssemblyMode,
    AssemblyState,
    AssemblyConfig,
    SystemHealth,
    create_self_assembly_v2,
    run_self_assembly_v2,
)

__all__ = [
    # Core V1
    'ImmutableSafetyCore',
    'SafetyBoundary',
    'SafetyViolation',
    'verify_safety_integrity',
    
    # Self-Improvement V1
    'RecursiveSelfImprovement',
    'ImprovementProposal',
    'ImprovementType',
    'SafetyConstraint',
    
    # Self-Assembly V1
    'SelfAssemblyOrchestrator',
    'ComponentType',
    'AssemblyStatus',
    'quick_start_self_assembly',
    
    # Risk Mitigation
    'RiskMitigationMatrix',
    'RiskCategory',
    'MitigationStrategy',
    'RiskLevel',
    
    # Evolution Monitoring
    'EvolutionMonitor',
    'EvolutionMetrics',
    'SafetyCheckpoint',
    'rollback_to_checkpoint',

    # Advanced AI Capabilities
    'AdvancedAICapability',
    'get_default_advanced_ai_capabilities',
    'summarize_capabilities_by_category',
    
    # Master Orchestrator V1
    'MasterSelfAssemblyOrchestrator',
    'SystemStatus',
    'quick_start_self_assembly_ai',
    'run_self_assembly_ai',
    
    # V2 - Code Genetics
    'CodeGenetics',
    'Gene',
    'GeneType',
    'Chromosome',
    'GenePool',
    'create_code_genetics',
    
    # V2 - Swarm Intelligence
    'SwarmIntelligence',
    'SwarmAgent',
    'ParticleAgent',
    'AntAgent',
    'BeeAgent',
    'Position',
    'Pheromone',
    'create_swarm_intelligence',
    
    # V2 - Neural Architecture Search
    'NeuralArchitectureSearch',
    'Architecture',
    'LayerConfig',
    'LayerType',
    'SearchSpace',
    'PerformancePredictor',
    'create_nas_engine',
    
    # V2 - Emergent Behavior
    'EmergentBehaviorEngine',
    'CellularAutomata',
    'SelfOrganizingMap',
    'Autopoiesis',
    'HomeostasisController',
    'EmergentPattern',
    'create_emergent_behavior_engine',
    
    # V2 - Strategy Factory
    'StrategyFactory',
    'Strategy',
    'StrategyDNA',
    'StrategyBlueprint',
    'StrategyType',
    'StrategyState',
    'create_strategy_factory',
    
    # V2 - Component Auto-Wiring
    'AutoWiringContainer',
    'ComponentRegistry',
    'DependencyResolver',
    'ComponentScanner',
    'ComponentMetadata',
    'ComponentScope',
    'component',
    'autowired',
    'create_autowiring_container',
    
    # V2 - Master Orchestrator
    'SelfAssemblyOrchestratorV2',
    'AssemblyMode',
    'AssemblyState',
    'AssemblyConfig',
    'SystemHealth',
    'create_self_assembly_v2',
    'run_self_assembly_v2',
]

__version__ = '2.0.0'
