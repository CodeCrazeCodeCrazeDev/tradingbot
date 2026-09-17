"""
AlphaAlgo World Model Subsystem
===============================

The World Model provides market simulation, latent dynamics prediction,
and counterfactual reasoning capabilities.

Canonical Architecture: WM-V2 (Institutional Predictive Planning)
Backbone: Hybrid Transformer-Mamba (SSM)
"""

# Core WM-V2 Components
from .v2_core import (
    WorldModelV2,
    MarketScenario,
    PredictiveMarketCore,
    UnifiedCrossAssetEncoder,
)

# Training and Adaptation
from .v2_training import (
    WorldModelSpecialistTrainer as WorldModelTrainer,
)
from .v2_adapter import (
    LegacyWorldModelAdapter,
)

# Support Infrastructure
from .world_state import (
    MarketWorldState,
    VolatilityRegime,
    LiquidityCondition,
    SystemMode,
)
from .v2_core import (
    WorldModelV2,
    MarketScenario as V2MarketScenario,
    PredictiveMarketCore,
    UnifiedCrossAssetEncoder,
)
from .v2_training import (
    WorldModelTrainer as V2WorldModelTrainer,
)
from .v2_adapter import (
    LegacyWorldModelAdapter,
)

__all__ = [
    'MarketWorldState',
    'VolatilityRegime',
    'LiquidityCondition',
    'SystemMode',
    'WorldModelV2',
    'V2MarketScenario',
    'PredictiveMarketCore',
    'UnifiedCrossAssetEncoder',
    'V2WorldModelTrainer',
    'LegacyWorldModelAdapter',
]
