"""
Master Orchestrator

Provides backward compatibility for consolidated hierarchical orchestrators.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from enum import Enum

logger = logging.getLogger(__name__)

class DecisionPriority(Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class SystemContext:
    timestamp: datetime = field(default_factory=datetime.utcnow)
    market_state: Dict[str, Any] = field(default_factory=dict)
    portfolio_state: Dict[str, Any] = field(default_factory=dict)
    agent_states: Dict[str, Any] = field(default_factory=dict)
    pending_decisions: List[Any] = field(default_factory=list)
    recent_outcomes: List[Any] = field(default_factory=list)
    risk_metrics: Dict[str, Any] = field(default_factory=dict)

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
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        import warnings
        warnings.warn(
            "MasterOrchestrator is a deprecated duplicate; canonical "
            "orchestrator is trading_bot.core.csc.controller."
            "CognitiveSystemController.",
            DeprecationWarning,
            stacklevel=2,
        )
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
            reasoning="Default MasterOrchestrator implementation."
        )

    async def _generate_candidate_actions(self, context: SystemContext) -> List[Dict[str, Any]]:
        candidates = [
            {"type": "hold", "action": {}, "probability": 0.9, "priority": DecisionPriority.NORMAL},
            {"type": "buy", "action": {"operation": "open_long"}, "confidence": 0.7, "source_agent": "agent1", "priority": DecisionPriority.HIGH}
        ]
        return candidates

    async def _evaluate_candidates(self, context: SystemContext, candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        for c in candidates:
            c["value"] = 0.8
        return candidates

    async def _mcts_search(self, context: SystemContext, candidates: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not candidates:
            return {"type": "hold"}
        return max(candidates, key=lambda x: x.get("value", 0.0))

    async def learn(self, experience: Dict[str, Any]):
        pass

    def get_status(self) -> Dict[str, Any]:
        return {"state": "active" if self.initialized else "inactive", "safety_threshold": 0.7}

__all__ = [
    'DecisionPriority',
    'SystemContext',
    'Decision',
    'MasterOrchestrator',
]
