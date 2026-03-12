"""
evolution package
"""

try:
    from .strategy_evolution import (
        CrossMarketIntelligence,
        EvolutionResult,
        GeneType,
        GeneticStrategyEvolver,
        IntelligenceSource,
        MutationType,
        NonTraditionalIntelligence,
        SelfReprogrammingEngine,
        StrategyCreationLab,
        StrategyDNA,
        StrategyEvolutionSystem,
        StrategyGene,
        StrategyGeneMap
    )
except ImportError as e:
    import logging
    logging.getLogger(__name__).debug(f'Optional import failed in evolution: {e}')

__all__ = [
    'CrossMarketIntelligence',
    'EvolutionResult',
    'GeneType',
    'GeneticStrategyEvolver',
    'IntelligenceSource',
    'MutationType',
    'NonTraditionalIntelligence',
    'SelfReprogrammingEngine',
    'StrategyCreationLab',
    'StrategyDNA',
    'StrategyEvolutionSystem',
    'StrategyGene',
    'StrategyGeneMap',
]