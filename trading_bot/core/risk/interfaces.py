from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

@dataclass
class RiskResult:
    evaluator_name: str
    approved: bool
    risk_score: float  # 0.0 to 1.0
    confidence: float  # 0.0 to 1.0
    violated_constraints: List[str] = field(default_factory=list)
    evidence: Dict[str, Any] = field(default_factory=dict)
    recommended_position_size: Optional[float] = None
    emergency_stop: bool = False
    audit_trace: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.utcnow)

class IRiskEvaluator(ABC):
    @abstractmethod
    async def evaluate(self, params: Dict[str, Any], context: Dict[str, Any]) -> RiskResult:
        """Evaluate risk for a specific action or state."""
        pass
