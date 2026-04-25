"""
AADS - Autonomous Alpha Discovery System

A Level 6 Financial AI Infrastructure modeled after:
- Palantir's Foundry (data ops) + Gotham (intelligence graph) + AIP (agent orchestration) + Maven (decision intelligence)
- Sakana AI's evolutionary model merging
- AlphaEvolve's program synthesis
- OmniFlow's agentic workflow orchestration
- MicroFish swarm intelligence
- OpenClaw's extensible tool system
- OpenCLIP's visual intelligence
- Causal inference with do-calculus

Modules:
1. FOUNDRY: Data Sovereignty Layer
2. GOTHAM: Market Intelligence Graph
3. SAKANA: Evolutionary Engine (Strategy Genomes)
4. SIMULATION: Monte Carlo, Agent-Based, Stress Testing
5. ALPHAEVOLVE: Code Evolution Engine
6. MICROFISH: Swarm Intelligence
7. OPENCLAW: Extensible Tool System
8. OPENCLIP: Visual Intelligence
9. CAUSAL: World Model + Causal Reasoning
10. AIP: Multi-Agent Core
11. MAVEN: Decision Intelligence
12. SELF_IMPROVE: Recursive Self-Improvement
"""

__version__ = "6.0.0"

# Lazy imports to avoid circular dependencies
def __getattr__(name):
    """Lazy import for AADS modules"""
    
    # Core Strategy
    if name in ('AADSStrategyGenome', 'StrategyGene', 'RiskGene', 'FilterGene', 'ExecutionGene', 
                'SignalGeneType', 'GenomeStatus', 'create_random_genome', 'merge_strategies'):
        from .core.strategy_genome import (
            AADSStrategyGenome, StrategyGene, RiskGene, FilterGene, ExecutionGene,
            SignalGeneType, GenomeStatus, create_random_genome, merge_strategies
        )
        return locals()[name]
    
    # Evolution
    if name in ('SakanaEvolutionEngine', 'EvolutionConfig'):
        from .core.sakana_engine import SakanaEvolutionEngine, EvolutionConfig
        return locals()[name]
    
    # Foundry - Data Sovereignty
    if name in ('FoundryDataPipeline', 'DataContract', 'DataSchema', 'DataLineage', 'get_foundry'):
        from .core.foundry import FoundryDataPipeline, DataContract, DataSchema, DataLineage, get_foundry
        return locals()[name]
    
    # Gotham - Knowledge Graph
    if name in ('GothamKnowledgeGraph', 'GraphNode', 'GraphEdge', 'NodeType', 'RelationType', 'get_gotham'):
        from .core.gotham import GothamKnowledgeGraph, GraphNode, GraphEdge, NodeType, RelationType, get_gotham
        return locals()[name]
    
    # Simulation Engine
    if name in ('AADSSimulationEngine', 'MonteCarloSimulator', 'StressTestSimulator', 
                'AgentBasedSimulator', 'SimulationResult', 'get_simulation_engine'):
        from .core.simulation_engine import (
            AADSSimulationEngine, MonteCarloSimulator, StressTestSimulator,
            AgentBasedSimulator, SimulationResult, get_simulation_engine
        )
        return locals()[name]
    
    # AlphaEvolve - Code Evolution
    if name in ('AlphaEvolveEngine', 'EvolvedSignal', 'EvolutionContext', 'get_alpha_evolve_engine'):
        from .core.alpha_evolve_engine import AlphaEvolveEngine, EvolvedSignal, EvolutionContext, get_alpha_evolve_engine
        return locals()[name]
    
    # Polymarket
    if name in ('PolymarketModule', 'PolymarketContract', 'PredictionPosition', 'get_polymarket_module'):
        from .core.polymarket import PolymarketModule, PolymarketContract, PredictionPosition, get_polymarket_module
        return locals()[name]
    
    # Swarm
    if name in ('MicroFishSwarm', 'MicroFish', 'SwarmSignal'):
        from .core.microfish_swarm import MicroFishSwarm, MicroFish, SwarmSignal
        return locals()[name]
    
    # Tools
    if name in ('OpenClawRegistry', 'Tool', 'ToolCategory'):
        from .core.openclaw_registry import OpenClawRegistry, Tool, ToolCategory
        return locals()[name]
    
    # Causal
    if name in ('CausalWorldModel', 'CausalIntervention'):
        from .core.causal_world_model import CausalWorldModel, CausalIntervention
        return locals()[name]
    
    # Vision
    if name in ('OpenCLIPPipeline', 'VisualSignal'):
        from .core.openclip_vision import OpenCLIPPipeline, VisualSignal
        return locals()[name]
    
    # Agents
    if name in ('ResearchAgent', 'BullAgent', 'BearAgent', 'RiskAgent', 
                'ExecutionAgent', 'AuditAgent', 'SimulationAgent', 'OntologyAgent'):
        from .core.aip_agents import (
            ResearchAgent, BullAgent, BearAgent, RiskAgent,
            ExecutionAgent, AuditAgent, SimulationAgent, OntologyAgent
        )
        return locals()[name]
    
    # Decision
    if name in ('MavenDecisionEngine', 'DecisionBrief', 'ApprovalStatus'):
        from .core.maven_decision import MavenDecisionEngine, DecisionBrief, ApprovalStatus
        return locals()[name]
    
    # Self-Improvement
    if name in ('SelfImprovementEngine', 'ComponentRegistry'):
        from .core.self_improvement import SelfImprovementEngine, ComponentRegistry
        return locals()[name]
    
    # Discovery Loop
    if name in ('AutonomousAlphaDiscoveryLoop', 'OperationalConstraints'):
        from .core.alpha_discovery_loop import AutonomousAlphaDiscoveryLoop, OperationalConstraints
        return locals()[name]
    
    # Orchestrator
    if name in ('AADSOrchestrator', 'AADSConfig', 'AADSMode', 'create_aads', 'run_aads_demo'):
        from .orchestrator import AADSOrchestrator, AADSConfig, AADSMode, create_aads, run_aads_demo
        return locals()[name]
    
    raise AttributeError(f"module 'trading_bot.aads' has no attribute '{name}'")


__all__ = [
    # Core Strategy
    'AADSStrategyGenome',
    'StrategyGene',
    'RiskGene',
    'FilterGene',
    'ExecutionGene',
    'SignalGeneType',
    'GenomeStatus',
    'create_random_genome',
    'merge_strategies',
    # Evolution
    'SakanaEvolutionEngine',
    'EvolutionConfig',
    # Foundry - Data Sovereignty
    'FoundryDataPipeline',
    'DataContract',
    'DataSchema',
    'DataLineage',
    'get_foundry',
    # Gotham - Knowledge Graph
    'GothamKnowledgeGraph',
    'GraphNode',
    'GraphEdge',
    'NodeType',
    'RelationType',
    'get_gotham',
    # Simulation Engine
    'AADSSimulationEngine',
    'MonteCarloSimulator',
    'StressTestSimulator',
    'AgentBasedSimulator',
    'SimulationResult',
    'get_simulation_engine',
    # AlphaEvolve - Code Evolution
    'AlphaEvolveEngine',
    'EvolvedSignal',
    'EvolutionContext',
    'get_alpha_evolve_engine',
    # Polymarket
    'PolymarketModule',
    'PolymarketContract',
    'PredictionPosition',
    'get_polymarket_module',
    # Swarm
    'MicroFishSwarm',
    'MicroFish',
    'SwarmSignal',
    # Tools
    'OpenClawRegistry',
    'Tool',
    'ToolCategory',
    # Causal
    'CausalWorldModel',
    'CausalIntervention',
    # Vision
    'OpenCLIPPipeline',
    'VisualSignal',
    # Agents
    'ResearchAgent',
    'BullAgent',
    'BearAgent',
    'RiskAgent',
    'ExecutionAgent',
    'AuditAgent',
    'SimulationAgent',
    'OntologyAgent',
    # Decision
    'MavenDecisionEngine',
    'DecisionBrief',
    'ApprovalStatus',
    # Self-Improvement
    'SelfImprovementEngine',
    'ComponentRegistry',
    # Discovery Loop
    'AutonomousAlphaDiscoveryLoop',
    'OperationalConstraints',
    # Orchestrator
    'AADSOrchestrator',
    'AADSConfig',
    'AADSMode',
    'create_aads',
    'run_aads_demo',
]
