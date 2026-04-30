"""
PHCE-D Module 10: Circuit Breakers

Sits outside PHCE-D, above all modules.

Triggers:
- Stale evidence across symbols
- Drawdown limit breach
- Repeated paper-trade failures
- Dependency graph failure
- Unexpected live execution path
- Validation gateway bypass attempt

Behavior:
- Pause all trade-positive outputs
- Force HOLD or NO_TRADE
- Require manual reset

The decision policy CANNOT override circuit breakers. Ever.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from .core_types import (
    CircuitBreakerTrigger,
    DecisionOutput,
    GatewayBypassError,
    PHCEDError,
)

logger = logging.getLogger(__name__)


@dataclass
class BreakerEvent:
    """Record of a circuit breaker trigger."""
    trigger: CircuitBreakerTrigger
    timestamp: float
    details: str
    auto_reset_eligible: bool = False


@dataclass
class CircuitBreakerState:
    """Current state of all circuit breakers."""
    active: bool = False
    active_triggers: List[CircuitBreakerTrigger] = field(default_factory=list)
    triggered_at: Optional[float] = None
    triggered_by: Optional[str] = None
    manual_reset_required: bool = False
    event_log: List[BreakerEvent] = field(default_factory=list)
    consecutive_paper_trade_failures: int = 0
    stale_evidence_symbols: List[str] = field(default_factory=list)


class CircuitBreaker:
    """
    Module 10: Circuit Breakers

    Sits above all PHCE-D modules. Cannot be overridden by the decision policy.

    When triggered:
    - All trade-positive outputs are paused
    - Output is forced to HOLD or NO_TRADE
    - Manual reset is required (unless auto-reset eligible)

    Triggers:
    - Stale evidence across multiple symbols
    - Drawdown limit breach
    - Repeated paper-trade failures
    - Dependency graph failure
    - Unexpected live execution path
    - Validation gateway bypass attempt
    """

    def __init__(
        self,
        max_consecutive_paper_failures: int = 5,
        max_stale_symbols: int = 3,
        drawdown_breach_threshold_pct: float = 15.0,
        auto_reset_after_seconds: float = 0.0,  # 0 = manual reset only
        alert_callbacks: Optional[List[Callable]] = None,
    ):
        self.max_consecutive_paper_failures = max_consecutive_paper_failures
        self.max_stale_symbols = max_stale_symbols
        self.drawdown_breach_threshold = drawdown_breach_threshold_pct
        self.auto_reset_after_seconds = auto_reset_after_seconds
        self.alert_callbacks = alert_callbacks or []

        self.state = CircuitBreakerState()

        # Statistics
        self.total_triggers = 0
        self.triggers_by_type: Dict[str, int] = {}
        self.total_resets = 0

    def check_and_enforce(
        self,
        decision_output: DecisionOutput,
        stale_symbols: Optional[List[str]] = None,
        current_drawdown_pct: float = 0.0,
        paper_trade_failure_count: int = 0,
        dependency_graph_ok: bool = True,
        live_execution_detected: bool = False,
        gateway_bypass_detected: bool = False,
    ) -> DecisionOutput:
        """
        Check circuit breaker conditions and enforce if triggered.

        If the breaker is active, all trade-positive outputs are forced
        to NO_TRADE or HOLD. The decision policy cannot override this.

        Args:
            decision_output: The proposed decision output
            stale_symbols: Symbols with stale evidence
            current_drawdown_pct: Current portfolio drawdown
            paper_trade_failure_count: Consecutive paper-trade failures
            dependency_graph_ok: Whether dependency graph is healthy
            live_execution_detected: Whether unexpected live execution was detected
            gateway_bypass_detected: Whether a gateway bypass was attempted

        Returns:
            The enforced decision output (may be downgraded)
        """
        # Check for new triggers
        self._check_triggers(
            stale_symbols=stale_symbols or [],
            current_drawdown_pct=current_drawdown_pct,
            paper_trade_failure_count=paper_trade_failure_count,
            dependency_graph_ok=dependency_graph_ok,
            live_execution_detected=live_execution_detected,
            gateway_bypass_detected=gateway_bypass_detected,
        )

        # If breaker is active, enforce
        if self.state.active:
            if decision_output in DecisionOutput.trade_positive():
                logger.warning(
                    f"CIRCUIT BREAKER ACTIVE: Downgrading {decision_output.value} "
                    f"to NO_TRADE. Triggers: {[t.value for t in self.state.active_triggers]}"
                )
                return DecisionOutput.NO_TRADE
            # Non-trade-positive outputs pass through
            return decision_output

        return decision_output

    def _check_triggers(
        self,
        stale_symbols: List[str],
        current_drawdown_pct: float,
        paper_trade_failure_count: int,
        dependency_graph_ok: bool,
        live_execution_detected: bool,
        gateway_bypass_detected: bool,
    ) -> None:
        """Check all trigger conditions and trip breaker if needed."""
        new_triggers: List[CircuitBreakerTrigger] = []

        # Trigger 1: Stale evidence across symbols
        self.state.stale_evidence_symbols = stale_symbols
        if len(stale_symbols) >= self.max_stale_symbols:
            new_triggers.append(CircuitBreakerTrigger.STALE_EVIDENCE_ACROSS_SYMBOLS)

        # Trigger 2: Drawdown limit breach
        if current_drawdown_pct >= self.drawdown_breach_threshold:
            new_triggers.append(CircuitBreakerTrigger.DRAWDOWN_LIMIT_BREACH)

        # Trigger 3: Repeated paper-trade failures
        self.state.consecutive_paper_trade_failures = paper_trade_failure_count
        if paper_trade_failure_count >= self.max_consecutive_paper_failures:
            new_triggers.append(CircuitBreakerTrigger.REPEATED_PAPER_TRADE_FAILURES)

        # Trigger 4: Dependency graph failure
        if not dependency_graph_ok:
            new_triggers.append(CircuitBreakerTrigger.DEPENDENCY_GRAPH_FAILURE)

        # Trigger 5: Unexpected live execution path
        if live_execution_detected:
            new_triggers.append(CircuitBreakerTrigger.UNEXPECTED_LIVE_EXECUTION_PATH)
            logger.critical("UNEXPECTED LIVE EXECUTION PATH DETECTED — CIRCUIT BREAKER TRIGGERED")

        # Trigger 6: Gateway bypass attempt
        if gateway_bypass_detected:
            new_triggers.append(CircuitBreakerTrigger.VALIDATION_GATEWAY_BYPASS_ATTEMPT)
            logger.critical("VALIDATION GATEWAY BYPASS ATTEMPT — CIRCUIT BREAKER TRIGGERED")

        # Trip breaker if any new triggers
        if new_triggers:
            self._trip(new_triggers)

    def _trip(self, triggers: List[CircuitBreakerTrigger]) -> None:
        """Trip the circuit breaker."""
        now = time.time()
        for trigger in triggers:
            event = BreakerEvent(
                trigger=trigger,
                timestamp=now,
                details=f"Circuit breaker triggered: {trigger.value}",
                auto_reset_eligible=(self.auto_reset_after_seconds > 0),
            )
            self.state.event_log.append(event)

            key = trigger.value
            self.triggers_by_type[key] = self.triggers_by_type.get(key, 0) + 1

        self.state.active = True
        self.state.active_triggers.extend(triggers)
        self.state.triggered_at = now
        self.state.manual_reset_required = self.auto_reset_after_seconds == 0
        self.total_triggers += 1

        logger.critical(
            f"CIRCUIT BREAKER TRIPPED: {[t.value for t in triggers]}. "
            f"Manual reset required: {self.state.manual_reset_required}"
        )

        # Fire alert callbacks
        for callback in self.alert_callbacks:
            try:
                callback({
                    "type": "circuit_breaker_tripped",
                    "triggers": [t.value for t in triggers],
                    "timestamp": now,
                    "manual_reset_required": self.state.manual_reset_required,
                })
            except Exception as e:
                logger.error(f"Alert callback error: {e}")

    def manual_reset(self, authorized_by: str) -> bool:
        """
        Manual reset of the circuit breaker.
        Requires human authorization — no automated reset unless auto_reset is configured.
        """
        if not self.state.active:
            return True  # Already reset

        logger.critical(
            f"CIRCUIT BREAKER MANUAL RESET by {authorized_by}. "
            f"Previous triggers: {[t.value for t in self.state.active_triggers]}"
        )

        self.state.active = False
        self.state.active_triggers = []
        self.state.triggered_at = None
        self.state.triggered_by = None
        self.state.manual_reset_required = False
        self.total_resets += 1

        return True

    def check_auto_reset(self) -> bool:
        """
        Check if auto-reset is eligible (only if configured).
        Most production deployments should require manual reset.
        """
        if not self.state.active:
            return True

        if self.auto_reset_after_seconds <= 0:
            return False  # Manual reset only

        if self.state.triggered_at is None:
            return False

        elapsed = time.time() - self.state.triggered_at
        if elapsed >= self.auto_reset_after_seconds:
            # Only auto-reset if all trigger conditions have cleared
            if not self.state.stale_evidence_symbols and self.state.consecutive_paper_trade_failures == 0:
                self.state.active = False
                self.state.active_triggers = []
                self.state.triggered_at = None
                self.total_resets += 1
                logger.info("Circuit breaker auto-reset after timeout")
                return True

        return False

    def is_active(self) -> bool:
        """Check if the circuit breaker is currently active."""
        return self.state.active

    def get_stats(self) -> Dict[str, Any]:
        """Return circuit breaker statistics."""
        return {
            "active": self.state.active,
            "active_triggers": [t.value for t in self.state.active_triggers],
            "total_triggers": self.total_triggers,
            "total_resets": self.total_resets,
            "triggers_by_type": self.triggers_by_type,
            "consecutive_paper_failures": self.state.consecutive_paper_trade_failures,
            "stale_symbols": self.state.stale_evidence_symbols,
        }
