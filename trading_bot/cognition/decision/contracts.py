"""Decision Intelligence and Risk Gatekeeper contracts."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, List, Optional
import time


class CognitiveAction(Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"
    WAIT = "WAIT"
    REDUCE = "REDUCE"
    EXIT = "EXIT"
    ABSTAIN = "ABSTAIN"


@dataclass
class DecisionProposal:
    """Structured decision object produced by Decision Intelligence."""
    decision_id: str
    action: CognitiveAction
    instrument: str
    direction: Optional[str] = None  # LONG, SHORT, None
    entry_price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    proposed_position_size: float = 0.0
    expected_value: float = 0.0
    uncertainty: float = 0.0
    confidence: float = 0.0
    calibrated_probability: float = 0.0
    regime: str = "transitional"
    supporting_evidence: List[str] = field(default_factory=list)
    contradicting_evidence: List[str] = field(default_factory=list)
    invalidation_conditions: List[str] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)


@dataclass
class RiskGateResult:
    """Outcome of rigid Risk Gatekeeper evaluation."""
    proposal_id: str
    authorized: bool
    authorized_action: CognitiveAction
    authorized_size: float
    rejection_reason: Optional[str] = None
    hard_limit_violations: List[str] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)
