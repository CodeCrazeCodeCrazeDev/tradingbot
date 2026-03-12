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
]

__version__ = '1.0.0'
