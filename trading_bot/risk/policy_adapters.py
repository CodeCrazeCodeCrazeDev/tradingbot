"""Subordinate veto-only risk-policy adapters for retained legacy analyzers.

These adapters expose legacy risk analyzers to ``CanonicalRiskService`` as
``RiskPolicy`` vetoes. A policy may reject a proposal; it can never approve,
size, persist, or execute on its own. Every adapter fails closed: any
exception, missing evaluator, or ambiguous result is a veto.

Register via ``CanonicalRiskService.register_policy(name, adapter)``.
"""

from __future__ import annotations

import inspect
import logging
from typing import Any, Mapping, Optional

from trading_bot.foundation.contracts import DecisionProposal, RiskState

logger = logging.getLogger(__name__)


def _proposal_trade_fields(proposal: DecisionProposal) -> dict:
    signal = proposal.signal
    meta = dict(getattr(signal, "metadata", {}) or {})
    return {
        "symbol": signal.instrument.symbol,
        "direction": signal.direction,
        "quantity": float(meta.get("quantity", 0.0) or 0.0),
        "entry_price": float(meta.get("entry_price", meta.get("price", 0.0)) or 0.0),
        "stop_loss": float(getattr(signal, "stop_loss", None) or meta.get("stop_loss", 0.0) or 0.0),
        "take_profit": float(getattr(signal, "take_profit", None) or meta.get("take_profit", 0.0) or 0.0),
        "confidence": float(getattr(signal, "confidence", 0.0) or 0.0),
        "meta": meta,
    }


async def _maybe_await(result: Any) -> Any:
    if inspect.isawaitable(result):
        return await result
    return result


class TradeAssessmentPolicyAdapter:
    """Adapt an analyzer exposing ``assess_trade_risk``/``check_risk_limits``.

    Shape covered (e.g. ``risk_management.risk_engine.RiskEngine``):
    ``assess_trade_risk(trade_id, symbol, direction, entry_price,
    position_size, stop_loss, take_profit=...)`` returns an assessment, and
    ``check_risk_limits(assessment)`` returns violation alerts. Any non-empty
    alert list, exception, or missing evaluator vetoes the proposal.
    """

    def __init__(self, name: str, analyzer: Any):
        self.name = name
        self.analyzer = analyzer

    async def evaluate(self, proposal: DecisionProposal, state: RiskState) -> Mapping[str, Any]:
        assess = getattr(self.analyzer, "assess_trade_risk", None)
        if assess is None:
            return {"approved": False, "reason": f"Policy '{self.name}' has no assess_trade_risk"}
        fields = _proposal_trade_fields(proposal)
        try:
            assessment = await _maybe_await(
                assess(
                    trade_id=proposal.decision_id,
                    symbol=fields["symbol"],
                    direction=fields["direction"],
                    entry_price=fields["entry_price"],
                    position_size=fields["quantity"],
                    stop_loss=fields["stop_loss"],
                    take_profit=fields["take_profit"] or None,
                )
            )
        except TypeError:
            # Tolerate positional-style analyzers.
            try:
                assessment = await _maybe_await(
                    assess(
                        proposal.decision_id,
                        fields["symbol"],
                        fields["direction"],
                        fields["entry_price"],
                        fields["quantity"],
                        fields["stop_loss"],
                    )
                )
            except Exception as exc:
                return {"approved": False, "reason": f"Policy '{self.name}' assessment failed: {exc}"}
        except Exception as exc:
            return {"approved": False, "reason": f"Policy '{self.name}' assessment failed: {exc}"}

        check_limits = getattr(self.analyzer, "check_risk_limits", None)
        alerts: Any = []
        if check_limits is not None and assessment is not None:
            try:
                alerts = await _maybe_await(check_limits(assessment))
            except Exception as exc:
                return {"approved": False, "reason": f"Policy '{self.name}' limit check failed: {exc}"}
        if alerts:
            messages = [str(getattr(a, "message", a)) for a in alerts]
            return {
                "approved": False,
                "reason": f"Policy '{self.name}' vetoed: " + "; ".join(messages[:3]),
                "alert_count": len(alerts),
            }
        risk_level = getattr(assessment, "risk_level", None)
        return {
            "approved": True,
            "reason": f"Policy '{self.name}' passed",
            "risk_level": getattr(risk_level, "value", risk_level),
        }


class TradeAllowancePolicyAdapter:
    """Adapt a controller exposing ``check_trade_allowed(symbol, direction, size)``.

    Shape covered (e.g. ``utils.risk_controller.RiskController``): returns
    ``(allowed, reason, action)``. A non-allowed result or any exception
    vetoes; the legacy ``action`` is recorded as evidence, never executed.
    """

    def __init__(self, name: str, controller: Any):
        self.name = name
        self.controller = controller

    async def evaluate(self, proposal: DecisionProposal, state: RiskState) -> Mapping[str, Any]:
        checker = getattr(self.controller, "check_trade_allowed", None)
        if checker is None:
            return {"approved": False, "reason": f"Policy '{self.name}' has no check_trade_allowed"}
        fields = _proposal_trade_fields(proposal)
        try:
            result = await _maybe_await(
                checker(fields["symbol"], fields["direction"], fields["quantity"])
            )
        except Exception as exc:
            return {"approved": False, "reason": f"Policy '{self.name}' check failed: {exc}"}
        if isinstance(result, tuple):
            allowed = bool(result[0])
            reason = str(result[1]) if len(result) > 1 else f"Policy '{self.name}'"
            action = getattr(result[2], "value", result[2]) if len(result) > 2 else None
            return {"approved": allowed, "reason": reason, "legacy_action": action}
        if isinstance(result, bool):
            return {"approved": result, "reason": f"Policy '{self.name}'"}
        return {"approved": bool(result), "reason": f"Policy '{self.name}'"}


class SizingVetoPolicyAdapter:
    """Adapt a legacy ``calculate_position_size`` implementation into a veto.

    Sizing advice is evidence only: a computed size <= ``min_size`` vetoes the
    proposal, but the adapter NEVER produces an approval quantity — sizing
    authority stays with ``CanonicalRiskService.approved_quantity``.
    """

    def __init__(self, name: str, sizer: Any, min_size: float = 0.0):
        self.name = name
        self.sizer = sizer
        self.min_size = float(min_size)

    async def evaluate(self, proposal: DecisionProposal, state: RiskState) -> Mapping[str, Any]:
        sizer_fn = getattr(self.sizer, "calculate_position_size", None)
        if sizer_fn is None:
            return {"approved": False, "reason": f"Policy '{self.name}' has no calculate_position_size"}
        fields = _proposal_trade_fields(proposal)
        try:
            size = await _maybe_await(
                sizer_fn(
                    symbol=fields["symbol"],
                    direction=fields["direction"],
                    confidence=fields["confidence"],
                )
            )
        except TypeError:
            try:
                size = await _maybe_await(
                    sizer_fn(fields["symbol"], fields["direction"], fields["confidence"])
                )
            except Exception as exc:
                return {"approved": False, "reason": f"Policy '{self.name}' sizing failed: {exc}"}
        except Exception as exc:
            return {"approved": False, "reason": f"Policy '{self.name}' sizing failed: {exc}"}
        try:
            size_value = float(size)
        except (TypeError, ValueError):
            return {"approved": False, "reason": f"Policy '{self.name}' returned non-numeric size"}
        if size_value <= self.min_size:
            return {
                "approved": False,
                "reason": f"Policy '{self.name}' vetoed: computed size {size_value} <= {self.min_size}",
            }
        return {"approved": True, "reason": f"Policy '{self.name}' sizing admissible"}
