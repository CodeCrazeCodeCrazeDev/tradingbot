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
from .ignorance_score import (
    IgnoranceScoreEngine,
)
from .uncertainty_engine import (
    UncertaintyEngine,
)

# Simulation and Planning (Canonical V2-compatible)
from .imagination import (
    PlanningEngine,
    FutureSimulator,
)

# Simulation Components - Pointing to Canonical Simulation Subsystem
try:
    from trading_bot.simulation import (
        SimulationOrchestrator,
        SimulationMode,
    )
except ImportError:
    # Minimal canonical definitions if simulation package is not yet fully linked
    from enum import Enum
    class SimulationMode(Enum):
        PAPER = "paper"
        BACKTEST = "backtest"
        STRESS = "stress"

    class SimulationOrchestrator:
        def __init__(self, config=None): pass

# Type stubs for completeness if missing elsewhere
from dataclasses import dataclass
from typing import Any
@dataclass
class SimulationConfig:
    mode: Any = None

@dataclass
class SimulationResult:
    success: bool = True

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
    'IgnoranceScoreEngine',
    'UncertaintyEngine',

    # Planning and Orchestration
    'PlanningEngine',
    'FutureSimulator',
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
]
