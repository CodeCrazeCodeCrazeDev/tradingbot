"""
Phase 4: World Models & Simulation
DreamerV3-style world model for market prediction
"""

from .latent_dynamics import (
    WorldModel,
    MarketStateEncoder,
    MarketStateDecoder,
    LatentDynamicsModel,
    RewardPredictor
)

from .imagination import ImaginationPlanner

from .synthetic_data import (
    SyntheticMarketGenerator,
    MarketScenario,
    MarketRegime
)

__all__ = [
    'WorldModel',
    'MarketStateEncoder',
    'MarketStateDecoder',
    'LatentDynamicsModel',
    'RewardPredictor',
    'ImaginationPlanner',
    'SyntheticMarketGenerator',
    'MarketScenario',
    'MarketRegime'
]
