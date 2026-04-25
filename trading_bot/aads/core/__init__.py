"""
AADS Core Modules

Contains the fundamental building blocks of the Autonomous Alpha Discovery System.

Modules are imported lazily to avoid circular dependencies.
Import directly from submodules:
    from trading_bot.aads.core.strategy_genome import AADSStrategyGenome
    from trading_bot.aads.core.microfish_swarm import MicroFishSwarm
    from trading_bot.aads.core.foundry import FoundryDataPipeline
    from trading_bot.aads.core.gotham import GothamKnowledgeGraph
"""

# Lazy imports - modules are loaded on first access
__all__ = [
    # Core strategy and evolution
    'strategy_genome',
    'sakana_engine', 
    
    # Data and intelligence layers
    'foundry',
    'gotham',
    
    # Simulation and analysis
    'simulation_engine',
    'causal_world_model',
    
    # Code evolution
    'alpha_evolve_engine',
    
    # Swarm and tools
    'microfish_swarm',
    'openclaw_registry',
    
    # Vision
    'openclip_vision',
    
    # Agents and decision
    'aip_agents',
    'maven_decision',
    
    # Self-improvement
    'self_improvement',
    
    # Discovery loop
    'alpha_discovery_loop',
    
    # Prediction markets
    'polymarket',
]
