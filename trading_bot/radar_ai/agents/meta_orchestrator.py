"""
RadarAI Meta-Orchestrator
============================================================

Agent-registry front-end over the canonical MetaOrchestrator,
plus the WorkflowStage enum used by the agent demos.
"""

import logging
from enum import Enum
from typing import Any, Dict, Optional

from trading_bot.core_agent_system.meta_orchestrator import MetaOrchestrator as _CoreMetaOrchestrator

logger = logging.getLogger(__name__)


class WorkflowStage(Enum):
    INGEST = "ingest"
    FUSE = "fuse"
    ANALYZE = "analyze"
    STRATEGIZE = "strategize"
    SIMULATE = "simulate"
    EVALUATE_RISK = "evaluate_risk"
    EXECUTE = "execute"
    REVIEW = "review"


class MetaOrchestrator(_CoreMetaOrchestrator):
    """RadarAI-facing orchestrator with an agent registry."""

    def __init__(self, config: Optional[Dict] = None):
        import warnings
        warnings.warn(
            "MetaOrchestrator is a deprecated duplicate; canonical "
            "orchestrator is trading_bot.core.csc.controller."
            "CognitiveSystemController.",
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(config)
        self._registry: Dict[str, Any] = {}

    def register_agent(self, name: str, agent: Any) -> None:
        self._registry[name] = agent
        logger.debug(f"MetaOrchestrator: registered agent {name}")

    def get_agent(self, name: str) -> Optional[Any]:
        return self._registry.get(name)

    @property
    def agents(self) -> Dict[str, Any]:
        return dict(self._registry)
