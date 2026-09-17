"""
Strategy Registry for Research OS.
Registers and tracks synthesized quantitative strategies, approval gates, and deployment lineage.
"""

from typing import Dict, Optional, Tuple, Any
import logging
from datetime import datetime
from trading_bot.research.core.interfaces import StrategyRegistry, ResearchStrategy

logger = logging.getLogger(__name__)


class StandardStrategyRegistry(StrategyRegistry):
    """
    Standard Strategy Registry tracking strategy deployments, approvals, performance, and lineaged metrics.
    """

    def __init__(self):
        self._strategies: Dict[str, ResearchStrategy] = {}
        self._metadata: Dict[str, Dict[str, Any]] = {}

    def register_strategy(self, strategy: ResearchStrategy, metadata: Dict[str, Any]) -> None:
        strategy_id = strategy.strategy_id
        self._strategies[strategy_id] = strategy

        self._metadata[strategy_id] = {
            "registered_at": datetime.utcnow().isoformat(),
            "lineage": strategy.get_lineage(),
            "governance_status": metadata.get("governance_status", "pending_review"),  # pending, approved, rejected
            "deployment_history": metadata.get("deployment_history", []),
            "production_performance": metadata.get("production_performance", {}),
            "retirement_reason": metadata.get("retirement_reason", None),
            "status": metadata.get("status", "active")  # active, retired, deprecated
        }
        logger.info(f"Registered strategy '{strategy_id}' successfully in Strategy Registry.")

    def get_strategy(self, strategy_id: str) -> Optional[Tuple[ResearchStrategy, Dict[str, Any]]]:
        if strategy_id in self._strategies:
            return self._strategies[strategy_id], self._metadata[strategy_id]
        return None

    def update_governance(self, strategy_id: str, status: str, auditor: str = "GovernanceBoard") -> None:
        """Update approval state."""
        if strategy_id in self._metadata:
            self._metadata[strategy_id]["governance_status"] = status
            self._metadata[strategy_id]["lineage"]["governance_approvals"] = {
                "audited_at": datetime.utcnow().isoformat(),
                "auditor": auditor,
                "status": status
            }
            logger.info(f"Strategy '{strategy_id}' governance updated to: {status}")

    def retire_strategy(self, strategy_id: str, reason: str) -> None:
        """Track strategy retirement with explicit post-mortem evidence."""
        if strategy_id in self._metadata:
            self._metadata[strategy_id]["status"] = "retired"
            self._metadata[strategy_id]["retirement_reason"] = reason
            logger.info(f"Strategy '{strategy_id}' retired in Strategy Registry: {reason}")
