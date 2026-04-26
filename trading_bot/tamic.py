"""TAMIC: Time-Aware Market Intelligence and Control.

TAMIC is the timing and temporal-risk layer for AlphaAlgo. It does not place
orders. It evaluates whether a signal is fresh, horizon-consistent, market-time
aware, and safe enough to pass to downstream portfolio or execution systems.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
import math
import time
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple


class TimeHorizon(str, Enum):
    """Supported TAMIC decision horizons."""

    MICROSTRUCTURE = "microstructure"
    INTRADAY = "intraday"
    SHORT_SWING = "short_swing"
    MEDIUM_HORIZON = "medium_horizon"
    LONG_HORIZON = "long_horizon"


class MarketTimeState(str, Enum):
    """How fast market time is moving relative to normal clock time."""

    NORMAL = "normal"
    ACCELERATED = "accelerated"
    EXTREME = "extreme"
    HALTED = "halted"


class SignalHalfLife(str, Enum):
    """Qualitative state of signal decay."""

    FRESH = "fresh"
    DECAYING = "decaying"
    STALE = "stale"
    EXPIRED = "expired"


class ForbiddenBehaviorType(str, Enum):
    """Temporal behaviors TAMIC must reject."""

    CHASE_RECENT_PERFORMANCE = "chase_recent_performance"
    MIX_TIME_HORIZONS = "mix_time_horizons"
    REUSE_EXPIRED_SIGNALS = "reuse_expired_signals"
    RETRAIN_DURING_DRAWDOWNS = "retrain_during_drawdowns"
    INCREASE_LEVERAGE_AFTER_LOSSES = "increase_leverage_after_losses"
    ASSUME_STATIONARITY = "assume_stationarity"


@dataclass(frozen=True)
class TAMICConfig:
    """Runtime knobs for TAMIC gates."""

    min_trade_confidence: float = 0.62
    max_trade_volatility: float = 0.045
    extreme_volatility: float = 0.05
    accelerated_volatility: float = 0.025
    max_spread: float = 0.025
    max_drawdown_for_retraining: float = 0.08
    recent_performance_chase_threshold: float = 0.12
    stationarity_volatility_change_threshold: float = 0.35
    max_loss_streak_for_leverage_increase: int = 2
    max_base_exposure: float = 0.50
    horizon_half_life_seconds: Mapping[TimeHorizon, float] = field(
        default_factory=lambda: {
            TimeHorizon.MICROSTRUCTURE: 30.0,
            TimeHorizon.INTRADAY: 30.0 * 60.0,
            TimeHorizon.SHORT_SWING: 6.0 * 60.0 * 60.0,
            TimeHorizon.MEDIUM_HORIZON: 3.0 * 24.0 * 60.0 * 60.0,
            TimeHorizon.LONG_HORIZON: 14.0 * 24.0 * 60.0 * 60.0,
        }
    )


@dataclass(frozen=True)
class MarketTimeResult:
    """Market-time classification and drivers."""

    state: MarketTimeState
    acceleration_factor: float
    volatility: float
    liquidity: float
    spread: float
    reasons: Tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "state": self.state.value,
            "acceleration_factor": self.acceleration_factor,
            "volatility": self.volatility,
            "liquidity": self.liquidity,
            "spread": self.spread,
            "reasons": list(self.reasons),
        }


@dataclass(frozen=True)
class SignalDecayResult:
    """Signal freshness and decay result."""

    half_life_seconds: float = 0.0
    age_seconds: float = 0.0
    decay_factor: float = 1.0
    half_life_state: SignalHalfLife = SignalHalfLife.FRESH
    expired: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "half_life_seconds": self.half_life_seconds,
            "age_seconds": self.age_seconds,
            "decay_factor": self.decay_factor,
            "half_life_state": self.half_life_state.value,
            "expired": self.expired,
        }


@dataclass(frozen=True)
class ForbiddenBehaviorResult:
    """Forbidden temporal behavior check."""

    behavior: ForbiddenBehaviorType
    detected: bool
    severity: float = 0.0
    message: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "behavior": self.behavior.value,
            "detected": self.detected,
            "severity": self.severity,
            "message": self.message,
        }


@dataclass(frozen=True)
class ConfidenceResult:
    """Confidence humility report."""

    raw_confidence: float
    calibrated_confidence: float
    uncertainty_penalty: float
    reasons: Tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "raw_confidence": self.raw_confidence,
            "calibrated_confidence": self.calibrated_confidence,
            "uncertainty_penalty": self.uncertainty_penalty,
            "reasons": list(self.reasons),
        }


@dataclass(frozen=True)
class RiskAssessmentResult:
    """Time-aware risk sizing result."""

    allowed: bool
    exposure: float
    risk_score: float
    reasons: Tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "allowed": self.allowed,
            "exposure": self.exposure,
            "risk_score": self.risk_score,
            "reasons": list(self.reasons),
        }


@dataclass(frozen=True)
class TAMICDecision:
    """Final TAMIC decision package."""

    symbol: str = ""
    time_horizon: TimeHorizon = TimeHorizon.INTRADAY
    is_trade_recommended: bool = False
    confidence_level: float = 0.0
    exposure_recommendation: float = 0.0
    market_time_state: MarketTimeState = MarketTimeState.NORMAL
    signal_half_life: SignalHalfLife = SignalHalfLife.FRESH
    no_trade_reason: Optional[str] = None
    forbidden_behaviors: Tuple[ForbiddenBehaviorResult, ...] = field(default_factory=tuple)
    market_time: Optional[MarketTimeResult] = None
    signal_decay: Optional[SignalDecayResult] = None
    confidence: Optional[ConfidenceResult] = None
    risk: Optional[RiskAssessmentResult] = None
    reasoning_chain: Tuple[str, ...] = field(default_factory=tuple)
    generated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol,
            "time_horizon": self.time_horizon.value,
            "is_trade_recommended": self.is_trade_recommended,
            "confidence_level": self.confidence_level,
            "exposure_recommendation": self.exposure_recommendation,
            "market_time_state": self.market_time_state.value,
            "signal_half_life": self.signal_half_life.value,
            "no_trade_reason": self.no_trade_reason,
            "forbidden_behaviors": [item.to_dict() for item in self.forbidden_behaviors],
            "market_time": self.market_time.to_dict() if self.market_time else None,
            "signal_decay": self.signal_decay.to_dict() if self.signal_decay else None,
            "confidence": self.confidence.to_dict() if self.confidence else None,
            "risk": self.risk.to_dict() if self.risk else None,
            "reasoning_chain": list(self.reasoning_chain),
            "generated_at": self.generated_at.isoformat(),
        }


class HorizonSegmentation:
    """Normalize and validate horizon-specific market data."""

    HORIZON_KEYS = {
        "microstructure_data": TimeHorizon.MICROSTRUCTURE,
        "intraday_data": TimeHorizon.INTRADAY,
        "short_swing_data": TimeHorizon.SHORT_SWING,
        "medium_horizon_data": TimeHorizon.MEDIUM_HORIZON,
        "long_horizon_data": TimeHorizon.LONG_HORIZON,
    }

    def normalize(self, horizon: Any) -> TimeHorizon:
        if isinstance(horizon, TimeHorizon):
            return horizon
        if isinstance(horizon, str):
            normalized = horizon.strip().lower().replace("-", "_")
            for item in TimeHorizon:
                if item.value == normalized or item.name.lower() == normalized:
                    return item
        return TimeHorizon.INTRADAY

    def detect_mixed_horizons(self, market_data: Mapping[str, Any], target: TimeHorizon) -> List[str]:
        present = [key for key in self.HORIZON_KEYS if key in market_data]
        if len(present) <= 1:
            return []
        target_key = next((key for key, value in self.HORIZON_KEYS.items() if value == target), None)
        return [key for key in present if key != target_key]


class MarketTimeEngine:
    """Classify market-time acceleration from volatility, liquidity, and spread."""

    def __init__(self, config: Optional[TAMICConfig] = None):
        self.config = config or TAMICConfig()

    def evaluate_market_time(self, market_data: Optional[Mapping[str, Any]] = None) -> MarketTimeResult:
        data = market_data or {}
        volatility = _extract_volatility(data)
        liquidity = max(_float(data.get("liquidity"), 1.0), 0.0)
        spread = max(_float(data.get("spread"), 0.0), 0.0)
        reasons: List[str] = []

        acceleration = 1.0
        acceleration += min(volatility / max(self.config.accelerated_volatility, 0.0001), 4.0) * 0.35
        if spread > self.config.max_spread:
            acceleration += 0.75
            reasons.append("spread exceeds temporal liquidity limit")
        if liquidity and liquidity < 0.5:
            acceleration += 0.50
            reasons.append("liquidity is thin")
        if bool(data.get("halted")):
            return MarketTimeResult(
                state=MarketTimeState.HALTED,
                acceleration_factor=0.0,
                volatility=volatility,
                liquidity=liquidity,
                spread=spread,
                reasons=("market is halted",),
            )

        if volatility >= self.config.extreme_volatility or acceleration >= 2.8:
            state = MarketTimeState.EXTREME
            reasons.append("market time is extreme")
        elif volatility >= self.config.accelerated_volatility or acceleration >= 1.7:
            state = MarketTimeState.ACCELERATED
            reasons.append("market time is accelerated")
        else:
            state = MarketTimeState.NORMAL
            reasons.append("market time is normal")

        return MarketTimeResult(
            state=state,
            acceleration_factor=round(acceleration, 4),
            volatility=volatility,
            liquidity=liquidity,
            spread=spread,
            reasons=tuple(reasons),
        )


class SignalDecayEngine:
    """Estimate signal age, half-life, and decay."""

    def __init__(self, config: Optional[TAMICConfig] = None):
        self.config = config or TAMICConfig()

    def analyze(
        self,
        horizon: TimeHorizon,
        market_data: Mapping[str, Any],
        market_time: MarketTimeResult,
        now: Optional[float] = None,
    ) -> SignalDecayResult:
        now_ts = now if now is not None else time.time()
        timestamp = _float(market_data.get("signal_timestamp", market_data.get("timestamp")), now_ts)
        age_seconds = max(now_ts - timestamp, 0.0)
        base_half_life = float(self.config.horizon_half_life_seconds.get(horizon, 1800.0))
        adjusted_half_life = base_half_life / max(market_time.acceleration_factor, 0.25)
        decay_factor = math.exp(-age_seconds / max(adjusted_half_life, 1.0))

        if age_seconds >= adjusted_half_life * 3.0:
            state = SignalHalfLife.EXPIRED
        elif age_seconds >= adjusted_half_life * 1.5:
            state = SignalHalfLife.STALE
        elif age_seconds >= adjusted_half_life * 0.5:
            state = SignalHalfLife.DECAYING
        else:
            state = SignalHalfLife.FRESH

        return SignalDecayResult(
            half_life_seconds=round(adjusted_half_life, 4),
            age_seconds=round(age_seconds, 4),
            decay_factor=round(max(0.0, min(decay_factor, 1.0)), 6),
            half_life_state=state,
            expired=state == SignalHalfLife.EXPIRED,
        )


class ForbiddenBehaviorGuard:
    """Detect temporal anti-patterns before a trade is recommended."""

    def __init__(self, config: Optional[TAMICConfig] = None):
        self.config = config or TAMICConfig()

    def check_behaviors(
        self,
        horizon: TimeHorizon,
        market_data: Optional[Mapping[str, Any]] = None,
        signal_decay: Optional[SignalDecayResult] = None,
        horizon_segmentation: Optional[HorizonSegmentation] = None,
    ) -> Tuple[ForbiddenBehaviorResult, ...]:
        data = market_data or {}
        segmentation = horizon_segmentation or HorizonSegmentation()
        results: List[ForbiddenBehaviorResult] = []

        recent_performance = abs(_float(data.get("recent_performance"), 0.0))
        results.append(
            ForbiddenBehaviorResult(
                ForbiddenBehaviorType.CHASE_RECENT_PERFORMANCE,
                recent_performance > self.config.recent_performance_chase_threshold,
                min(recent_performance / max(self.config.recent_performance_chase_threshold, 0.0001), 2.0),
                "recent performance impulse is too strong to chase safely",
            )
        )

        mixed = segmentation.detect_mixed_horizons(data, horizon)
        results.append(
            ForbiddenBehaviorResult(
                ForbiddenBehaviorType.MIX_TIME_HORIZONS,
                bool(mixed),
                1.0 if mixed else 0.0,
                "market data mixes incompatible time horizons" if mixed else "",
            )
        )

        expired = bool(signal_decay and signal_decay.expired)
        results.append(
            ForbiddenBehaviorResult(
                ForbiddenBehaviorType.REUSE_EXPIRED_SIGNALS,
                expired,
                1.0 if expired else 0.0,
                "signal is past its time-aware half-life limit" if expired else "",
            )
        )

        drawdown = _normalize_percentage(data.get("drawdown"), 0.0)
        retraining = bool(data.get("is_retraining", data.get("retraining")))
        results.append(
            ForbiddenBehaviorResult(
                ForbiddenBehaviorType.RETRAIN_DURING_DRAWDOWNS,
                drawdown > self.config.max_drawdown_for_retraining and retraining,
                min(drawdown / max(self.config.max_drawdown_for_retraining, 0.0001), 2.0),
                "model retraining is blocked during deep drawdown",
            )
        )

        loss_streak = int(_float(data.get("loss_streak"), 0.0))
        previous_leverage = _float(data.get("previous_leverage"), _float(data.get("current_leverage"), 1.0))
        current_leverage = _float(data.get("current_leverage"), previous_leverage)
        results.append(
            ForbiddenBehaviorResult(
                ForbiddenBehaviorType.INCREASE_LEVERAGE_AFTER_LOSSES,
                loss_streak >= self.config.max_loss_streak_for_leverage_increase
                and current_leverage > previous_leverage,
                min(max(current_leverage - previous_leverage, 0.0), 2.0),
                "leverage increase after a loss streak is blocked",
            )
        )

        volatility_change = abs(_float(data.get("volatility_change"), 0.0))
        regime_changed = bool(data.get("regime_changed"))
        results.append(
            ForbiddenBehaviorResult(
                ForbiddenBehaviorType.ASSUME_STATIONARITY,
                regime_changed or volatility_change > self.config.stationarity_volatility_change_threshold,
                min(max(volatility_change, 1.0 if regime_changed else 0.0), 2.0),
                "regime change requires revalidation before trading",
            )
        )

        return tuple(results)


class ConfidenceHumilityControl:
    """Calibrate confidence down under temporal uncertainty."""

    def __init__(self, config: Optional[TAMICConfig] = None):
        self.config = config or TAMICConfig()
        self.outcomes: List[Tuple[float, bool]] = []

    def calibrate_confidence(
        self,
        raw_confidence: float,
        market_time: MarketTimeResult,
        signal_decay: SignalDecayResult,
        forbidden_behaviors: Sequence[ForbiddenBehaviorResult],
    ) -> ConfidenceResult:
        reasons: List[str] = []
        penalty = 0.0

        penalty += max(market_time.acceleration_factor - 1.0, 0.0) * 0.08
        if market_time.state == MarketTimeState.EXTREME:
            penalty += 0.18
            reasons.append("extreme market time")
        elif market_time.state == MarketTimeState.ACCELERATED:
            penalty += 0.08
            reasons.append("accelerated market time")

        decay_penalty = 1.0 - signal_decay.decay_factor
        penalty += decay_penalty * 0.30
        if signal_decay.half_life_state != SignalHalfLife.FRESH:
            reasons.append(f"signal is {signal_decay.half_life_state.value}")

        detected = [item for item in forbidden_behaviors if item.detected]
        if detected:
            penalty += min(0.40, sum(item.severity for item in detected) * 0.10)
            reasons.extend(item.behavior.value for item in detected)

        calibrated = max(0.0, min(raw_confidence - penalty, 1.0))
        return ConfidenceResult(
            raw_confidence=round(raw_confidence, 6),
            calibrated_confidence=round(calibrated, 6),
            uncertainty_penalty=round(min(penalty, 1.0), 6),
            reasons=tuple(dict.fromkeys(reasons)),
        )

    def record_outcome(self, confidence: float, success: bool) -> None:
        self.outcomes.append((max(0.0, min(confidence, 1.0)), bool(success)))


class TimeBasedRiskManager:
    """Convert TAMIC confidence into exposure under temporal risk."""

    def __init__(self, config: Optional[TAMICConfig] = None):
        self.config = config or TAMICConfig()

    def evaluate_risk(
        self,
        confidence: ConfidenceResult,
        market_time: MarketTimeResult,
        market_data: Optional[Mapping[str, Any]] = None,
    ) -> RiskAssessmentResult:
        data = market_data or {}
        reasons: List[str] = []
        risk_score = 0.0

        risk_score += min(market_time.volatility / max(self.config.max_trade_volatility, 0.0001), 2.0) * 0.30
        risk_score += max(market_time.acceleration_factor - 1.0, 0.0) * 0.15
        risk_score += _normalize_percentage(data.get("drawdown"), 0.0) * 2.0
        if market_time.spread > self.config.max_spread:
            risk_score += 0.25
            reasons.append("spread too wide")
        if market_time.state in {MarketTimeState.EXTREME, MarketTimeState.HALTED}:
            risk_score += 0.35
            reasons.append(f"market time state is {market_time.state.value}")

        risk_score = max(0.0, min(risk_score, 1.0))
        exposure = self.config.max_base_exposure * confidence.calibrated_confidence * (1.0 - risk_score)
        exposure = max(0.0, min(exposure, self.config.max_base_exposure))
        allowed = risk_score < 0.85 and confidence.calibrated_confidence >= self.config.min_trade_confidence

        if not allowed and confidence.calibrated_confidence < self.config.min_trade_confidence:
            reasons.append("confidence below TAMIC trade floor")

        return RiskAssessmentResult(
            allowed=allowed,
            exposure=round(exposure, 6),
            risk_score=round(risk_score, 6),
            reasons=tuple(dict.fromkeys(reasons)),
        )


class TAMIC:
    """Main Time-Aware Market Intelligence and Control system."""

    def __init__(self, config: Optional[Mapping[str, Any]] = None):
        self.config = _coerce_config(config)
        self.running = False
        self.evaluation_count = 0
        self.last_decision: Optional[TAMICDecision] = None
        self.horizon_segmentation = HorizonSegmentation()
        self.market_time_engine = MarketTimeEngine(self.config)
        self.signal_decay_engine = SignalDecayEngine(self.config)
        self.forbidden_guard = ForbiddenBehaviorGuard(self.config)
        self.confidence_control = ConfidenceHumilityControl(self.config)
        self.time_risk = TimeBasedRiskManager(self.config)
        self.components: Dict[str, Any] = {
            "horizon_segmentation": self.horizon_segmentation,
            "signal_decay": self.signal_decay_engine,
            "market_time": self.market_time_engine,
            "time_risk": self.time_risk,
            "forbidden_behaviors": self.forbidden_guard,
            "confidence_control": self.confidence_control,
        }

    def add_component(self, name: Optional[str] = None, component: Optional[Any] = None) -> None:
        if name:
            self.components[name] = component

    async def start(self) -> None:
        self.running = True

    async def stop(self) -> None:
        self.running = False

    async def evaluate_market(
        self,
        symbol: str = "",
        horizon: Any = TimeHorizon.INTRADAY,
        market_data: Optional[Mapping[str, Any]] = None,
    ) -> TAMICDecision:
        data = market_data or {}
        normalized_horizon = self.horizon_segmentation.normalize(horizon)
        market_time = self.market_time_engine.evaluate_market_time(data)
        signal_decay = self.signal_decay_engine.analyze(normalized_horizon, data, market_time)
        forbidden = self.forbidden_guard.check_behaviors(
            normalized_horizon,
            data,
            signal_decay,
            self.horizon_segmentation,
        )
        raw_confidence = _raw_signal_confidence(data, normalized_horizon)
        confidence = self.confidence_control.calibrate_confidence(
            raw_confidence,
            market_time,
            signal_decay,
            forbidden,
        )
        risk = self.time_risk.evaluate_risk(confidence, market_time, data)

        blocking_reasons = self._blocking_reasons(market_time, signal_decay, forbidden, confidence, risk)
        recommended = not blocking_reasons
        no_trade_reason = "; ".join(blocking_reasons) if blocking_reasons else None
        exposure = risk.exposure if recommended else 0.0

        reasoning = [
            f"horizon={normalized_horizon.value}",
            f"market_time={market_time.state.value}",
            f"signal_half_life={signal_decay.half_life_state.value}",
            f"confidence={confidence.calibrated_confidence:.3f}",
            f"risk_score={risk.risk_score:.3f}",
        ]
        if no_trade_reason:
            reasoning.append(f"no_trade={no_trade_reason}")

        decision = TAMICDecision(
            symbol=symbol or str(data.get("symbol", "")),
            time_horizon=normalized_horizon,
            is_trade_recommended=recommended,
            confidence_level=confidence.calibrated_confidence,
            exposure_recommendation=exposure,
            market_time_state=market_time.state,
            signal_half_life=signal_decay.half_life_state,
            no_trade_reason=no_trade_reason,
            forbidden_behaviors=forbidden,
            market_time=market_time,
            signal_decay=signal_decay,
            confidence=confidence,
            risk=risk,
            reasoning_chain=tuple(reasoning),
        )
        self.last_decision = decision
        self.evaluation_count += 1
        return decision

    def analyze(self, market_snapshot: Optional[Mapping[str, Any]] = None) -> Dict[str, Any]:
        """Synchronous integration hook used by archive orchestrators."""
        snapshot = market_snapshot or {}
        decision = self._evaluate_sync(
            symbol=str(snapshot.get("symbol", "")),
            horizon=snapshot.get("time_horizon", snapshot.get("horizon", TimeHorizon.INTRADAY)),
            market_data=snapshot,
        )
        return decision.to_dict()

    def process(self, market_snapshot: Optional[Mapping[str, Any]] = None) -> Dict[str, Any]:
        """Alias for analyze."""
        return self.analyze(market_snapshot)

    def get_status(self) -> Dict[str, Any]:
        return {
            "running": self.running,
            "available": True,
            "components": sorted(self.components.keys()),
            "evaluation_count": self.evaluation_count,
            "last_decision": self.last_decision.to_dict() if self.last_decision else None,
        }

    def _evaluate_sync(self, symbol: str, horizon: Any, market_data: Mapping[str, Any]) -> TAMICDecision:
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(self.evaluate_market(symbol=symbol, horizon=horizon, market_data=market_data))

        # If called from a running loop, use the deterministic sync path to avoid
        # nested event-loop errors in legacy integrations.
        normalized_horizon = self.horizon_segmentation.normalize(horizon)
        market_time = self.market_time_engine.evaluate_market_time(market_data)
        signal_decay = self.signal_decay_engine.analyze(normalized_horizon, market_data, market_time)
        forbidden = self.forbidden_guard.check_behaviors(
            normalized_horizon,
            market_data,
            signal_decay,
            self.horizon_segmentation,
        )
        confidence = self.confidence_control.calibrate_confidence(
            _raw_signal_confidence(market_data, normalized_horizon),
            market_time,
            signal_decay,
            forbidden,
        )
        risk = self.time_risk.evaluate_risk(confidence, market_time, market_data)
        blocking_reasons = self._blocking_reasons(market_time, signal_decay, forbidden, confidence, risk)
        decision = TAMICDecision(
            symbol=symbol or str(market_data.get("symbol", "")),
            time_horizon=normalized_horizon,
            is_trade_recommended=not blocking_reasons,
            confidence_level=confidence.calibrated_confidence,
            exposure_recommendation=risk.exposure if not blocking_reasons else 0.0,
            market_time_state=market_time.state,
            signal_half_life=signal_decay.half_life_state,
            no_trade_reason="; ".join(blocking_reasons) if blocking_reasons else None,
            forbidden_behaviors=forbidden,
            market_time=market_time,
            signal_decay=signal_decay,
            confidence=confidence,
            risk=risk,
        )
        self.last_decision = decision
        self.evaluation_count += 1
        return decision

    def _blocking_reasons(
        self,
        market_time: MarketTimeResult,
        signal_decay: SignalDecayResult,
        forbidden: Sequence[ForbiddenBehaviorResult],
        confidence: ConfidenceResult,
        risk: RiskAssessmentResult,
    ) -> List[str]:
        reasons: List[str] = []
        if market_time.state == MarketTimeState.HALTED:
            reasons.append("market halted")
        if market_time.state == MarketTimeState.EXTREME:
            reasons.append("extreme market time")
        if signal_decay.expired:
            reasons.append("expired signal")
        for item in forbidden:
            if item.detected:
                reasons.append(item.message or item.behavior.value)
        if confidence.calibrated_confidence < self.config.min_trade_confidence:
            reasons.append("low time-adjusted confidence")
        if not risk.allowed:
            reasons.extend(risk.reasons)
        return list(dict.fromkeys(reason for reason in reasons if reason))


class TAMICGovernanceLayer:
    """Small governance adapter that vetoes trades when TAMIC blocks timing."""

    def __init__(self, tamic: Optional[TAMIC] = None):
        self.tamic = tamic or TAMIC()

    def process(self, market_snapshot: Optional[Mapping[str, Any]] = None) -> Dict[str, Any]:
        result = self.tamic.analyze(market_snapshot)
        return {
            "approved": bool(result.get("is_trade_recommended")),
            "tamic": result,
            "reason": result.get("no_trade_reason"),
        }


class TAMICIntegration:
    """Bridge TAMIC into legacy capital-governance flows."""

    def __init__(self, tamic: Optional[TAMIC] = None):
        self.tamic = tamic or TAMIC()
        self.governance_layer = TAMICGovernanceLayer(self.tamic)

    def integrate_with_capital_governance(self, market_snapshot: Optional[Mapping[str, Any]] = None) -> Dict[str, Any]:
        return self.governance_layer.process(market_snapshot)


class TAMICOrchestrator(TAMIC):
    """Backward-compatible orchestrator name expected by existing integrations."""


def create_tamic(config: Optional[Mapping[str, Any]] = None) -> TAMIC:
    return TAMIC(config=config)


async def quick_start(config: Optional[Mapping[str, Any]] = None) -> TAMIC:
    tamic = create_tamic(config)
    await tamic.start()
    return tamic


def create_tamic_integration(config: Optional[Mapping[str, Any]] = None) -> TAMICIntegration:
    return TAMICIntegration(create_tamic(config))


async def evaluate_market(
    symbol: str = "",
    horizon: Any = TimeHorizon.INTRADAY,
    market_data: Optional[Mapping[str, Any]] = None,
) -> TAMICDecision:
    tamic = create_tamic()
    return await tamic.evaluate_market(symbol=symbol, horizon=horizon, market_data=market_data or {})


def get_status() -> Dict[str, Any]:
    return create_tamic().get_status()


def add_component(name: Optional[str] = None, component: Optional[Any] = None) -> None:
    create_tamic().add_component(name, component)


def _coerce_config(config: Optional[Mapping[str, Any]]) -> TAMICConfig:
    if isinstance(config, TAMICConfig):
        return config
    if not config:
        return TAMICConfig()
    allowed = TAMICConfig.__dataclass_fields__.keys()
    values = {key: value for key, value in config.items() if key in allowed and key != "horizon_half_life_seconds"}
    if "horizon_half_life_seconds" in config:
        values["horizon_half_life_seconds"] = {
            HorizonSegmentation().normalize(key): float(value)
            for key, value in dict(config["horizon_half_life_seconds"]).items()
        }
    return TAMICConfig(**values)


def _raw_signal_confidence(market_data: Mapping[str, Any], horizon: TimeHorizon) -> float:
    if "signal_confidence" in market_data:
        return max(0.0, min(_float(market_data.get("signal_confidence"), 0.5), 1.0))

    close = _series(market_data.get("close"))
    returns = _returns(close)
    if not returns:
        return 0.55

    mean_return = sum(returns[-10:]) / max(len(returns[-10:]), 1)
    volatility = _std(returns[-20:]) or 0.0001
    trend_strength = abs(mean_return) / volatility
    horizon_bonus = {
        TimeHorizon.MICROSTRUCTURE: 0.00,
        TimeHorizon.INTRADAY: 0.03,
        TimeHorizon.SHORT_SWING: 0.04,
        TimeHorizon.MEDIUM_HORIZON: 0.02,
        TimeHorizon.LONG_HORIZON: 0.01,
    }[horizon]
    confidence = 0.52 + min(trend_strength, 2.0) * 0.12 + horizon_bonus
    if str(market_data.get("market_regime", "")).lower() in {"trending", "trend", "risk_on"}:
        confidence += 0.06
    return max(0.0, min(confidence, 0.92))


def _extract_volatility(market_data: Mapping[str, Any]) -> float:
    explicit = market_data.get("volatility")
    if explicit is not None:
        return max(_float(explicit, 0.0), 0.0)
    returns = _returns(_series(market_data.get("close")))
    if not returns:
        return 0.0
    return _std(returns) * math.sqrt(252)


def _series(value: Any) -> List[float]:
    if value is None:
        return []
    if isinstance(value, (int, float)):
        return [float(value)]
    try:
        return [float(item) for item in value if item is not None]
    except TypeError:
        return []


def _returns(values: Sequence[float]) -> List[float]:
    returns: List[float] = []
    for previous, current in zip(values, values[1:]):
        if previous:
            returns.append((current - previous) / previous)
    return returns


def _std(values: Sequence[float]) -> float:
    if not values:
        return 0.0
    mean = sum(values) / len(values)
    variance = sum((item - mean) ** 2 for item in values) / len(values)
    return math.sqrt(variance)


def _float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _normalize_percentage(value: Any, default: float = 0.0) -> float:
    raw = _float(value, default)
    return raw / 100.0 if raw > 1.0 else raw


__all__ = [
    "TimeHorizon",
    "MarketTimeState",
    "SignalHalfLife",
    "ForbiddenBehaviorType",
    "TAMICConfig",
    "MarketTimeResult",
    "SignalDecayResult",
    "ForbiddenBehaviorResult",
    "ConfidenceResult",
    "RiskAssessmentResult",
    "TAMICDecision",
    "HorizonSegmentation",
    "MarketTimeEngine",
    "SignalDecayEngine",
    "ForbiddenBehaviorGuard",
    "ConfidenceHumilityControl",
    "TimeBasedRiskManager",
    "TAMIC",
    "TAMICGovernanceLayer",
    "TAMICIntegration",
    "TAMICOrchestrator",
    "create_tamic",
    "quick_start",
    "create_tamic_integration",
    "evaluate_market",
    "get_status",
    "add_component",
]
