"""AI Core Agents - planner/verifier/safety/executor orchestration."""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class AgentRole(Enum):
    PLANNER = "planner"
    VERIFIER = "verifier"
    EXECUTOR = "executor"
    SAFETY_VALIDATOR = "safety_validator"
    MONITOR = "monitor"


class DecisionStatus(Enum):
    PROPOSED = "proposed"
    VALIDATED = "validated"
    REJECTED = "rejected"
    EXECUTED = "executed"
    FAILED = "failed"


@dataclass
class TradingDecision:
    action: str
    confidence: float
    reasoning: str = ""
    status: DecisionStatus = DecisionStatus.PROPOSED
    metadata: Dict[str, Any] = field(default_factory=dict)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    @property
    def is_actionable(self) -> bool:
        return self.action.lower() not in {"hold", "wait", "none", ""}


class BaseAgent:
    """Base class for orchestrated agents."""

    def __init__(self, agent_id: str = None, role: AgentRole = None, **kwargs: Any):
        self.agent_id = agent_id or str(uuid.uuid4())[:8]
        self.role = role
        self.performance_history: List[Dict[str, Any]] = []
        for k, v in kwargs.items():
            setattr(self, k, v)

    def update_performance(self, metric: float) -> None:
        self.performance_history.append({"metric": metric, "timestamp": datetime.now()})

    def get_status(self) -> Dict[str, Any]:
        return {
            "status": "operational",
            "agent_id": self.agent_id,
            "role": self.role.value if self.role else None,
        }


class PlannerAgent(BaseAgent):
    def __init__(self, agent_id: str = None, **kwargs: Any):
        super().__init__(agent_id=agent_id, role=AgentRole.PLANNER, **kwargs)


class VerifierAgent(BaseAgent):
    def __init__(self, agent_id: str = None, **kwargs: Any):
        super().__init__(agent_id=agent_id, role=AgentRole.VERIFIER, **kwargs)


class SafetyValidatorAgent(BaseAgent):
    def __init__(self, agent_id: str = None, **kwargs: Any):
        super().__init__(agent_id=agent_id, role=AgentRole.SAFETY_VALIDATOR, **kwargs)


class ExecutorAgent(BaseAgent):
    def __init__(self, agent_id: str = None, **kwargs: Any):
        super().__init__(agent_id=agent_id, role=AgentRole.EXECUTOR, **kwargs)


class AgentOrchestrator:
    """Coordinates the planner/verifier/safety/executor agent chain."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.planner = PlannerAgent()
        self.verifier = VerifierAgent()
        self.safety_validator = SafetyValidatorAgent()
        self.executor = ExecutorAgent()
        self.running = False

    def get_status(self) -> Dict[str, Any]:
        return {
            "status": "operational",
            "running": self.running,
            "agents": ["planner", "verifier", "safety_validator", "executor"],
        }
