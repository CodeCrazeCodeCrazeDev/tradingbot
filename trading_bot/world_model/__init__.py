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
class ImaginationPlanner: pass
class PlanResult: pass
class CEMPlanner: pass

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

# Authoritative Compatibility Stubs for Legacy Migration

class SimulationOrchestrator:
    def __init__(self, config=None):
        self.config = config or {}
        self.running = False
    async def start(self): self.running = True
    async def stop(self): self.running = False
    def get_status(self): return {"running": self.running}

class SimulationConfig: pass
class SimulationMode: pass
class SimulationResult: pass

class WorldModel:
    """Legacy WorldModel adapter pointing to WorldModelV2."""
    def __init__(self, config=None):
        self.config = config or {}
        self.core = WorldModelV2({"equities": 20, "fx": 10, "macro": 5})
    def predict(self, state):
        return self.core(state)

__all__ = [
    # Canonical WM-V2/V3
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
