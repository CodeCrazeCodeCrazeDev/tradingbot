"""
Immutable Shield - UCA-2026 Core Governance Component
===================================================

Authoritative non-bypassable safety gate for all system actions.
"""

import logging
import threading
import asyncio
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)

class GovernanceDecision(Enum):
    APPROVED = "APPROVED"
    BLOCKED = "BLOCKED"
    REJECTED = "REJECTED"

def _coerce_float(value: Any, default: Optional[float]) -> Optional[float]:
    """Coerce loose numeric inputs (e.g. string numbers from dict bridges);
    unparseable values fall back to ``default`` so caps still evaluate."""
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


@dataclass
class ShieldReport:
    decision: GovernanceDecision
    reason: str
    risk_score: float
    timestamp: datetime = field(default_factory=datetime.utcnow)
    audit_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    details: Dict[str, Any] = field(default_factory=dict)

class ImmutableShield:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(ImmutableShield, cls).__new__(cls)
                cls._instance._initialized = False
        return cls._instance

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        if self._initialized: return
        self.config = config or {}
        self._audit_log: List[ShieldReport] = []

        # Delayed registration to avoid circular import
        from .unified_event_bus import decision_bus
        decision_bus.register_voter("shield", self.audit_log_action)

        self._initialized = True

    async def audit_log_action(self, action: Any) -> Dict[str, Any]:
        context = action.payload.get("context", {})
        report = await self.validate_action(action.action_type, action.payload, context)
        return {
            "decision": report.decision.value,
            "reason": report.reason,
            "risk_score": report.risk_score,
            "audit_id": report.audit_id
        }

    async def validate_action(self, action_type: str, params: Dict[str, Any], context: Dict[str, Any]) -> ShieldReport:
        """
        Deterministic, non-bypassable governance checks.

        Enforces hard limits from ``self.config``:
          - ``trading_enabled``   (default True) — global kill switch
          - ``max_quantity``      (default 10.0) — absolute order size cap
          - ``max_exposure``      (default 0.05) — portfolio exposure fraction cap
          - ``min_confidence``    (default 0.0)  — required decision confidence
          - ``allowed_actions``   (default trade types) — action whitelist
          - ``blocked_symbols``   (default [])   — symbol denylist
        """
        params = params if isinstance(params, dict) else {}
        context = context if isinstance(context, dict) else {}
        risk_score = 0.1

        # 1. Global kill switch
        if not self.config.get("trading_enabled", True):
            return ShieldReport(GovernanceDecision.BLOCKED, "Trading disabled by kill switch", 1.0)

        # 2. Action whitelist
        allowed = set(self.config.get("allowed_actions", ["trade", "TRADE_PROPOSAL", "TRADE_EXECUTION"]))
        if action_type not in allowed:
            return ShieldReport(GovernanceDecision.REJECTED, f"Action type '{action_type}' not whitelisted", 0.9)

        # 3. Quantity sanity + cap — only enforced when the proposal carries a
        # quantity (context-only checks like drawdown do not require one).
        quantity = params.get("quantity")
        if quantity is not None:
            if not isinstance(quantity, (int, float)) or quantity <= 0:
                return ShieldReport(GovernanceDecision.REJECTED, f"Invalid quantity: {quantity}", 0.9)
            max_qty = self.config.get("max_quantity", 10.0)
            if quantity > max_qty:
                return ShieldReport(GovernanceDecision.BLOCKED, f"Quantity {quantity} exceeds cap {max_qty}", min(1.0, quantity / max_qty))

        # 4. Symbol denylist; typed OrderRequest payloads nest instrument data
        # in dict OR attribute form — a non-dict instrument must not bypass it.
        instrument = params.get("instrument", {})
        symbol = params.get("symbol")
        if not symbol:
            if isinstance(instrument, dict):
                symbol = instrument.get("symbol")
            else:
                symbol = getattr(instrument, "symbol", None)
        if symbol and symbol in self.config.get("blocked_symbols", []):
            return ShieldReport(GovernanceDecision.BLOCKED, f"Symbol {symbol} is denylisted", 0.95)

        # 5. Data freshness and quality are hard execution prerequisites when
        # supplied by the normalized market-data boundary.
        market = context.get("market", context)
        if isinstance(market, dict):
            quality = str(market.get("data_quality", market.get("quality", ""))).lower()
            if quality in {"invalid", "stale"} or market.get("data_is_fresh") is False:
                return ShieldReport(GovernanceDecision.BLOCKED, "Market data is not fresh and valid", 0.95)

        # 6. Confidence floor — a proposal that omits confidence defaults to
        # 0.0, not 1.0: with a configured floor an absent value must fail
        # closed rather than implicitly satisfy it.
        confidence = params.get("confidence", 0.0)
        min_conf = self.config.get("min_confidence", 0.0)
        if isinstance(confidence, (int, float)) and confidence < min_conf:
            return ShieldReport(GovernanceDecision.REJECTED, f"Confidence {confidence} below floor {min_conf}", 0.7)

        # 7. Exposure cap (from market context) — coerce loose numerics; a
        # string "0.20" must still be enforced, not skipped.
        market = context.get("market", context)
        exposure = market.get("exposure", market.get("portfolio_exposure", 0.0)) if isinstance(market, dict) else 0.0
        exposure = _coerce_float(exposure, 0.0)
        max_exp = self.config.get("max_exposure", 0.05)
        if exposure > max_exp:
            return ShieldReport(GovernanceDecision.BLOCKED, f"Portfolio exposure {exposure:.2%} exceeds cap {max_exp:.2%}", 0.85)

        # 7b. Portfolio drawdown hard stop — beyond the configured cap the
        # shield blocks all new risk, not merely flags it.
        portfolio = context.get("portfolio", {})
        drawdown = portfolio.get("drawdown", 0.0) if isinstance(portfolio, dict) else 0.0
        drawdown = _coerce_float(drawdown, 0.0)
        max_dd = self.config.get("max_drawdown", 0.15)
        if drawdown > max_dd:
            return ShieldReport(GovernanceDecision.BLOCKED, f"Portfolio drawdown {drawdown:.2%} exceeds cap {max_dd:.2%}", 1.0)

        # 8. Regime veto: under EXTREME_VOLATILITY only exit/close actions pass
        regime = market.get("regime") if isinstance(market, dict) else None
        intent = str(params.get("action", "")).lower()
        exit_intents = ("exit", "close", "exit_position", "sell_to_close", "buy_to_close")
        if regime == "EXTREME_VOLATILITY" and str(action_type).lower() not in exit_intents and intent not in exit_intents:
            return ShieldReport(GovernanceDecision.BLOCKED, "Extreme volatility regime: only exits permitted", 0.95)

        # 9. Spread guard: when live microstructure is in context, entering a
        # trade across an abnormally wide spread is a hard veto. Exits pass.
        micro = market.get("microstructure", market) if isinstance(market, dict) else {}
        spread = micro.get("spread_bps") if isinstance(micro, dict) else None
        spread = _coerce_float(spread, None)
        max_spread = self.config.get("max_spread_bps")
        if (max_spread is not None and spread is not None
                and spread > max_spread and intent not in exit_intents):
            return ShieldReport(
                GovernanceDecision.BLOCKED,
                f"Spread {spread:.1f}bps exceeds guard {max_spread}bps", 0.9)

        return ShieldReport(GovernanceDecision.APPROVED, "All shield checks passed", risk_score)

    def check_evolution_gate(self, current_perf: float, proposed_perf: float, gain_threshold: float = 0.02) -> bool:
        """
        Monotone Improvement Gate (RSEA): only allow self-improvement when the
        proposed variant beats the incumbent by a strict gain on held-out data.
        Deterministic — no model reasoning in the safety path.
        """
        passed = proposed_perf > current_perf + gain_threshold
        if passed:
            logger.info(f"Evolution Gate: PASS (Gain: {proposed_perf - current_perf:.4f})")
        else:
            logger.warning(f"Evolution Gate: REJECT (Insufficient Gain: {proposed_perf - current_perf:.4f})")
        return passed

shield = ImmutableShield()
