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
from .ignorance_score import (
    IgnoranceScoreEngine,
)
from .uncertainty_engine import (
    UncertaintyEngine,
)

# Simulation and Planning (Canonical V2-compatible)
from .imagination import (
    ImaginationPlanner,
    PlanResult,
    CEMPlanner,
)
from .simulation_orchestrator import (
    SimulationOrchestrator,
    SimulationConfig,
    SimulationMode,
    SimulationResult,
)

# Synthetic Data Generation
from .synthetic_data import (
    SyntheticMarketGenerator,
    MarketRegime,
    WorldFabricSimulator,
    CurriculumLevel,
    DomainRandomizationConfig,
)

# Experience and Memory
from .experience_replay import (
    ExperienceReplayBuffer,
    Experience,
    BeliefStateTracker,
)

# Maintenance of Legacy Core for transition
from .latent_dynamics import (
    WorldModel,
)

__all__ = [
    # Canonical WM-V2
    'WorldModelV2',
    'MarketScenario',
    'PredictiveMarketCore',
    'UnifiedCrossAssetEncoder',
    'WorldModelTrainer',
    'LegacyWorldModelAdapter',

    # State and Governance
    'MarketWorldState',
    'VolatilityRegime',
    'LiquidityCondition',
    'SystemMode',
    'IgnoranceScoreEngine',
    'UncertaintyEngine',

    # Planning and Orchestration
    'ImaginationPlanner',
    'PlanResult',
    'CEMPlanner',
    'SimulationOrchestrator',
    'SimulationConfig',
    'SimulationMode',
    'SimulationResult',

    # Environment and Data
    'SyntheticMarketGenerator',
    'MarketRegime',
    'WorldFabricSimulator',
    'CurriculumLevel',
    'DomainRandomizationConfig',

    # Learning and Memory
    'ExperienceReplayBuffer',
    'Experience',
    'BeliefStateTracker',

    # Legacy Transition
    'WorldModel',
]
