
"""
Provides backward compatibility for consolidated hierarchical orchestrators.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum

logger = logging.getLogger(__name__)

class DecisionPriority(Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class SystemContext:
    timestamp: datetime
    market_state: Dict[str, Any]
    portfolio_state: Dict[str, Any]
    agent_states: Dict[str, Any]
    pending_decisions: List[Any]
    recent_outcomes: List[Any]
    risk_metrics: Dict[str, Any]

@dataclass
class Decision:
    decision_type: str
    expected_value: float
    safety_score: float
    reasoning: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def is_safe(self) -> bool:
        return self.safety_score > 0.7

class MasterOrchestrator:
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.initialized = False

    async def initialize(self):
        self.initialized = True

    def inject_dependencies(self, **kwargs):
        pass

    async def think(self, context: SystemContext) -> Decision:
        return Decision(
            decision_type="NO_ACTION",
            expected_value=0.0,
            safety_score=1.0,
            reasoning="Default MasterOrchestrator stub."
        )

    async def learn(self, experience: Dict[str, Any]):
        pass

    def get_status(self) -> Dict[str, Any]:
        return {"state": "active" if self.initialized else "inactive", "safety_threshold": 0.7}
