"""
COS Type Definitions
====================

All data structures that flow through the Cognitive Operating System loop.

Each type is designed to carry both content and provenance — every piece of
knowledge knows where it came from, every decision knows what produced it,
and every correction knows what it corrected.
"""

from __future__ import annotations

import numpy as np
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4


# ── Enums ──────────────────────────────────────────────────────────────────

class KnowledgeCategory(Enum):
    """What kind of knowledge is this node?"""
    MARKET_REGIME = "market_regime"
    STRATEGY_PERFORMANCE = "strategy_performance"
    CAUSAL_RELATION = "causal_relation"
    RISK_INSIGHT = "risk_insight"
    EXECUTION_LESSON = "execution_lesson"
    SIMULATION_CALIBRATION = "simulation_calibration"
    META_COGNITIVE = "meta_cognitive"       # insights about the COS itself
    DOMAIN_PRIOR = "domain_prior"            # external research / priors
    TEMPORAL_PATTERN = "temporal_pattern"
    CORRELATION_STRUCTURE = "correlation_structure"


class IdeaStatus(Enum):
    """Lifecycle of an idea through the COS loop."""
    CANDIDATE = "candidate"          # just generated
    SIMULATED = "simulated"          # dream-tested
    VALIDATED = "validated"          # passed simulation
    DEPLOYED = "deployed"            # fed to execution
    CONFIRMED = "confirmed"          # reality matched prediction
    REFUTED = "refuted"              # reality contradicted prediction
    ARCHIVED = "archived"            # stored for future reference


class DecisionConfidence(Enum):
    """How confident is the COS in a decision?"""
    SPECULATIVE = 0.0
    LOW = 0.25
    MEDIUM = 0.5
    HIGH = 0.75
    CONCRETE = 1.0


class SimulationFidelity(Enum):
    """How well does the simulation match reality?"""
    UNCALIBRATED = 0.0
    POOR = 0.25
    APPROXIMATE = 0.5
    GOOD = 0.75
    CALIBRATED = 1.0


# ── Core Data Structures ───────────────────────────────────────────────────

@dataclass
class KnowledgeNode:
    """
    A single unit of structured knowledge in the Cognition Store.

    Every node is:
      - Embedding-indexed for semantic retrieval
      - Provenance-tagged for trust scoring
      - Validated against reality for calibration
    """
    node_id: str = field(default_factory=lambda: uuid4().hex[:12])
    category: KnowledgeCategory = KnowledgeCategory.DOMAIN_PRIOR

    # Content
    title: str = ""
    content: str = ""                    # natural language summary
    structured_data: Dict[str, Any] = field(default_factory=dict)  # machine-readable payload

    # Embedding for semantic search
    embedding: Optional[np.ndarray] = None

    # Provenance
    source: str = ""                     # "simulation", "real_trade", "research", "meta"
    parent_ids: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    # Validation
    validation_count: int = 0
    validation_score: float = 0.0        # -1.0 (refuted) to +1.0 (confirmed)
    last_validated_at: Optional[datetime] = None

    # Usage tracking
    retrieval_count: int = 0
    decision_impact_count: int = 0       # how many decisions cited this node

    # Salience — how important is this right now?
    salience: float = 0.5                # 0..1, decays over time unless refreshed

    def refresh_salience(self, decay: float = 0.95):
        """Time-decay salience unless recently validated."""
        if self.last_validated_at:
            hours_since = (datetime.utcnow() - self.last_validated_at).total_seconds() / 3600
            boost = max(0, 1.0 - hours_since / 24.0)  # validated in last 24h → boost
            self.salience = self.salience * decay + boost * (1 - decay)
        else:
            self.salience *= decay


@dataclass
class Idea:
    """
    A candidate strategy, hypothesis, or modification to be tested.

    Ideas flow through: CANDIDATE → SIMULATED → VALIDATED → DEPLOYED → CONFIRMED/REFUTED
    """
    idea_id: str = field(default_factory=lambda: uuid4().hex[:12])
    title: str = ""
    description: str = ""
    motivation: str = ""                 # why was this idea generated?

    # What knowledge nodes inspired this idea?
    source_node_ids: List[str] = field(default_factory=list)

    # The actual proposal — can be a strategy config, a parameter change, etc.
    proposal: Dict[str, Any] = field(default_factory=dict)

    # Simulation results (filled by CalibratedSimulationEngine)
    simulation_results: List["SimulationResult"] = field(default_factory=list)
    expected_pnl: float = 0.0
    expected_risk: float = 0.0
    simulation_confidence: float = 0.0

    # Reality results (filled by RealityCalibrationLoop)
    actual_pnl: Optional[float] = None
    actual_risk: Optional[float] = None
    reality_gap: Optional[float] = None   # |expected - actual|

    # Lifecycle
    status: IdeaStatus = IdeaStatus.CANDIDATE
    created_at: datetime = field(default_factory=datetime.utcnow)
    deployed_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None

    # Priority for simulation queue
    priority: float = 0.5                # 0..1


@dataclass
class SimulationResult:
    """
    Output of a single simulation run on an Idea.

    Captures what the simulation predicted, how confident it is,
    and which scenarios were tested.
    """
    sim_id: str = field(default_factory=lambda: uuid4().hex[:12])
    idea_id: str = ""

    # Scenario tested
    scenario_name: str = ""
    scenario_params: Dict[str, Any] = field(default_factory=dict)
    market_regime: str = "normal"
    duration_steps: int = 100

    # Predicted outcomes
    predicted_pnl: float = 0.0
    predicted_risk: float = 0.0
    predicted_sharpe: float = 0.0
    predicted_max_drawdown: float = 0.0
    win_rate: float = 0.0

    # Confidence in this prediction
    confidence: float = 0.0
    fidelity: SimulationFidelity = SimulationFidelity.UNCALIBRATED

    # Trajectory data (compressed)
    trajectory_summary: Dict[str, Any] = field(default_factory=dict)

    # Which knowledge nodes were used to build this simulation
    used_node_ids: List[str] = field(default_factory=list)

    # Metadata
    timestamp: datetime = field(default_factory=datetime.utcnow)
    simulation_mode: str = "dream"       # "dream", "counterfactual", "stress_test"


@dataclass
class DecisionTrace:
    """
    Complete provenance of a decision: which knowledge, which ideas,
    which simulations led to this action.

    This is the "explanation" that feeds back into the Cognition Store
    as meta-cognitive knowledge.
    """
    trace_id: str = field(default_factory=lambda: uuid4().hex[:12])
    decision_id: str = ""

    # What action was taken
    action: str = ""                      # "BUY", "SELL", "HOLD", "ADJUST_RISK", etc.
    action_params: Dict[str, Any] = field(default_factory=dict)

    # Provenance chain
    knowledge_node_ids: List[str] = field(default_factory=list)
    idea_ids: List[str] = field(default_factory=list)
    simulation_ids: List[str] = field(default_factory=list)

    # Confidence
    confidence: DecisionConfidence = DecisionConfidence.MEDIUM
    confidence_score: float = 0.5

    # Reasoning
    reasoning_chain: List[str] = field(default_factory=list)

    # Expected outcome (from simulation)
    expected_pnl: float = 0.0
    expected_risk: float = 0.0

    # Actual outcome (filled later by feedback)
    actual_pnl: Optional[float] = None
    actual_risk: Optional[float] = None

    # Timestamps
    decided_at: datetime = field(default_factory=datetime.utcnow)
    resolved_at: Optional[datetime] = None


@dataclass
class RealityCheck:
    """
    Comparison of predicted vs actual outcome.

    This is the core signal that drives model correction.
    """
    check_id: str = field(default_factory=lambda: uuid4().hex[:12])
    trace_id: str = ""

    # Prediction
    predicted_pnl: float = 0.0
    predicted_risk: float = 0.0
    predicted_regime: str = ""

    # Reality
    actual_pnl: float = 0.0
    actual_risk: float = 0.0
    actual_regime: str = ""

    # Gaps
    pnl_gap: float = 0.0                 # predicted - actual
    risk_gap: float = 0.0
    regime_match: bool = True

    # Assessment
    prediction_quality: float = 0.0       # 0 (completely wrong) to 1 (spot on)
    was_profitable: bool = False
    was_expected_profitable: bool = False

    # Which knowledge/simulation led to the prediction
    node_ids: List[str] = field(default_factory=list)
    simulation_ids: List[str] = field(default_factory=list)

    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class CalibrationDelta:
    """
    A correction to the simulation model derived from a RealityCheck.

    This is what makes the COS "smarter over time" — every mismatch
    between prediction and reality produces a calibration delta that
    updates the simulation model and the knowledge base.
    """
    delta_id: str = field(default_factory=lambda: uuid4().hex[:12])
    check_id: str = ""

    # What was wrong
    error_type: str = ""                  # "regime_mismatch", "pnl_bias", "risk_underestimate"
    error_magnitude: float = 0.0

    # What to correct
    corrections: Dict[str, Any] = field(default_factory=dict)

    # Which knowledge nodes need updating
    node_ids_to_update: List[str] = field(default_factory=list)

    # Which simulation parameters need adjusting
    simulation_param_deltas: Dict[str, float] = field(default_factory=dict)

    # Meta: should the COS itself change how it operates?
    meta_cognitive_correction: Optional[Dict[str, Any]] = None

    # Impact tracking
    applied: bool = False
    applied_at: Optional[datetime] = None
    resulting_improvement: Optional[float] = None

    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class COSCycleReport:
    """
    Summary of one complete COS loop iteration.

    Produced every cycle for observability and meta-cognitive learning.
    """
    cycle_id: str = field(default_factory=lambda: uuid4().hex[:12])
    cycle_number: int = 0

    # Phase timings
    knowledge_retrieval_ms: float = 0.0
    idea_generation_ms: float = 0.0
    simulation_ms: float = 0.0
    decision_ms: float = 0.0
    execution_ms: float = 0.0
    feedback_ms: float = 0.0
    calibration_ms: float = 0.0
    total_cycle_ms: float = 0.0

    # Counts
    nodes_retrieved: int = 0
    ideas_generated: int = 0
    ideas_simulated: int = 0
    decisions_made: int = 0
    reality_checks: int = 0
    calibration_deltas: int = 0

    # Quality metrics
    avg_simulation_fidelity: float = 0.0
    avg_prediction_quality: float = 0.0
    calibration_score: float = 0.0        # rolling average of prediction_quality

    # State
    knowledge_store_size: int = 0
    pending_ideas: int = 0
    active_simulations: int = 0

    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class COSConfig:
    """Configuration for the Cognitive Operating System."""
    # Cognition Store
    store_capacity: int = 100000
    embedding_dim: int = 64
    use_faiss: bool = True
    salience_decay: float = 0.95
    salience_refresh_on_validation: bool = True

    # Simulation Engine
    num_dream_scenarios: int = 10
    dream_horizon_steps: int = 100
    stress_test_scenarios: int = 5
    counterfactual_depth: int = 3
    min_simulation_confidence: float = 0.3
    fidelity_target: SimulationFidelity = SimulationFidelity.GOOD

    # Decision Support
    min_confidence_to_execute: float = 0.4
    max_concurrent_ideas: int = 20
    idea_priority_decay: float = 0.9

    # Feedback Loop
    reality_check_interval_seconds: float = 60.0
    calibration_learning_rate: float = 0.1
    min_checks_for_calibration: int = 5

    # Loop Control
    cycle_interval_seconds: float = 30.0
    max_cycle_duration_seconds: float = 25.0
    enable_meta_cognition: bool = True     # COS learns about itself

    # Persistence
    storage_path: str = "cos_data"
    auto_save_interval_cycles: int = 10

    # Integration
    cognitive_architecture_enabled: bool = True
    world_model_enabled: bool = True
    decision_layer_enabled: bool = True
    feedback_analyzer_enabled: bool = True
