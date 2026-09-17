"""
AlphaAlgo World Model Subsystem
===============================

The World Model provides market simulation, latent dynamics prediction,
and counterfactual reasoning capabilities.

Canonical Architecture: WM-V3 / SCM V5
Backbone: Hybrid Transformer-Mamba (SSM)
"""

# Core WM-V2/V3 Components
from .v2_core import (
    WorldModelV2,
    MarketScenario,
    PredictiveMarketCore,
    UnifiedCrossAssetEncoder,
)

# Training and Adaptation
from .v2_training import (
    WorldModelSpecialistTrainer,
    WorldModelSpecialistTrainer,
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

# Simulation and Planning (Canonical V2-compatible)
from .imagination import (
    ImaginationPlanner,
    PlanResult,
    CEMPlanner,
)

# Experience and Memory
from .experience_replay import (
    ExperienceReplayBuffer,
    Experience,
    BeliefStateTracker,
)

# Maintenance of Legacy Core for transition

__all__ = [
    # Canonical WM-V2/V3
    'WorldModelV2',
    'MarketScenario',
    'PredictiveMarketCore',
    'UnifiedCrossAssetEncoder',
    'WorldModelSpecialistTrainer',
    'LegacyWorldModelAdapter',

    # State and Governance
    'MarketWorldState',
    'VolatilityRegime',
    'LiquidityCondition',
    'SystemMode',

    # Planning and Orchestration
    'ImaginationPlanner',
    'PlanResult',
    'CEMPlanner',

    # Learning and Memory
    'ExperienceReplayBuffer',
    'Experience',
    'BeliefStateTracker',

    # Legacy Transition
]
