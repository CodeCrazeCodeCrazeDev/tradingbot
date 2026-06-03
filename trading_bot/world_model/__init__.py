"""
Phase 4: World Models & Simulation
DreamerV3-style world model for market prediction

Layered Architecture (L0–L10):
  L0: World Fabric Simulator — active domain randomization, curriculum generation
  L1: Multimodal Perception — event segmentation, surprise reservoir
  L2: Object-Centric Scene State — slot attention, probabilistic causal graphs
  L3: World Model Ensemble — JEPA×Dreamer RSSM, Skip-Graph, temporal consistency
  L4: Belief State + Memory — SSM belief tracker, HDC episodic memory, OCHL
  L5: Counterfactual Simulator — two-phase rollout, graph repair, constraint checking
  L6: Value/Constraint/Curiosity — successor features, exploration value
  L7: Hierarchical Planner — CEM over latent options, MPPI fallback
  L8: Actor-Controller — EBM/IBC, LQR, diffusion policy
  L9: Meta-Learning — Change Control Board, shadow networks, active experiments
  L10: Governance/Verifier — LTL runtime shield, formal methods light
"""

# L1 + L3: Latent Dynamics (Perception + World Model Ensemble)
from .latent_dynamics import (
    WorldModel,
    MarketStateEncoder,
    MarketStateDecoder,
    LatentDynamicsModel,
    RewardPredictor,
    # L1: Multimodal Perception
    StreamModality,
    MultimodalFrame,
    TemporalSegmentNetwork,
    SurpriseReservoir,
    MultimodalPerceptionEncoder,
    # L3: World Model Ensemble
    JEPALatentPredictor,
    FastRSSMModel,
    JumpMacroTransitionModel,
    MoEGatingNetwork,
    EnsembleWorldModel,
    # B1 Ceiling-Pushed: Triangulated Consistency
    ObservationReAnchorer,
    UncertaintyHorizonGate,
    MacroActionHierarchy,
    LongHorizonDistiller,
)

# L7 + L8: Imagination-Based Planning
from .imagination import (
    ImaginationPlanner,
    # L7: Hierarchical Planner
    PlanResult,
    CEMPlanner,
    # L8: Actor-Controller
    EnergyBasedPolicy,
    LQRTracker,
    DiffusionPolicyHead,
    ActorController,
    # L7 ceiling-push
    RiskAwarePlanResult,
    RiskAwareCVaRPlanner,
    PlanRepairEngine,
    TemporalBoundaryConsistencyChecker,
    # L8 ceiling-push
    ContactMode,
    ContactModeDecision,
    ContactModeSwitcher,
    ComplianceAction,
    ComplianceController,
    ResidualDiffusionRefiner,
    # Cross-cutting loops
    AdversarialSelfPlay,
    CausalAgentLoop,
    DreamAndVerifyLoop,
)

# L2 + L5: Counterfactual Engine (Object-Centric + Counterfactual Simulator)
from .counterfactual_engine import (
    CounterfactualEngine,
    # L2: Object-Centric Scene State
    EdgeType,
    ProbabilisticEdge,
    InterventionOperator,
    ObjectSlot,
    ObjectSceneGraph,
    SlotAttentionEncoder,
    RelationalGraphNetwork,
    # L5: Counterfactual Simulator
    RolloutOutput,
    CounterfactualSimulator,
    CausalReasoningModule,
    # B2 Ceiling-Pushed: Intervention Targets, Invariance, Active Probing
    InterventionTargetSelector,
    EnvironmentInvarianceTester,
    ActiveProbingLoop,
)

# L4 + L6: Experience Replay (Belief State + Value/Curiosity)
from .experience_replay import (
    ExperienceReplayBuffer,
    Experience,
    # L4: Belief State + Memory
    S4Block,
    HyperdimensionalEncoder,
    SkillMemoryEntry,
    BeliefStateTracker,
    # L6: Value/Constraint/Curiosity
    SuccessorFeatureNetwork,
    CuriosityDrive,
    # B3 Ceiling-Pushed: Backward Causal Responsibility, Repair, Relabeling
    OptionTransition,
    BackwardCausalResponsibility,
    PreconditionTerminationRepair,
    DualObjectiveRelabeler,
    FailureModeReplayQueues,
)

# L0: Synthetic Data (World Fabric Simulator)
from .synthetic_data import (
    SyntheticMarketGenerator,
    MarketScenario,
    MarketRegime,
    # L0: World Fabric Simulator
    DomainRandomizationConfig,
    CurriculumLevel,
    WorldFabricSimulator,
    # L0 Ceiling-Pushed: Staged Randomization, Real-Anchored Sim, Shielded Eval
    RandomizationStage,
    ContinualStagedRandomizer,
    RealAnchoredSimCoTrainer,
    ShieldedCurriculumEvaluator,
)

# L10: Governance/Verifier (Runtime Shield)
from .simulation_orchestrator import (
    SimulationOrchestrator,
    SimulationConfig,
    SimulationMode,
    SimulationResult,
    # L10: Governance/Verifier
    LTLFormula,
    RuntimeShield,
    DegradationLevel,
    ShieldDecision,
    PredictiveShield,
    create_runtime_shield,
)

from .world_state import (
    MarketWorldState,
    VolatilityRegime,
    LiquidityCondition,
    SystemMode,
)

from .ignorance_score import (
    IgnoranceScoreEngine,
)

__all__ = [
    # Legacy
    'WorldModel',
    'MarketStateEncoder',
    'MarketStateDecoder',
    'LatentDynamicsModel',
    'RewardPredictor',
    'ImaginationPlanner',
    'SyntheticMarketGenerator',
    'MarketScenario',
    'MarketRegime',
    'ExperienceReplayBuffer',
    'Experience',
    'CounterfactualEngine',
    'SimulationOrchestrator',
    'SimulationConfig',
    'SimulationMode',
    'SimulationResult',
    # L1: Multimodal Perception
    'StreamModality',
    'MultimodalFrame',
    'TemporalSegmentNetwork',
    'SurpriseReservoir',
    'MultimodalPerceptionEncoder',
    # L2: Object-Centric Scene State
    'EdgeType',
    'ProbabilisticEdge',
    'InterventionOperator',
    'ObjectSlot',
    'ObjectSceneGraph',
    'SlotAttentionEncoder',
    'RelationalGraphNetwork',
    # L3: World Model Ensemble
    'JEPALatentPredictor',
    'FastRSSMModel',
    'JumpMacroTransitionModel',
    'MoEGatingNetwork',
    'EnsembleWorldModel',
    # L4: Belief State + Memory
    'S4Block',
    'HyperdimensionalEncoder',
    'SkillMemoryEntry',
    'BeliefStateTracker',
    # L5: Counterfactual Simulator
    'RolloutOutput',
    'CounterfactualSimulator',
    'CausalReasoningModule',
    # L6: Value/Constraint/Curiosity
    'SuccessorFeatureNetwork',
    'CuriosityDrive',
    # L7: Hierarchical Planner
    'PlanResult',
    'CEMPlanner',
    # L8: Actor-Controller
    'EnergyBasedPolicy',
    'LQRTracker',
    'DiffusionPolicyHead',
    'ActorController',
    'RiskAwarePlanResult',
    'RiskAwareCVaRPlanner',
    'PlanRepairEngine',
    'TemporalBoundaryConsistencyChecker',
    # L8/L10 ceiling-push + cross-cut loops
    'AdversarialSelfPlay',
    'ComplianceAction',
    'ComplianceController',
    'ContactMode',
    'ContactModeDecision',
    'ContactModeSwitcher',
    'CausalAgentLoop',
    'DegradationLevel',
    'DreamAndVerifyLoop',
    'PredictiveShield',
    'ResidualDiffusionRefiner',
    'ShieldDecision',
    # L0: World Fabric Simulator
    'DomainRandomizationConfig',
    'CurriculumLevel',
    'WorldFabricSimulator',
    # L10: Governance/Verifier
    'LTLFormula',
    'RuntimeShield',
    'create_runtime_shield',
    # Governance
    'MarketWorldState',
    'VolatilityRegime',
    'LiquidityCondition',
    'SystemMode',
    'IgnoranceScoreEngine',
    # B1 Ceiling-Pushed: Triangulated Consistency
    'ObservationReAnchorer',
    'UncertaintyHorizonGate',
    'MacroActionHierarchy',
    'LongHorizonDistiller',
    # B2 Ceiling-Pushed: Intervention Targets, Invariance, Active Probing
    'InterventionTargetSelector',
    'EnvironmentInvarianceTester',
    'ActiveProbingLoop',
    # B3 Ceiling-Pushed: Backward Causal Responsibility, Repair, Relabeling
    'OptionTransition',
    'BackwardCausalResponsibility',
    'PreconditionTerminationRepair',
    'DualObjectiveRelabeler',
    'FailureModeReplayQueues',
    # L0 Ceiling-Pushed: Staged Randomization, Real-Anchored Sim, Shielded Eval
    'RandomizationStage',
    'ContinualStagedRandomizer',
    'RealAnchoredSimCoTrainer',
    'ShieldedCurriculumEvaluator',
]
