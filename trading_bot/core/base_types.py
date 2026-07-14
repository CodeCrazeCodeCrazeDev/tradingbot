"""
AlphaAlgo UCA V5 Base Types
==========================

Canonical dependency-free domain primitives for the AlphaAlgo system.
Ensures system-wide consistency for core data structures.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union
from uuid import uuid4

class ActionStatus(Enum):
    PROPOSED = "proposed"
    AUDITING = "auditing"
    APPROVED = "approved"
    VETOED = "vetoed"
    EXECUTED = "executed"
    FAILED = "failed"

class DecisionOutcome(Enum):
    TRADE_APPROVED = "trade_approved"
    TRADE_REJECTED = "trade_rejected"
    NO_TRADE_MARKET_HOSTILE = "no_trade_market_hostile"
    INCONCLUSIVE = "inconclusive"
    ERROR = "error"

@dataclass
class ConfidenceVector:
    """Multi-dimensional confidence (no single scores)"""
    statistical: float          # Historical expectancy
    regime: float              # Regime validity
    execution: float           # Execution feasibility
    tail_risk: float           # Tail risk bounded
    model_stability: float     # Model reliability

    sample_size: int = 0
    regime_novelty_penalty: float = 0.0
    alpha_decay_factor: float = 1.0

    def min_confidence(self) -> float:
        return min(self.statistical, self.regime, self.execution, self.tail_risk, self.model_stability)

@dataclass
class SystemContext:
    """Represents the global state of the AlphaAlgo system at a point in time."""
    timestamp: datetime = field(default_factory=datetime.utcnow)
    market_state: Dict[str, Any] = field(default_factory=dict)
    portfolio_state: Dict[str, Any] = field(default_factory=dict)
    agent_states: Dict[str, Any] = field(default_factory=dict)
    pending_decisions: List[Any] = field(default_factory=list)
    recent_outcomes: List[Any] = field(default_factory=list)
    risk_metrics: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class Decision:
    """Represents a strategic decision."""
    decision_id: str = field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = field(default_factory=datetime.utcnow)
    outcome: DecisionOutcome = DecisionOutcome.INCONCLUSIVE
    expected_value: float = 0.0
    confidence_vector: Optional[ConfidenceVector] = None
    reasoning: str = ""
    decision_type: str = "unknown"
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def confidence(self) -> float:
        if self.confidence_vector:
            return self.confidence_vector.min_confidence()
        return 0.0

    def is_safe(self) -> bool:
        return self.outcome == DecisionOutcome.TRADE_APPROVED and self.confidence > 0.7

@dataclass
class Action:
    """Represents an executable intent (LogAction)."""
    action_id: str = field(default_factory=lambda: str(uuid4()))
    action_type: str = "unknown"
    payload: Dict[str, Any] = field(default_factory=dict)
    source_agent: str = "system"
    timestamp: datetime = field(default_factory=datetime.utcnow)
    status: ActionStatus = ActionStatus.PROPOSED
    correlation_id: Optional[str] = None
    sequence_number: Optional[int] = None
    voter_reports: Dict[str, Any] = field(default_factory=dict)

@dataclass
class Observation:
    """Raw data ingestion unit."""
    timestamp: datetime = field(default_factory=datetime.utcnow)
    source: str = ""
    data: Dict[str, Any] = field(default_factory=dict)

@dataclass
class Evidence:
    """Verified fact or derivative used in reasoning."""
    evidence_id: str = field(default_factory=lambda: str(uuid4()))
    claim: str = ""
    source_observation_ids: List[str] = field(default_factory=list)
    confidence: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class Hypothesis:
    """Falsifiable market thesis."""
    hypothesis_id: str = field(default_factory=lambda: str(uuid4()))
    description: str = ""
    predicted_outcome: str = ""
    confidence_interval: Tuple[float, float] = (0.0, 0.0)

@dataclass
class RiskAssessment:
    """Evaluation of potential downside for an action."""
    risk_score: float = 0.0
    va_r: float = 0.0
    cva_r: float = 0.0
    warnings: List[str] = field(default_factory=list)

@dataclass
class ExecutionPlan:
    """Sequence of instructions for order fulfillment."""
    plan_id: str = field(default_factory=lambda: str(uuid4()))
    steps: List[Dict[str, Any]] = field(default_factory=list)
    algo_type: str = "VWAP"
