"""
Strategy Discovery Module - Layer 3
====================================

Discovers novel trading strategies through three methods:
1. Reinforcement Learning (PPO, SAC)
2. Evolutionary Algorithms (Genetic Programming)
3. Adversarial Simulation (Red Team/Blue Team)

Goal: Find strategies humans never tried.
"""

from .rl_engine import RLStrategyEngine, TradingPolicy, TradingEnvironment
from .evolutionary_engine import EvolutionaryStrategyEngine, StrategyGenome
from .adversarial_simulator import AdversarialSimulator, MarketScenario, SurvivalMetrics
from .validation import StrategyValidationPipeline

__all__ = [
    'RLStrategyEngine',
    'TradingPolicy',
    'TradingEnvironment',
    'EvolutionaryStrategyEngine',
    'StrategyGenome',
    'AdversarialSimulator',
    'MarketScenario',
    'SurvivalMetrics',
    'StrategyValidationPipeline',
]
