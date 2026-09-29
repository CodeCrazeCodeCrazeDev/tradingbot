"""Hypothesis Engine and Research OS contracts."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, List, Optional
import time


class HypothesisStatus(Enum):
    GENERATED = "GENERATED"
    UNDER_REVIEW = "UNDER_REVIEW"
    BACKTESTING = "BACKTESTING"
    WALK_FORWARD = "WALK_FORWARD"
    OUT_OF_SAMPLE = "OUT_OF_SAMPLE"
    VALIDATED = "VALIDATED"
    REJECTED = "REJECTED"


@dataclass
class Hypothesis:
    """Scientific trade/market hypothesis schema."""
    hypothesis_id: str
    origin: str  # e.g., LLM_Research, ML_Pattern, Human
    mechanism: str  # Economic/structural justification
    predictions: List[str]
    required_data: List[str]
    null_hypothesis: str
    alternative_hypothesis: str
    evaluation_protocol: Dict[str, Any]
    status: HypothesisStatus = HypothesisStatus.GENERATED
    created_at: float = field(default_factory=time.time)
    p_value: Optional[float] = None
    deflated_sharpe: Optional[float] = None
    pbo_probability: Optional[float] = None  # Probability of Backtest Overfitting
    rejection_reason: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
