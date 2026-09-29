"""Model Router contracts and task classification."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, Optional


class TaskCategory(Enum):
    ARITHMETIC_DETERMINISTIC = "ARITHMETIC_DETERMINISTIC"
    SPECIALIZED_ML_PREDICTION = "SPECIALIZED_ML_PREDICTION"
    STRUCTURED_REASONING = "STRUCTURED_REASONING"
    RESEARCH_SYNTHESIS = "RESEARCH_SYNTHESIS"
    INDEPENDENT_VERIFICATION = "INDEPENDENT_VERIFICATION"


@dataclass
class TaskRequest:
    task_id: str
    category: TaskCategory
    payload: Dict[str, Any]
    max_latency_ms: float = 100.0
    cost_budget: float = 0.05
    required_reliability: float = 0.99


@dataclass
class TaskResponse:
    task_id: str
    category: TaskCategory
    result: Any
    provider_used: str
    latency_ms: float
    cost_estimated: float
    success: bool
    error_message: Optional[str] = None
