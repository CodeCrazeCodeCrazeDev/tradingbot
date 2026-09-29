"""Canonical portfolio-level risk service for the foundation runtime."""

from __future__ import annotations

import inspect
import logging
from typing import Any, Dict, Mapping, Optional

from trading_bot.foundation.contracts import (
    DecisionProposal,
    Instrument,
    InstrumentType,
    PortfolioSnapshot,
    RiskDecision,
    RiskState,
    Signal,
)


class LegacyRiskPolicyAdapter:
    """Convert a legacy risk analyzer into a subordinate veto policy."""

    def __init__(self, name: str, legacy: Any):
        self.name = name
        self.legacy = legacy

    async def evaluate(self, proposal: DecisionProposal, state: RiskState) -> Mapping[str, Any]:
        evaluator = getattr(self.legacy, "evaluate", None)
        if evaluator is None:
            evaluator = getattr(self.legacy, "validate_trade", None)
        if evaluator is None:
            evaluator = getattr(self.legacy, "assess_risk", None)
        if evaluator is None and hasattr(self.legacy, "run_all_checks"):
            order = {
                "symbol": proposal.signal.instrument.symbol,
                "action": proposal.signal.direction,
                "quantity": proposal.signal.metadata.get("quantity", 0.0),
                "position_value": proposal.signal.metadata.get("position_value", 0.0),
                "stop_loss": proposal.signal.stop_loss,
                "take_profit": proposal.signal.take_profit,
                **dict(proposal.signal.metadata),
            }
            portfolio = {
                "equity": state.equity,
                "exposure": state.portfolio_exposure,
                "open_positions": state.open_positions,
                "daily_pnl": state.daily_pnl,
                "drawdown": state.drawdown_fraction,
            }
            result = self.legacy.run_all_checks(order, portfolio)
            rejected = [check.reason for check in result if getattr(check.result, "value", "") == "rejected"]
            return {
                "approved": not rejected,
                "reason": "; ".join(rejected) if rejected else f"Legacy policy '{self.name}' passed",
            }
        if evaluator is None and hasattr(self.legacy, "can_trade"):
            result = self.legacy.can_trade()
            if inspect.isawaitable(result):
                result = await result
            return {"approved": bool(result[0]), "reason": str(result[1] or self.name)}
        if evaluator is None and hasattr(self.legacy, "validate"):
            evaluator = self.legacy.validate
        if evaluator is None:
            return {"approved": False, "reason": f"Legacy policy '{self.name}' has no evaluator"}
        try:
            result = evaluator(proposal, state)
        except TypeError:
            result = evaluator(proposal.signal, state)
        if inspect.isawaitable(result):
            result = await result
        if isinstance(result, tuple):
            return {"approved": bool(result[0]), "reason": str(result[1] if len(result) > 1 else "legacy policy")}
        if isinstance(result, bool):
            return {"approved": result, "reason": f"Legacy policy '{self.name}'"}
        if isinstance(result, Mapping):
            return result
        return {"approved": bool(result), "reason": f"Legacy policy '{self.name}'"}


logger = logging.getLogger(__name__)


class CanonicalRiskService:
    """Deterministic risk authority used before the immutable final gate.

    The existing MasterRiskManager remains available behind the compatibility
    surface while its broader analytics are migrated into this contract.
    """

    def __init__(
        self,
        limits: Mapping[str, float] = None,
        policies: Optional[Mapping[str, Any]] = None,
        state_provider: Any = None,
    ) -> None:
        self.limits: Dict[str, float] = {
            "max_quantity": 10.0,
            "max_exposure": 0.05,
            "max_drawdown": 0.25,
            "max_daily_loss": 0.05,
            "max_open_positions": 10,
            **dict(limits or {}),
        }
        self.policies: Dict[str, Any] = dict(policies or {})
        # Optional authoritative portfolio-state source (e.g.
        # PortfolioStateProvider over SqliteTradingRepository). When set,
        # evaluate_action uses real persisted state and fails closed if the
        # provider cannot supply it; without it the legacy dict path applies.
        self.state_provider = state_provider

    async def _provider_state(self, observation: Mapping[str, Any]) -> Optional[Mapping[str, Any]]:
        provider = self.state_provider
        getter = (
            getattr(provider, "portfolio_state", None)
            or getattr(provider, "risk_state", None)
            or (provider if callable(provider) else None)
        )
        if getter is None:
            return None
        result = getter(observation)
        if inspect.isawaitable(result):
            result = await result
        return result if isinstance(result, Mapping) else None

    def register_policy(self, name: str, policy: Any) -> None:
        """Register a subordinate veto policy; policies cannot approve alone."""
        if not name.strip() or policy is None or not hasattr(policy, "evaluate"):
            raise ValueError("Risk policies require a name and evaluate() method")
        self.policies[name] = policy

    def unregister_policy(self, name: str) -> None:
        self.policies.pop(name, None)

    async def evaluate(self, proposal: DecisionProposal, state: RiskState) -> RiskDecision:
        requested_quantity = float(proposal.signal.metadata.get("quantity", 1.0))
        checks = {
            "trading_enabled": state.trading_enabled,
            "data_fresh": state.data_is_fresh,
            "not_emergency": not state.emergency,
            "drawdown_limit": state.drawdown_fraction <= self.limits["max_drawdown"],
            "daily_loss_limit": state.daily_pnl >= -abs(self.limits["max_daily_loss"] * max(state.equity, 0.0)),
            "exposure_limit": state.portfolio_exposure <= self.limits["max_exposure"],
            "open_position_limit": state.open_positions < int(self.limits["max_open_positions"]),
            "quantity_limit": 0.0 < requested_quantity <= self.limits["max_quantity"],
        }
        approved = all(checks.values()) and proposal.signal.direction.lower() not in {"hold", "neutral"}
        reason = "All canonical risk checks passed" if approved else self._rejection_reason(checks)
        if approved:
            for name, policy in self.policies.items():
                try:
                    result = policy.evaluate(proposal, state)
                    result = await result if inspect.isawaitable(result) else result
                except Exception as exc:
                    checks[f"policy_{name}"] = False
                    approved = False
                    reason = f"Risk policy '{name}' failed closed: {exc}"
                    break
                allowed = bool(result if isinstance(result, bool) else result.get("approved", False))
                checks[f"policy_{name}"] = allowed
                if not allowed:
                    approved = False
                    reason = str(result.get("reason", f"Risk policy '{name}' vetoed"))
                    break
        return RiskDecision(
            approved=approved,
            decision_id=proposal.decision_id,
            reason=reason,
            approved_quantity=requested_quantity if approved else 0.0,
            risk_score=self._risk_score(state),
            checks=checks,
        )

    async def evaluate_action(
        self,
        action: Mapping[str, Any],
        observation: Mapping[str, Any],
    ) -> RiskDecision:
        """Compatibility bridge for the CSC's current dictionary proposal."""
        provider_state: Optional[Mapping[str, Any]] = None
        if self.state_provider is not None:
            try:
                provider_state = await self._provider_state(observation)
            except Exception as exc:
                logger.warning(f"portfolio state provider failed closed: {exc}")
                provider_state = None
            if provider_state is None:
                return RiskDecision(
                    approved=False,
                    decision_id=str(action.get("trade_id", "runtime-decision")),
                    reason="Portfolio state unavailable from provider",
                    approved_quantity=0.0,
                    risk_score=1.0,
                    checks={"portfolio_state_available": False},
                )
        live = dict(provider_state or {})

        def _field(*keys: str, default: float = 0.0) -> float:
            for key in keys:
                if key in live and live[key] is not None:
                    return float(live[key])
            for key in keys:
                if key in observation and observation[key] is not None:
                    return float(observation[key])
            return default

        symbol = str(action.get("symbol") or observation.get("symbol") or "UNKNOWN")
        instrument = Instrument(symbol, InstrumentType.SYNTHETIC, str(observation.get("venue") or "runtime"))
        equity = _field("equity", default=1.0)
        quality = str(observation.get("data_quality", "valid")).lower()
        state = RiskState(
            account_id=str(live.get("account_id", observation.get("account_id", "runtime"))),
            equity=equity,
            portfolio_exposure=_field("portfolio_exposure", "exposure"),
            daily_pnl=_field("daily_pnl"),
            drawdown_fraction=_field("drawdown_fraction", "drawdown"),
            open_positions=int(_field("open_positions")),
            data_is_fresh=quality not in {"invalid", "stale"},
            trading_enabled=bool(observation.get("trading_enabled", True)),
            emergency=bool(observation.get("emergency", False)),
        )
        signal = Signal(
            signal_id=str(action.get("trade_id", "runtime-signal")),
            instrument=instrument,
            direction=str(action.get("action", "WAIT")),
            confidence=float(action.get("confidence", 0.0) or 0.0),
            metadata={"quantity": action.get("quantity", 0.0)},
        )
        proposal = DecisionProposal(
            decision_id=str(action.get("trade_id", "runtime-decision")),
            signal=signal,
            portfolio=PortfolioSnapshot(state.account_id, equity, float(live.get("cash", equity))),
            risk_state=state,
        )
        return await self.evaluate(proposal, state)

    async def refresh(self, portfolio: PortfolioSnapshot) -> RiskState:
        exposure = sum(abs(item.fraction_of_equity) for item in portfolio.exposures)
        daily_pnl = sum(item.realized_pnl for item in portfolio.positions)
        return RiskState(
            account_id=portfolio.account_id,
            equity=portfolio.equity,
            portfolio_exposure=exposure,
            daily_pnl=daily_pnl,
            drawdown_fraction=portfolio.drawdown_fraction,
            open_positions=len([item for item in portfolio.positions if item.quantity != 0]),
            limits=self.limits,
        )

    def _risk_score(self, state: RiskState) -> float:
        drawdown_score = state.drawdown_fraction / max(self.limits["max_drawdown"], 1e-9)
        exposure_score = state.portfolio_exposure / max(self.limits["max_exposure"], 1e-9)
        return max(0.0, min(1.0, max(drawdown_score, exposure_score)))

    @staticmethod
    def _rejection_reason(checks: Mapping[str, bool]) -> str:
        failed = [name for name, passed in checks.items() if not passed]
        return "Risk checks failed: " + ", ".join(failed or ["direction_not_tradeable"])
