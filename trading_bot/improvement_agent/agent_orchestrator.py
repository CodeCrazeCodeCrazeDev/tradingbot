"""
Improvement Agent Orchestrator
============================================================

Core agent primitives for the improvement_agent subsystem:
the ImprovementAgent plus its config/mode/state/directive types.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class AgentMode(Enum):
    OBSERVE = "observe"          # analysis only, no changes proposed
    PROPOSE = "propose"          # propose improvements, no application
    APPLY = "apply"              # apply approved improvements
    AUTONOMOUS = "autonomous"    # full loop within governance


class AgentState(Enum):
    IDLE = "idle"
    ANALYZING = "analyzing"
    PROPOSING = "proposing"
    WAITING_APPROVAL = "waiting_approval"
    APPLYING = "applying"
    HALTED = "halted"


@dataclass
class AgentConfig:
    """Configuration for an ImprovementAgent."""
    mode: AgentMode = AgentMode.OBSERVE
    max_proposals_per_cycle: int = 5
    require_human_approval: bool = True
    scan_interval_seconds: float = 300.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentDirective:
    """An instruction issued to the agent."""
    directive_id: str
    action: str
    payload: Dict[str, Any] = field(default_factory=dict)
    issued_at: datetime = field(default_factory=datetime.now)
    priority: int = 0


class ImprovementAgent:
    """Agent that detects weaknesses and proposes improvements."""

    def __init__(self, config: Optional[AgentConfig] = None):
        self.config = config or AgentConfig()
        self.state = AgentState.IDLE
        self.directives: List[AgentDirective] = []
        self.proposals: List[Any] = []
        logger.info(f"ImprovementAgent initialized (mode={self.config.mode.value})")

    def issue_directive(self, directive: AgentDirective) -> None:
        self.directives.append(directive)

    async def analyze(self, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        self.state = AgentState.ANALYZING
        try:
            return {"findings": [], "context": context or {}}
        finally:
            self.state = AgentState.IDLE

    async def propose(self, findings: Optional[List[Any]] = None) -> List[Any]:
        self.state = AgentState.PROPOSING
        try:
            return list(findings or [])[: self.config.max_proposals_per_cycle]
        finally:
            self.state = AgentState.IDLE

    def status(self) -> Dict[str, Any]:
        return {
            "state": self.state.value,
            "mode": self.config.mode.value,
            "directives_pending": len(self.directives),
            "proposals": len(self.proposals),
        }
