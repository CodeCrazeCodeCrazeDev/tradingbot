import datetime
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, Optional

@dataclass
class AgentScorecard:
    """
    Enterprise-grade AgentScorecard capturing deep, rolling multi-agent performance metrics.
    Completely backward-compatible with 3 standard fields, but extensively featured for
    high-frequency and production observability under the UCA-2026 specification.
    """
    expected_contribution: float
    precision: float
    recall: float
    agent_id: Optional[str] = None
    role: Optional[str] = None
    debate_id: Optional[str] = None
    hypothesis_id: Optional[str] = None
    confidence: float = 0.0
    calibrated_confidence: float = 0.0
    uncertainty: float = 0.0
    actual_contribution: float = 0.0
    evidence_quality: float = 0.0
    evidence_count: int = 0
    contradiction_count: int = 0
    falsification_score: float = 0.0
    agreement_score: float = 0.0
    disagreement_score: float = 0.0
    calibration_error: float = 0.0
    latency: float = 0.0
    token_usage: int = 0
    computational_cost: float = 0.0
    reliability_score: float = 1.0
    historical_accuracy: float = 0.0
    Bayesian_update: float = 0.0
    verifier_consensus: float = 0.0
    timestamp: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert scorecard metrics to a JSON-serializable dictionary."""
        data = asdict(self)
        if self.timestamp is None:
            data['timestamp'] = datetime.datetime.now().isoformat()
        return data
