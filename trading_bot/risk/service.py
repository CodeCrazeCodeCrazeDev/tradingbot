"""Canonical portfolio-level risk service for the foundation runtime."""

from __future__ import annotations

import inspect
import logging
import math
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

    _NON_TRADEABLE = frozenset({"hold", "neutral", "wait", "none", "no_trade"})

    def _marginal_exposure(self, proposal: DecisionProposal) -> Optional[float]:
        """Equity-fraction change in same-symbol exposure after the proposed
        order, or None when it cannot be measured. Reducing an existing
        position yields a non-positive marginal exposure.
        """
        direction = proposal.signal.direction.lower()
        if direction in self._NON_TRADEABLE:
            return 0.0
        if direction not in {"buy", "sell"}:
            return None
        metadata = proposal.signal.metadata or {}
        mark = metadata.get("mark_price") or metadata.get("price")
        symbol = proposal.signal.instrument.symbol
        if mark is None:
            for pos in proposal.portfolio.positions:
                if pos.instrument.symbol == symbol:
                    mark = pos.average_price
                    break
        if mark is None or float(mark) <= 0:
            return None
        requested = float(metadata.get("quantity", 1.0))
        signed = requested if direction == "buy" else -requested
        current = sum(
            float(p.quantity) for p in proposal.portfolio.positions
            if p.instrument.symbol == symbol
        )
        contract_size = float(proposal.signal.instrument.contract_size or 1.0)
        equity = float(proposal.portfolio.equity)
        if equity <= 0:
            return None
        delta_units = abs(current + signed) - abs(current)
        return delta_units * float(mark) * contract_size / equity

    def _size_for_exposure(self, proposal: DecisionProposal, state: RiskState) -> float:
        """Largest proposal quantity whose marginal exposure fits the
        remaining ``max_exposure`` headroom, floored to the venue's quantity
        increment when one is known. Returns 0.0 when no size is permitted.
        """
        direction = proposal.signal.direction.lower()
        if direction not in {"buy", "sell"}:
            return 0.0
        metadata = proposal.signal.metadata or {}
        mark = metadata.get("mark_price") or metadata.get("price")
        symbol = proposal.signal.instrument.symbol
        if mark is None:
            for pos in proposal.portfolio.positions:
                if pos.instrument.symbol == symbol:
                    mark = pos.average_price
                    break
        contract_size = float(proposal.signal.instrument.contract_size or 1.0)
        equity = float(proposal.portfolio.equity)
        if not mark or float(mark) <= 0 or contract_size <= 0 or equity <= 0:
            return 0.0
        headroom = float(self.limits["max_exposure"]) - float(state.portfolio_exposure)
        if headroom <= 0:
            return 0.0
        unit_budget = headroom * equity / (float(mark) * contract_size)
        # Marginal units added by quantity q:
        #   same direction / flat book:      delta = q
        #   reversal across zero:            delta = q - 2*|current|
        # so the largest q satisfying delta <= unit_budget is budget + 2|cur|
        # for a reversal, else just the budget.
        current = sum(
            float(p.quantity) for p in proposal.portfolio.positions
            if p.instrument.symbol == symbol)
        opposite = (current < 0) if direction == "buy" else (current > 0)
        allowed = unit_budget + (2.0 * abs(current) if opposite else 0.0)
        increment = float(getattr(
            proposal.signal.instrument, "quantity_increment", None) or 0.0)
        if increment > 0:
            allowed = math.floor(allowed / increment) * increment
        sized = max(0.0, min(float(metadata.get("quantity", 1.0)), allowed))
        # A clamped size below the venue minimum is a rejection, not a
        # nominal approval that the adapter must rescue later.
        min_quantity = float(metadata.get("quantity_min", 0.0) or 0.0)
        floor = max(min_quantity, increment, 0.0)
        if floor > 0 and 0 < sized < floor - 1e-12:
            return 0.0
        return sized

    async def evaluate(self, proposal: DecisionProposal, state: RiskState) -> RiskDecision:
        requested_quantity = float(proposal.signal.metadata.get("quantity", 1.0))
        marginal = self._marginal_exposure(proposal)
        projected_exposure = (
            state.portfolio_exposure + marginal if marginal is not None
            else float("inf")
        )
        checks = {
            "trading_enabled": state.trading_enabled,
            "data_fresh": state.data_is_fresh,
            "not_emergency": not state.emergency,
            "drawdown_limit": state.drawdown_fraction <= self.limits["max_drawdown"],
            "daily_loss_limit": state.daily_pnl >= -abs(self.limits["max_daily_loss"] * max(state.equity, 0.0)),
            "exposure_limit": state.portfolio_exposure <= self.limits["max_exposure"],
            "projected_exposure_limit": (
                math.isfinite(projected_exposure)
                and projected_exposure <= self.limits["max_exposure"]
            ),
            "open_position_limit": state.open_positions < int(self.limits["max_open_positions"]),
            "quantity_limit": 0.0 < requested_quantity <= self.limits["max_quantity"],
        }
        direction_tradeable = (
            proposal.signal.direction.lower() not in self._NON_TRADEABLE)
        approved = all(checks.values()) and direction_tradeable
        approved_quantity = requested_quantity
        reason = ("All canonical risk checks passed" if approved
                  else self._rejection_reason(checks))
        if (not approved and direction_tradeable
                and not checks["projected_exposure_limit"]
                and all(ok for name, ok in checks.items()
                        if name != "projected_exposure_limit")):
            # Sizing authority: directional intent that only exceeds the
            # exposure projection is clamped to the largest permitted size
            # instead of vetoed — the CSC's quantity is unit intent, not a
            # venue order size.
            sized = self._size_for_exposure(proposal, state)
            if sized > 0:
                checks["projected_exposure_limit"] = True
                checks["sized_by_risk"] = True
                approved = True
                approved_quantity = sized
                reason = (f"Approved with risk-sized quantity {sized} "
                          f"(requested {requested_quantity})")
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
            approved_quantity=approved_quantity if approved else 0.0,
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
        contract_size = _field("contract_size", "trade_contract_size", default=1.0)
        quantity_increment = _field(
            "quantity_increment", "volume_step", "volume_min", default=0.0)
        instrument = Instrument(
            symbol, InstrumentType.SYNTHETIC, str(observation.get("venue") or "runtime"),
            contract_size=max(contract_size, 1e-12),
            quantity_increment=quantity_increment if quantity_increment > 0 else None)
        equity = _field("equity", default=1.0)
        quality = str(observation.get("data_quality", "valid")).lower()
        state = RiskState(
            account_id=str(live.get("account_id", observation.get("account_id", "runtime"))),
            equity=equity,
            portfolio_exposure=_field("portfolio_exposure", "exposure"),
            daily_pnl=_field("daily_pnl"),
            drawdown_fraction=_field("drawdown_fraction", "drawdown"),
            open_positions=int(_field("open_positions")),
            # Only an explicit "valid" marker is fresh. "unknown" and
            # "degraded" feeds cannot authorize risk — unverified data
            # fails closed, same as invalid/stale.
            data_is_fresh=(quality == "valid"
                           and observation.get("data_is_fresh") is not False),
            trading_enabled=bool(observation.get("trading_enabled", True)),
            emergency=bool(observation.get("emergency", False)),
        )
        signal = Signal(
            signal_id=str(action.get("trade_id", "runtime-signal")),
            instrument=instrument,
            direction=str(action.get("action", "WAIT")),
            confidence=float(action.get("confidence", 0.0) or 0.0),
            metadata={
                "quantity": action.get("quantity", 0.0),
                # Mark price for projected-exposure accounting: the action
                # payload wins, then the validated observation.
                "price": action.get("price") or observation.get("price")
                         or observation.get("close"),
                # Venue floor for the sizing path — proposals smaller than
                # this reject rather than emit an untradable order.
                "quantity_min": _field("quantity_min", "volume_min",
                                       default=0.0),
            },
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
