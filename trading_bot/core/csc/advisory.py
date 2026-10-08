"""Universal advisory wiring — every AI-adjacent module under CSC.

One AI means exactly two statuses for every AI-named module in the
repository:

- ``attached``: wrapped by ``AdvisoryModuleAdapter`` and registered via
  ``configure_cognition`` — its output joins the evidence channel as
  ``advisory_only`` artifacts with every authority field stripped.
- ``unwired``: explicitly listed in the manifest with a reason — the
  module cannot hold decision authority because nothing reaches it from
  the decision path at all.

The manifest therefore doubles as the audit map: a reader can enumerate
the whole orphan-AI surface and see, per module, either its advisory
capability or why it is inert.
"""

from __future__ import annotations

import asyncio
import collections
import dataclasses
import enum
import inspect
import logging
from datetime import date, datetime
from typing import Any, Callable, Dict, List, Mapping, Optional, Tuple

import numpy as np

from trading_bot.cognition.advisory_adapter import AUTHORITY_FIELDS

logger = logging.getLogger("alphaalgo.csc.advisory")


def _run_coro_sync(coro: Any, timeout_s: float = 5.0) -> Any:
    """Run a probe coroutine whether or not an event loop is already
    running. Assembly is called from async runtime entry points —
    run_until_complete() would fail inside a live loop, so the probe
    goes to a short-lived thread with its own loop when needed."""
    import asyncio
    import threading
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        # Fresh loop instead of asyncio.run() — asyncio.run() calls
        # set_event_loop(None) on exit, which would leave the calling
        # thread with no current loop for downstream callers.
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()
    box: Dict[str, Any] = {}

    def _worker() -> None:
        try:
            box["r"] = asyncio.run(coro)
        except Exception as exc:  # noqa: BLE001 - re-raised below
            box["e"] = exc

    t = threading.Thread(target=_worker, daemon=True)
    t.start()
    t.join(timeout_s)
    if t.is_alive():
        raise TimeoutError("advisory probe timed out")
    if "e" in box:
        raise box["e"]
    return box.get("r")


_DIRECTION_MAP = {
    "BUY": "BUY", "LONG": "BUY", "UP": "BUY", "BULLISH": "BUY",
    "SELL": "SELL", "SHORT": "SELL", "DOWN": "SELL", "BEARISH": "SELL",
    "HOLD": None, "NEUTRAL": None, "FLAT": None, "NONE": None,
}
_DIRECTION_KEYS = (
    "direction", "signal", "action", "bias", "recommendation", "verdict")
_CONFIDENCE_KEYS = (
    "confidence", "calibrated_probability", "probability",
    "win_probability", "score", "certainty")


def normalize_advisory(payload: Any) -> Dict[str, Any]:
    """Extract the advisory contract from a stripped payload.

    Returns ``{direction, confidence, evidence}`` — direction is
    BUY/SELL when the module expresses one (None for HOLD/NEUTRAL or
    non-directional output), confidence is [0,1] when expressed. The
    full stripped payload is preserved in ``evidence`` for audit.
    Top-level keys are searched first, then one level of nesting."""
    evidence = payload if isinstance(payload, dict) else {"result": payload}
    direction: Optional[str] = None
    confidence: Optional[float] = None

    def _scan(m: Mapping) -> Tuple[Optional[str], Optional[float]]:
        d: Optional[str] = None
        c: Optional[float] = None
        for key, value in m.items():
            k = str(key).lower()
            if d is None and k in _DIRECTION_KEYS and isinstance(
                    value, str) and value.upper() in _DIRECTION_MAP:
                d = _DIRECTION_MAP[value.upper()]
            if c is None and k in _CONFIDENCE_KEYS and isinstance(
                    value, (int, float)) and not isinstance(value, bool) \
                    and 0.0 <= float(value) <= 1.0:
                c = float(value)
        return d, c

    direction, confidence = _scan(evidence)
    if direction is None and confidence is None:
        for value in evidence.values():
            if isinstance(value, Mapping):
                direction, confidence = _scan(value)
                if direction is not None or confidence is not None:
                    break
    return {"direction": direction, "confidence": confidence,
            "evidence": evidence}


def _strip_authority(payload: Any) -> Any:
    """Recursively remove authority-bearing fields — same policy as
    ``AdvisoryCognitiveBrain``: advisory evidence must not carry approval,
    sizing, or execution vocabulary."""
    if isinstance(payload, Mapping):
        out: Dict[str, Any] = {}
        for key, value in payload.items():
            if key in AUTHORITY_FIELDS or str(key).startswith(
                    ("authorized", "risk_")):
                continue
            out[key] = _strip_authority(value)
        return out
    if isinstance(payload, (list, tuple)):
        return [_strip_authority(item) for item in payload]
    return payload


class AdvisoryModuleAdapter:
    """Wrap any callable ``fn(context) -> result`` as advisory-only.

    The callable may be sync or async; results are converted via
    ``to_dict`` when present, mappings pass through, anything else is
    wrapped as ``{"result": ...}``. Authority fields are stripped before
    the artifact ever reaches the evidence channel.
    """

    def __init__(self, capability_id: str,
                 fn: Callable[[Mapping[str, Any]], Any]) -> None:
        self.capability_id = capability_id
        self._fn = fn

    async def analyze(self, context: Mapping[str, Any]) -> Mapping[str, Any]:
        result = self._fn(context)
        if inspect.isawaitable(result):
            result = await result
        if hasattr(result, "to_dict"):
            result = result.to_dict()
        evidence = _strip_authority(result if isinstance(result, Mapping)
                                    else {"result": result})
        norm = normalize_advisory(evidence)
        return {
            "capability_id": self.capability_id,
            "direction": norm["direction"],
            "confidence": norm["confidence"],
            "evidence": norm["evidence"],
            "advisory_only": True,
        }




def _debate_service() -> AdvisoryModuleAdapter:
    """Legacy multi-agent debate as advisory evidence — translated into
    its typed DebateTopic/MarketContext from a raw observation."""
    from trading_bot.agents.multi_agent_debate import (
        DebateTopic, MarketContext, MultiAgentDebateSystem)

    system = MultiAgentDebateSystem()
    _trend_map = {"UP": "UP", "BULLISH": "UP",
                  "DOWN": "DOWN", "BEARISH": "DOWN"}

    async def analyze(ctx: Mapping[str, Any]) -> Any:
        symbol = str(ctx.get("symbol") or "UNKNOWN")
        trend = _trend_map.get(
            str(ctx.get("trend") or ctx.get("regime") or "").upper(),
            "SIDEWAYS")
        mc = MarketContext(
            symbol=symbol,
            current_price=float(
                ctx.get("price") or ctx.get("close") or 0.0) or 1.0,
            htf_trend=trend, ltf_trend=trend,
            volatility=float(ctx.get("volatility") or 0.0),
            volume_ratio=float(ctx.get("volume_ratio") or 1.0),
            key_levels={"support": [], "resistance": []},
            news_sentiment=float(ctx.get("sentiment") or 0.0),
            portfolio_exposure=0.0, correlation_risk=0.0)
        return await system.debate(
            DebateTopic(id=f"obs:{symbol}", content=f"market update {symbol}"),
            mc)

    return AdvisoryModuleAdapter("multi_agent_debate", analyze)


def _anomaly_service() -> AdvisoryModuleAdapter:
    """Statistical anomaly detection on the observation's price/vol fields."""
    from trading_bot.market_intelligence.event_detection import (
        AnomalyDetector)

    detector = AnomalyDetector()

    def analyze(ctx: Mapping[str, Any]) -> Any:
        price = ctx.get("price") or ctx.get("close")
        if not isinstance(price, (int, float)):
            return {"status": "no_numeric_price"}
        fn = (getattr(detector, "detect", None)
              or getattr(detector, "analyze", None)
              or getattr(detector, "detect_anomalies", None))
        if fn is None:
            return {"status": "no_detector_entry"}
        return fn({"price": float(price),
                   "volatility": ctx.get("volatility"),
                   "volume": ctx.get("volume"),
                   "symbol": ctx.get("symbol")})

    return AdvisoryModuleAdapter("market_anomaly_detection", analyze)


def _regime_classifier_service() -> AdvisoryModuleAdapter:
    """alphaalgo_core ensemble regime classifier → advisory regime call."""
    from trading_bot.alphaalgo_core.alphaalgo_core import MarketStateEngine

    engine = MarketStateEngine()
    _DIR = {"trending_bull": "BUY", "trending_bear": "SELL"}

    def analyze(ctx: Mapping[str, Any]) -> Any:
        # The engine expects a numeric trend scalar; the observation
        # carries a label. Feed it trend_strength (ER, [0,1]) signed by
        # the label's direction so sign and magnitude both land.
        data = dict(ctx)
        label = str(ctx.get("trend") or "").upper()
        sign = 1.0 if label in ("UP", "BULLISH") else (
            -1.0 if label in ("DOWN", "BEARISH") else 0.0)
        strength = ctx.get("trend_strength")
        data["trend"] = sign * float(strength) if isinstance(
            strength, (int, float)) else float(
                ctx.get("momentum") or 0.0)
        # The engine reads numerics raw — observations can carry
        # strings/sequences under those keys. Coerce or drop.
        for key in ("volatility", "volatility_percentile", "momentum",
                    "momentum_change", "data_quality", "price", "volume"):
            v = data.get(key)
            if not isinstance(v, (int, float)) or isinstance(v, bool):
                data.pop(key, None)
        c = engine.classify_regime(data)
        label = getattr(getattr(c, "label", None), "value",
                        str(getattr(c, "label", "")))
        return {
            "label": label,
            "direction": _DIR.get(str(label).lower()),
            "confidence": float(getattr(c, "confidence", 0.0) or 0.0),
            "stability": getattr(c, "stability", None),
            "ensemble_agreement": getattr(c, "ensemble_agreement", None),
            "transition_probability": getattr(
                c, "transition_probability", None),
        }

    return AdvisoryModuleAdapter("regime_classification", analyze)


def _adversarial_trade_service() -> AdvisoryModuleAdapter:
    """adversarial_decision's 9-step red-team evaluated on *both*
    directions — reports which survives; asymmetry is the signal."""
    from trading_bot.adversarial_decision.adversarial_core import (
        AdversarialDecisionEngine)

    engine = AdversarialDecisionEngine()

    def analyze(ctx: Mapping[str, Any]) -> Any:
        price = float(ctx.get("price") or ctx.get("close") or 0.0) or 1.0
        vol = float(ctx.get("volatility") or 0.005) or 0.005
        symbol = str(ctx.get("symbol") or "UNKNOWN")
        results = {}
        for d in ("BUY", "SELL"):
            dec = engine.evaluate_trade(
                symbol=symbol, direction=d, entry_price=price,
                stop_loss=price * (1 - 2 * vol) if d == "BUY"
                else price * (1 + 2 * vol),
                take_profit=price * (1 + 3 * vol) if d == "BUY"
                else price * (1 - 3 * vol),
                market_data=dict(ctx), signal_data=dict(ctx),
                portfolio_state={}, historical_data={})
            results[d.lower()] = {
                "approved": bool(getattr(dec, "approved", False)),
                "outcome": str(getattr(
                    getattr(dec, "outcome", None), "value",
                    getattr(dec, "outcome", ""))),
            }
        direction = (
            "BUY" if results["buy"]["approved"]
            and not results["sell"]["approved"]
            else "SELL" if results["sell"]["approved"]
            and not results["buy"]["approved"] else None)
        return {
            "direction": direction,
            "confidence": 0.6 if direction else None,
            "buy_eval": results["buy"], "sell_eval": results["sell"],
        }

    return AdvisoryModuleAdapter("adversarial_trade_eval", analyze)


def _trend_agent_service() -> AdvisoryModuleAdapter:
    """core_agent_system legacy trend-following agent → AgentProposal."""
    from trading_bot.core_agent_system.migrated_agents.legacy_agents import (
        TrendFollowingAgent)

    agent = TrendFollowingAgent()

    def analyze(ctx: Mapping[str, Any]) -> Any:
        return agent.analyze_market(dict(ctx))

    return AdvisoryModuleAdapter("trend_following_agent", analyze)


def _failure_mode_service() -> AdvisoryModuleAdapter:
    """intelligence_core model-degradation detector — evidence-only
    (no direction; still scored for audit completeness)."""
    from trading_bot.intelligence_core.failure_detector import (
        ModelDegradationDetector)

    detector = ModelDegradationDetector()

    def analyze(ctx: Mapping[str, Any]) -> Any:
        outs = detector.detect(dict(ctx), []) or []
        return {"detections": [str(o) for o in outs][:5],
                "count": len(outs)}

    return AdvisoryModuleAdapter("failure_mode_detection", analyze)


# ---------------------------------------------------------------------------
# Shared wiring helpers
# ---------------------------------------------------------------------------


def _num(value: Any) -> Optional[float]:
    """Best-effort float coercion; rejects bools/nan/inf/strings."""
    if isinstance(value, bool) or value is None:
        return None
    try:
        f = float(value)
    except (TypeError, ValueError):
        return None
    if f != f or f in (float("inf"), float("-inf")):
        return None
    return f


class _BarHistory:
    """Rolling OHLCV window accumulated from per-observation scalars.

    Many legacy analyzers expect a Series/DataFrame of bars while the
    advisory channel delivers one observation dict at a time. Accumulating
    a bounded window makes them honestly observation-callable — they emit
    ``{"status": "warming"}`` until enough real bars exist. No data is
    fabricated: the window is exactly the observations the CSC has seen.
    """

    def __init__(self, maxlen: int = 512) -> None:
        self._bars: "collections.deque" = collections.deque(maxlen=maxlen)

    def add(self, ctx: Mapping[str, Any]) -> int:
        close = _num(ctx.get("close") or ctx.get("price"))
        if close is None:
            return len(self._bars)
        self._bars.append({
            "open": _num(ctx.get("open")) or close,
            "high": _num(ctx.get("high")) or close,
            "low": _num(ctx.get("low")) or close,
            "close": close,
            "volume": _num(ctx.get("volume")) or 0.0,
        })
        return len(self._bars)

    def __len__(self) -> int:
        return len(self._bars)

    def bars(self, last: Optional[int] = None) -> List[Dict[str, float]]:
        bars = list(self._bars)
        return bars[-last:] if last else bars

    def frame(self) -> Any:
        import pandas as pd
        return pd.DataFrame(list(self._bars))

    def prices(self) -> List[float]:
        return [b["close"] for b in self._bars]

    def volumes(self) -> List[float]:
        return [b["volume"] for b in self._bars]

    def returns(self) -> List[float]:
        p = self.prices()
        return [p[i] / p[i - 1] - 1.0 for i in range(1, len(p)) if p[i - 1]]


def _primitive(value: Any) -> Any:
    """Coerce analyzer outputs (enum/datetime/numpy/dataclass) into
    JSON-safe values so advisory evidence survives audit persistence."""
    if isinstance(value, Mapping):
        return {str(k): _primitive(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_primitive(v) for v in value[:50]]
    if isinstance(value, enum.Enum):
        return value.value
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, np.generic):
        return value.item()
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return _payload(value)
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def _payload(result: Any) -> Any:
    """Normalize an analyzer return value into a plain mapping."""
    if result is None:
        return {"result": None}
    if hasattr(result, "to_dict"):
        try:
            result = result.to_dict()
        except Exception:  # noqa: BLE001 - fall through to field extraction
            pass
    if dataclasses.is_dataclass(result) and not isinstance(result, type):
        result = {f.name: getattr(result, f.name)
                  for f in dataclasses.fields(result)}
    elif not isinstance(result, Mapping) and hasattr(result, "__dict__"):
        result = {k: v for k, v in vars(result).items()
                  if not k.startswith("_")}
    if isinstance(result, Mapping):
        return _primitive(result)
    if isinstance(result, (list, tuple)):
        return {"items": _primitive(list(result))}
    return {"result": _primitive(result)}


def _market_context(ctx: Mapping[str, Any]) -> Any:
    """Build the debate system's typed MarketContext from a raw obs."""
    from trading_bot.agents.multi_agent_debate import MarketContext
    trend_map = {"UP": "UP", "BULLISH": "UP", "DOWN": "DOWN",
                 "BEARISH": "DOWN"}
    symbol = str(ctx.get("symbol") or "UNKNOWN")
    trend = trend_map.get(
        str(ctx.get("trend") or ctx.get("regime") or "").upper(),
        "SIDEWAYS")
    return MarketContext(
        symbol=symbol,
        current_price=_num(ctx.get("price") or ctx.get("close")) or 1.0,
        htf_trend=trend, ltf_trend=trend,
        volatility=_num(ctx.get("volatility")) or 0.0,
        volume_ratio=_num(ctx.get("volume_ratio")) or 1.0,
        key_levels={"support": [], "resistance": []},
        news_sentiment=_num(ctx.get("sentiment")) or 0.0,
        portfolio_exposure=0.0, correlation_risk=0.0)


def _numeric_fields(ctx: Mapping[str, Any]) -> Dict[str, float]:
    return {str(k): _num(v) for k, v in ctx.items()
            if _num(v) is not None}


def _feature_vector(ctx: Mapping[str, Any]) -> List[float]:
    """Canonical numeric feature order for vector-input advisors."""
    return [
        _num(ctx.get("close") or ctx.get("price")) or 0.0,
        _num(ctx.get("volatility")) or 0.0,
        _num(ctx.get("trend_strength")) or 0.0,
        _num(ctx.get("momentum")) or 0.0,
        _num(ctx.get("rsi")) or 50.0,
        _num(ctx.get("sentiment")) or 0.0,
        _num(ctx.get("volume_ratio")) or 1.0,
    ]


# ---------------------------------------------------------------------------
# Bucket A — previously-unwired orphan packages
# ---------------------------------------------------------------------------


def _alpha_research_state_service() -> AdvisoryModuleAdapter:
    """alpha_research MarketStateClassifier over accumulated real bars."""
    import scipy.stats  # noqa: F401 - module guards scipy; without it
    # the classifier NameErrors mid-run, so skip at attach instead.
    from trading_bot.alpha_research.market_state_classifier import (
        MarketStateClassifier)

    clf = MarketStateClassifier()
    hist = _BarHistory()
    _DIR = {"up": "BUY", "bullish": "BUY", "trending_up": "BUY",
            "down": "SELL", "bearish": "SELL", "trending_down": "SELL"}

    def analyze(ctx: Mapping[str, Any]) -> Any:
        n = hist.add(ctx)
        if len(hist) < 40:
            return {"status": "warming", "bars": n}
        state = clf.classify(hist.frame())
        regime = str(getattr(getattr(state, "regime", None), "value",
                             getattr(state, "regime", "")))
        direction = _DIR.get(regime.lower())
        td = _num(getattr(state, "trend_direction", None))
        if direction is None and td is not None:
            direction = "BUY" if td > 0.25 else (
                "SELL" if td < -0.25 else None)
        out = _payload(state)
        out["direction"] = direction
        out["bars"] = len(hist)
        return out

    return AdvisoryModuleAdapter("alpha_research_market_state", analyze)


def _alpha_research_risk_service() -> AdvisoryModuleAdapter:
    """alpha_research RiskPredictor on RiskFactors synthesized from ctx."""
    import numpy as _np
    from trading_bot.alpha_research.dynamic_risk_matrix import (
        RiskFactors, RiskPredictor)

    predictor = RiskPredictor()
    _probe_factors = RiskFactors(
        volatility=0.01, volatility_regime="normal", trend_strength=0.2,
        market_regime="ranging", current_drawdown=0.0, portfolio_heat=0.0,
        correlation_risk=0.0, concentration_risk=0.0, recent_win_rate=0.5,
        sharpe_ratio=0.0, vix_level=20.0)
    # predict() scales inputs before checking is_trained, so an unfitted
    # scaler raises; fit it on a neutral factor matrix at attach.
    scaler = getattr(predictor, "scaler", None)
    if scaler is not None:
        n = len(predictor._factors_to_array(_probe_factors))
        scaler.fit(_np.zeros((4, n)))

    def analyze(ctx: Mapping[str, Any]) -> Any:
        trend = str(ctx.get("trend") or "").upper()
        factors = RiskFactors(
            volatility=_num(ctx.get("volatility")) or 0.0,
            volatility_regime="high" if (
                _num(ctx.get("volatility")) or 0.0) > 0.02 else "normal",
            trend_strength=_num(ctx.get("trend_strength")) or 0.0,
            market_regime=("trending" if trend in ("UP", "DOWN")
                           else "ranging"),
            current_drawdown=_num(ctx.get("drawdown")) or 0.0,
            portfolio_heat=_num(ctx.get("portfolio_heat")) or 0.0,
            correlation_risk=_num(ctx.get("correlation_risk")) or 0.0,
            concentration_risk=_num(ctx.get("concentration_risk")) or 0.0,
            recent_win_rate=_num(ctx.get("win_rate")) or 0.5,
            sharpe_ratio=_num(ctx.get("sharpe")) or 0.0,
            vix_level=_num(ctx.get("vix")) or 20.0,
        )
        return _payload(predictor.predict(factors))

    return AdvisoryModuleAdapter("alpha_research_risk_matrix", analyze)


def _alpha_research_predator_service() -> AdvisoryModuleAdapter:
    """alpha_research PredatorDefenseSystem — stream-fed per observation.

    Each observation updates quote/trade/candle state with real values;
    detectors fire only once their internal windows fill — honest
    streaming evidence, never fabricated ticks.
    """
    from trading_bot.alpha_research.predator_defense import (
        PredatorDefenseSystem)

    system = PredatorDefenseSystem()

    def analyze(ctx: Mapping[str, Any]) -> Any:
        price = _num(ctx.get("close") or ctx.get("price"))
        if price is None:
            return {"status": "no_price"}
        spread = _num(ctx.get("spread")) or price * 1e-4
        ts = datetime.now()
        try:
            system.update_quote(price - spread / 2, price + spread / 2, ts)
        except Exception:  # noqa: BLE001 - optional feed
            pass
        vol = _num(ctx.get("volume"))
        if vol:
            try:
                system.update_trade(price, vol, str(
                    ctx.get("trend") or "buy").lower(), ts)
            except Exception:  # noqa: BLE001 - optional feed
                pass
        hist_bar = {
            "open": _num(ctx.get("open")) or price,
            "high": _num(ctx.get("high")) or price,
            "low": _num(ctx.get("low")) or price,
        }
        try:
            system.update_candle(hist_bar["open"], hist_bar["high"],
                                 hist_bar["low"], price, vol or 0.0)
        except Exception:  # noqa: BLE001 - optional feed
            pass
        signals = system.detect_predators() or []
        return {"signals": [_payload(s) for s in signals[:5]],
                "count": len(signals)}

    return AdvisoryModuleAdapter("alpha_research_predator_defense", analyze)


def _alpha_research_footprint_service() -> AdvisoryModuleAdapter:
    """alpha_research market-impact predator read: footprint + stop-hunt."""
    from trading_bot.alpha_research.market_impact_predator import (
        InstitutionalFootprintAnalyzer, StopHuntPredictor)

    footprint = InstitutionalFootprintAnalyzer()
    stop_hunt = StopHuntPredictor()

    def analyze(ctx: Mapping[str, Any]) -> Any:
        symbol = str(ctx.get("symbol") or "UNKNOWN")
        return {
            "footprint": _payload(footprint.analyze(symbol)),
            "stop_hunt": _payload(stop_hunt.predict(symbol)),
        }

    return AdvisoryModuleAdapter("alpha_research_footprint", analyze)


def _institutional_selection_service() -> AdvisoryModuleAdapter:
    """alphaalgo_institutional layer-1 analyzers on a MarketCharacteristics
    synthesized from the observation's real liquidity/quality fields."""
    from trading_bot.alphaalgo_institutional.core_types import MarketType
    from trading_bot.alphaalgo_institutional.layer1_market_selection import (
        InefficiencyAnalyzer, LiquidityAnalyzer, MarketCharacteristics,
        StructuralAnalyzer)

    analyzers = {"liquidity": LiquidityAnalyzer(),
                 "inefficiency": InefficiencyAnalyzer(),
                 "structural": StructuralAnalyzer()}

    def analyze(ctx: Mapping[str, Any]) -> Any:
        ch = MarketCharacteristics(
            market_type=MarketType.FX,
            avg_daily_volume=_num(ctx.get("volume")) or 0.0,
            bid_ask_spread_bps=(
                (_num(ctx.get("spread")) or 0.0)
                / max(_num(ctx.get("close") or ctx.get("price")) or 1.0,
                      1e-9)) * 1e4,
            volume_stability=1.0 - min(
                abs((_num(ctx.get("volume_ratio")) or 1.0) - 1.0), 1.0),
            data_completeness=_num(ctx.get("data_quality")) or 0.0,
        )
        return {name: _payload(a.analyze(ch))
                for name, a in analyzers.items()}

    return AdvisoryModuleAdapter("institutional_market_selection", analyze)


def _brain_technical_service() -> AdvisoryModuleAdapter:
    """brain tier-1 momentum + volatility analysis over accumulated bars."""
    from trading_bot.brain.tier1_technical import (
        MomentumAnalysis, VolatilityAnalysis)

    momentum, vol = MomentumAnalysis(), VolatilityAnalysis()
    hist = _BarHistory()

    def analyze(ctx: Mapping[str, Any]) -> Any:
        n = hist.add(ctx)
        if len(hist) < 40:
            return {"status": "warming", "bars": n}
        df = hist.frame()
        out = {"momentum": _payload(momentum.analyze(df)),
               "volatility": _payload(vol.analyze(df))}
        sig = _num((out["momentum"] or {}).get("momentum_signal"))
        if sig is not None:
            out["direction"] = "BUY" if sig > 0.2 else (
                "SELL" if sig < -0.2 else None)
            out["confidence"] = min(abs(sig), 1.0)
        return out

    return AdvisoryModuleAdapter("brain_technical_analysis", analyze)


def _brain_regime_service() -> AdvisoryModuleAdapter:
    """brain tier-4 regime + phase classifiers over accumulated bars."""
    from trading_bot.brain.tier4_regime import (
        MarketPhaseClassifier, VolatilityRegimeClassifier)

    vol_clf, phase_clf = VolatilityRegimeClassifier(), MarketPhaseClassifier()
    hist = _BarHistory()

    def analyze(ctx: Mapping[str, Any]) -> Any:
        n = hist.add(ctx)
        if len(hist) < 40:
            return {"status": "warming", "bars": n}
        df = hist.frame()
        return {"volatility_regime": _payload(vol_clf.classify(df)),
                "market_phase": _payload(phase_clf.classify(df))}

    return AdvisoryModuleAdapter("brain_regime_classification", analyze)


def _cognitive_regime_service() -> AdvisoryModuleAdapter:
    """cognitive_architecture layer-1 regime classifier + transition
    detector over accumulated real bars."""
    from trading_bot.cognitive_architecture.layer1_market_state_detection import (  # noqa: E501
        RegimeClassifier, TransitionDetector)

    clf, transitions = RegimeClassifier(), TransitionDetector()
    hist = _BarHistory()

    def analyze(ctx: Mapping[str, Any]) -> Any:
        n = hist.add(ctx)
        if len(hist) < 40:
            return {"status": "warming", "bars": n}
        df = hist.frame()
        out = {"regime": _payload(clf.classify(df, None))}
        try:
            out["transition"] = _payload(transitions.detect(
                _numeric_fields(ctx), df))
        except Exception:  # noqa: BLE001 - optional second opinion
            out["transition"] = None
        return out

    return AdvisoryModuleAdapter("cognitive_architecture_regime", analyze)


def _cognitive_perf_service() -> AdvisoryModuleAdapter:
    """cognitive_architecture layer-7 PerformanceEvaluator on the
    observation's numeric fields (evidence-only self-evaluation)."""
    from trading_bot.cognitive_architecture.layer7_self_healing import (
        PerformanceEvaluator)

    evaluator = PerformanceEvaluator()

    def analyze(ctx: Mapping[str, Any]) -> Any:
        return _payload(evaluator.evaluate(_numeric_fields(ctx)))

    return AdvisoryModuleAdapter("cognitive_performance_eval", analyze)


def _elite_factor_service() -> AdvisoryModuleAdapter:
    """elite_ai_system multi-factor confirmation evaluated on BOTH
    directions — asymmetry is the advisory signal."""
    from trading_bot.elite_ai_system.multi_factor_matrix import (
        MultiFactorConfirmationMatrix)

    matrix = MultiFactorConfirmationMatrix()

    def analyze(ctx: Mapping[str, Any]) -> Any:
        symbol = str(ctx.get("symbol") or "UNKNOWN")
        market = dict(ctx)
        out = {}
        for label, direction in (("long", "LONG"), ("short", "SHORT")):
            res = matrix.evaluate(symbol, direction, market, dict(ctx))
            p = _payload(res)
            out[label] = p
        def _score(p):
            for k in ("overall_score", "total_score", "score",
                      "confirmation_score", "weighted_score"):
                v = _num((p or {}).get(k)) if isinstance(p, Mapping) else None
                if v is not None:
                    return v
            return None
        ls, ss = _score(out["long"]), _score(out["short"])
        direction = None
        if ls is not None and ss is not None and abs(ls - ss) > 0.05:
            direction = "BUY" if ls > ss else "SELL"
        out["direction"] = direction
        return out

    return AdvisoryModuleAdapter("elite_factor_matrix", analyze)


def _adaptive_regime_service() -> AdvisoryModuleAdapter:
    """adaptive_systems MarketRegimeDetector over accumulated bars."""
    from trading_bot.adaptive_systems.market_regime import (
        MarketRegimeDetector)

    detector = MarketRegimeDetector()
    hist = _BarHistory()

    def analyze(ctx: Mapping[str, Any]) -> Any:
        n = hist.add(ctx)
        if len(hist) < 40:
            return {"status": "warming", "bars": n}
        signal = detector.detect_regime(hist.frame())
        out = _payload(signal)
        regime = str(out.get("regime") or out.get("regime_type") or ""
                       ).lower()
        if "bull" in regime or regime.endswith("up"):
            out["direction"] = "BUY"
        elif "bear" in regime or regime.endswith("down"):
            out["direction"] = "SELL"
        return out

    return AdvisoryModuleAdapter("adaptive_market_regime", analyze)


def _adaptive_learning_service() -> AdvisoryModuleAdapter:
    """adaptive_systems AdaptiveLearningEngine.predict — returns None
    until a model is trained; evidence-only."""
    from trading_bot.adaptive_systems.adaptive_learning import (
        AdaptiveLearningEngine, ModelType)

    engine = AdaptiveLearningEngine()

    def analyze(ctx: Mapping[str, Any]) -> Any:
        preds = {}
        for mt in ModelType:
            try:
                preds[mt.value] = engine.predict(mt, _feature_vector(ctx))
            except Exception:  # noqa: BLE001 - per-model failures skip
                preds[mt.value] = None
        return {"predictions": preds}

    return AdvisoryModuleAdapter("adaptive_learning_predict", analyze)


def _intelligence_strategy_service() -> AdvisoryModuleAdapter:
    """intelligence SelfLearningEngine — best-known strategy per
    (symbol, regime) from its own journal DB; evidence-only."""
    from trading_bot.intelligence.self_learning_engine import (
        SelfLearningEngine)

    engine = SelfLearningEngine()

    def analyze(ctx: Mapping[str, Any]) -> Any:
        symbol = str(ctx.get("symbol") or "UNKNOWN")
        regime = str(ctx.get("trend") or ctx.get("regime") or "FLAT")
        try:
            best = engine.get_best_strategy(symbol, regime)
        except Exception:  # noqa: BLE001 - db may be empty
            best = None
        try:
            insights = [str(i) for i in (engine.analyze() or [])][:5]
        except Exception:  # noqa: BLE001
            insights = []
        return {"best_strategy": _primitive(best), "insights": insights}

    return AdvisoryModuleAdapter("intelligence_strategy_stats", analyze)


def _self_learning_ensemble_service() -> AdvisoryModuleAdapter:
    """self_learning EnsembleLearner.predict on the canonical feature
    vector — untrained models predict zeros; evidence-only."""
    from trading_bot.self_learning.core_learning_engine import (
        EnsembleLearner, ModelType)

    ensemble = EnsembleLearner()
    try:
        ensemble.initialize(ModelType.PRICE_DIRECTION)
    except Exception:  # noqa: BLE001 - predict tolerates uninitialized
        pass

    def analyze(ctx: Mapping[str, Any]) -> Any:
        out = ensemble.predict(np.asarray([_feature_vector(ctx)]))
        if isinstance(out, tuple):
            preds, conf = out
        else:
            preds, conf = out, None
        # Evidence-only: untrained models return zeros, and a zero vector
        # must not be misread as a directional call — no direction field.
        return {"predictions": _primitive(
                    list(preds) if hasattr(preds, "__iter__") else preds),
                "confidence": _num(conf)}

    return AdvisoryModuleAdapter("self_learning_ensemble", analyze)


def _signal_regime_change_service() -> AdvisoryModuleAdapter:
    """signal_discovery RegimeChangeDetector over accumulated closes."""
    from trading_bot.signal_discovery.anomaly_detection.regime_change import (  # noqa: E501
        RegimeChangeDetector)

    detector = RegimeChangeDetector()
    hist = _BarHistory()

    def analyze(ctx: Mapping[str, Any]) -> Any:
        n = hist.add(ctx)
        if len(hist) < 20:
            return {"status": "warming", "bars": n}
        changes = detector.detect(hist.prices(), hist.volumes()) or []
        return {"regime_changes": [_payload(c) for c in changes[:5]],
                "count": len(changes),
                "current_regime": _primitive(
                    detector.get_current_regime(hist.prices()))}

    return AdvisoryModuleAdapter("signal_regime_change", analyze)


def _signal_outlier_service() -> AdvisoryModuleAdapter:
    """signal_discovery StatisticalOutlierDetector over accumulated
    closes — flags the tail of the real price window."""
    from trading_bot.signal_discovery.anomaly_detection.statistical_outliers import (  # noqa: E501
        StatisticalOutlierDetector)

    detector = StatisticalOutlierDetector()
    hist = _BarHistory()

    def analyze(ctx: Mapping[str, Any]) -> Any:
        n = hist.add(ctx)
        if len(hist) < 20:
            return {"status": "warming", "bars": n}
        outs = detector.detect(hist.prices()) or []
        return {"outliers": [_primitive(o) for o in outs[:10]],
                "count": len(outs)}

    return AdvisoryModuleAdapter("signal_statistical_outliers", analyze)


def _tamic_market_time_service() -> AdvisoryModuleAdapter:
    """tamic MarketTimeEngine — registers real obs baselines and reports
    active market-time acceleration events for the symbol."""
    from trading_bot.tamic.market_time import MarketTimeEngine

    engine = MarketTimeEngine()

    def analyze(ctx: Mapping[str, Any]) -> Any:
        symbol = str(ctx.get("symbol") or "UNKNOWN")
        for metric in ("price", "volatility", "volume"):
            v = _num(ctx.get(metric) or ctx.get("close")
                     if metric == "price" else ctx.get(metric))
            if v is not None:
                try:
                    engine.register_baseline(symbol, metric, v)
                except Exception:  # noqa: BLE001
                    pass
        try:
            events = engine.get_active_events(symbol) or []
        except Exception:  # noqa: BLE001
            events = []
        return {"active_events": [_payload(e) for e in events[:5]],
                "count": len(events)}

    return AdvisoryModuleAdapter("tamic_market_time", analyze)


def _self_diagnostic_service() -> AdvisoryModuleAdapter:
    """self_diagnostic ComprehensiveDiagnosticSuite health score —
    evidence-only system-health read alongside the market obs."""
    from trading_bot.self_diagnostic.comprehensive_diagnostics import (
        ComprehensiveDiagnosticSuite)

    suite = ComprehensiveDiagnosticSuite()

    def analyze(ctx: Mapping[str, Any]) -> Any:
        return {"health_score": _primitive(suite.get_health_score())}

    return AdvisoryModuleAdapter("self_diagnostic_health", analyze)


def _aletheia_audit_service() -> AdvisoryModuleAdapter:
    """aletheia_autonomous decision auditor — audits the observation
    framed as a hypothetical paper-stage proposal (never approved)."""
    from trading_bot.aletheia_autonomous.financial_decision_auditor import (  # noqa: E501
        AletheiaFinancialDecisionAuditor)

    auditor = AletheiaFinancialDecisionAuditor()

    def analyze(ctx: Mapping[str, Any]) -> Any:
        proposal = {
            "symbol": str(ctx.get("symbol") or "UNKNOWN"),
            "action": "observe",
            "price": _num(ctx.get("close") or ctx.get("price")),
            "metrics": _numeric_fields(ctx),
        }
        audit = auditor.audit_decision(proposal, target_stage="paper")
        return _payload(audit)

    return AdvisoryModuleAdapter("aletheia_decision_audit", analyze)


def _superintel_regime_service() -> AdvisoryModuleAdapter:
    """superintelligence RegimeStrategyEngine.analyze_and_activate over
    accumulated real closes — regime + strategy-fit evidence."""
    import pandas as pd
    from trading_bot.superintelligence.regime_strategy_engine import (
        RegimeStrategyEngine)

    engine = RegimeStrategyEngine()
    hist = _BarHistory()

    def analyze(ctx: Mapping[str, Any]) -> Any:
        n = hist.add(ctx)
        if len(hist) < 30:
            return {"status": "warming", "bars": n}
        prices = pd.Series(hist.prices())
        volumes = pd.Series(hist.volumes())
        chars, activation = engine.analyze_and_activate(prices, volumes)
        regime = str(getattr(getattr(chars, "regime", None), "value",
                             getattr(chars, "regime", "")))
        out = {"regime": _payload(chars), "activation": _payload(activation)}
        rl = regime.lower()
        if "bull" in rl or "up" in rl:
            out["direction"] = "BUY"
        elif "bear" in rl or "down" in rl:
            out["direction"] = "SELL"
        return out

    return AdvisoryModuleAdapter("superintelligence_regime_strategy",
                                 analyze)


def _systems_stress_service() -> AdvisoryModuleAdapter:
    """systems_ai SyntheticStressSimulator — stresses a naive buy-and-hold
    return stream built from accumulated real closes."""
    from trading_bot.systems_ai.advanced_features import (
        StressScenario, SyntheticStressSimulator)

    sim = SyntheticStressSimulator()
    hist = _BarHistory()

    def _buy_hold(prices, volumes):
        return [prices[i] / prices[i - 1] - 1.0
                for i in range(1, len(prices)) if prices[i - 1]]

    def analyze(ctx: Mapping[str, Any]) -> Any:
        n = hist.add(ctx)
        if len(hist) < 30:
            return {"status": "warming", "bars": n}
        results = {}
        for scenario in (StressScenario.VOLATILITY_SPIKE,
                         StressScenario.FLASH_CRASH):
            try:
                res = sim.run_stress_test(
                    scenario, hist.prices(), hist.volumes(), _buy_hold)
                results[scenario.value] = _payload(res)
            except Exception as exc:  # noqa: BLE001
                results[scenario.value] = {"error": str(exc)}
        return results

    return AdvisoryModuleAdapter("systems_ai_stress_test", analyze)


# ---------------------------------------------------------------------------
# Bucket B — additional capabilities from partially-wired packages
# ---------------------------------------------------------------------------


def _make_legacy_agent_service(capability_id: str, cls_name: str
                               ) -> Callable[[], AdvisoryModuleAdapter]:
    """core_agent_system legacy agents share analyze_market(dict) ->
    AgentProposal; bind one factory per agent class."""
    def factory() -> AdvisoryModuleAdapter:
        from trading_bot.core_agent_system.migrated_agents import (
            legacy_agents)
        agent = getattr(legacy_agents, cls_name)()

        def analyze(ctx: Mapping[str, Any]) -> Any:
            return _payload(agent.analyze_market(dict(ctx)))

        return AdvisoryModuleAdapter(capability_id, analyze)
    return factory


def _make_agents2_service(capability_id: str, cls_name: str
                          ) -> Callable[[], AdvisoryModuleAdapter]:
    """agents2 specialized agents expose the same analyze_market(dict)
    surface under their own base_agent — wire as distinct capabilities."""
    def factory() -> AdvisoryModuleAdapter:
        from trading_bot.agents2 import specialized_agents
        agent = getattr(specialized_agents, cls_name)()

        def analyze(ctx: Mapping[str, Any]) -> Any:
            return _payload(agent.analyze_market(dict(ctx)))

        return AdvisoryModuleAdapter(capability_id, analyze)
    return factory


def _make_failure_detector_service(capability_id: str, cls_name: str
                                   ) -> Callable[[], AdvisoryModuleAdapter]:
    """intelligence_core detectors share detect(current_state,
    historical_states) — feed the obs plus a rolling history window."""
    def factory() -> AdvisoryModuleAdapter:
        from trading_bot.intelligence_core import failure_detector
        detector = getattr(failure_detector, cls_name)()
        history: "collections.deque" = collections.deque(maxlen=50)

        def analyze(ctx: Mapping[str, Any]) -> Any:
            state = dict(ctx)
            history.append(state)
            outs = detector.detect(state, list(history)) or []
            return {"detections": [_payload(o) for o in outs[:5]],
                    "count": len(outs)}

        return AdvisoryModuleAdapter(capability_id, analyze)
    return factory


def _make_anomaly_classifier_service(
        capability_id: str, module: str, cls_name: str
        ) -> Callable[[], AdvisoryModuleAdapter]:
    """market_intelligence Layer-2 classifiers consume MarketAnomaly —
    synthesize one honestly from the observation's real fields."""
    def factory() -> AdvisoryModuleAdapter:
        import importlib
        from trading_bot.signal_discovery.agents.base_agent import (
            AnomalyType, DataSource, MarketAnomaly)
        classifier = getattr(importlib.import_module(module), cls_name)()

        def analyze(ctx: Mapping[str, Any]) -> Any:
            symbol = str(ctx.get("symbol") or "UNKNOWN")
            desc = " ".join(
                f"{k}={v}" for k, v in sorted(ctx.items())
                if isinstance(v, (int, float, str)))[:400]
            anomaly = MarketAnomaly(
                agent_id="csc_advisory", agent_type="observation",
                data_source=DataSource.TRADINGVIEW,
                anomaly_type=AnomalyType.STATISTICAL_OUTLIER,
                confidence=_num(ctx.get("trend_strength")) or 0.5,
                primary_asset=symbol, raw_data=dict(ctx),
                description=f"{symbol} market observation: {desc}",
                detection_method="csc_observation",
                statistical_significance=_num(
                    ctx.get("volatility")) or 0.0)
            res = classifier.classify(anomaly)
            return {"classification": _payload(res)}

        return AdvisoryModuleAdapter(capability_id, analyze)
    return factory


def _make_debate_agent_service(capability_id: str, cls_name: str
                               ) -> Callable[[], AdvisoryModuleAdapter]:
    """Individual multi_agent_debate agents take the typed MarketContext
    — the same builder the debate service uses."""
    def factory() -> AdvisoryModuleAdapter:
        from trading_bot.agents import multi_agent_debate
        agent = getattr(multi_agent_debate, cls_name)()

        def analyze(ctx: Mapping[str, Any]) -> Any:
            return _payload(agent.analyze(_market_context(ctx)))

        return AdvisoryModuleAdapter(capability_id, analyze)
    return factory


def _adversarial_failure_match_service() -> AdvisoryModuleAdapter:
    """adversarial_decision FailureMatcher — current conditions vs the
    recorded failure-mode database; evidence-only."""
    from trading_bot.adversarial_decision.failure_matcher import (
        FailureMatcher)

    matcher = FailureMatcher()

    def analyze(ctx: Mapping[str, Any]) -> Any:
        return _payload(matcher.check_failure_match(
            market_data=dict(ctx), signal_data=dict(ctx),
            portfolio_state={}, historical_data={}))

    return AdvisoryModuleAdapter("adversarial_failure_match", analyze)


def _alphaalgo_perf_sensor_service() -> AdvisoryModuleAdapter:
    """alphaalgo_core MultiMetricPerformanceSensor — records the realized
    per-observation return under the obs's regime label, then reports
    computed metrics once the window fills."""
    from trading_bot.alphaalgo_core.alphaalgo_core import (
        MultiMetricPerformanceSensor, RegimeLabel)

    sensor = MultiMetricPerformanceSensor()
    hist = _BarHistory()
    _REGIME = {"UP": RegimeLabel.TRENDING_BULL,
               "BULLISH": RegimeLabel.TRENDING_BULL,
               "DOWN": RegimeLabel.TRENDING_BEAR,
               "BEARISH": RegimeLabel.TRENDING_BEAR}

    def analyze(ctx: Mapping[str, Any]) -> Any:
        hist.add(ctx)
        rets = hist.returns()
        if rets:
            label = _REGIME.get(
                str(ctx.get("trend") or "").upper(), RegimeLabel.RANGING)
            try:
                sensor.record_return(rets[-1], label)
            except Exception:  # noqa: BLE001 - optional feed
                pass
        return _payload(sensor.compute_metrics())

    return AdvisoryModuleAdapter("alphaalgo_performance_sensor", analyze)


def _market_physics_service() -> AdvisoryModuleAdapter:
    """alphaalgo_core MarketPhysicsFilter — structural tradability read
    on a market_data dict synthesized from the observation."""
    from trading_bot.alphaalgo_core.market_physics_filter import (
        MarketPhysicsFilter)

    filt = MarketPhysicsFilter()
    hist = _BarHistory()

    async def analyze(ctx: Mapping[str, Any]) -> Any:
        hist.add(ctx)
        bars = hist.bars(20)
        market_data = {
            "ohlcv": bars,
            "orderbook": {},
            "trades": [],
            "liquidity": {"volume": _num(ctx.get("volume")) or 0.0},
            "volatility": {"value": _num(ctx.get("volatility")) or 0.0},
            "microstructure": {
                "spread": _num(ctx.get("spread")) or 0.0,
                "volume_ratio": _num(ctx.get("volume_ratio")) or 1.0,
            },
        }
        out = filt.process(
            str(ctx.get("symbol") or "UNKNOWN"), market_data)
        if inspect.isawaitable(out):
            out = await out
        return _payload(out)

    return AdvisoryModuleAdapter("market_physics_filter", analyze)


# ---------------------------------------------------------------------------
# Bucket C — loose orphan root files
# ---------------------------------------------------------------------------


def _alphaalgo_5star_risk_service() -> AdvisoryModuleAdapter:
    """alphaalgo_5star.calculate_risk_metrics over realized returns —
    lazy ctor leaves torch models un-initialized; only the numpy risk
    path is exercised."""
    import numpy as _np
    import trading_bot.alphaalgo_5star as _a5

    # Module calls loguru-style logger.success() on a stdlib logger;
    # shim it so construction succeeds.
    _log = getattr(_a5, "logger", None)
    if _log is not None and not hasattr(_log, "success"):
        _log.success = _log.info
    from trading_bot.alphaalgo_5star import AlphaAlgo5Star

    system = AlphaAlgo5Star({})
    hist = _BarHistory()

    def analyze(ctx: Mapping[str, Any]) -> Any:
        hist.add(ctx)
        rets = hist.returns()
        if len(rets) < 10:
            return {"status": "warming", "bars": len(hist)}
        return _payload(system.calculate_risk_metrics(
            _np.asarray(rets, dtype=float)))

    return AdvisoryModuleAdapter("alphaalgo_5star_risk_metrics", analyze)


def _world2agent_bridge_service() -> AdvisoryModuleAdapter:
    """world2agent bridge — publishes the observation as a world-state
    snapshot on a private bus and reports the enriched agent context;
    evidence-only provenance wiring."""
    from trading_bot.a2a import A2AMessageBus
    from trading_bot.world2agent import World2AgentBridge

    bridge = World2AgentBridge(A2AMessageBus())

    def analyze(ctx: Mapping[str, Any]) -> Any:
        snapshot = bridge.publish_world_state(
            source="csc_advisory", world_state=dict(ctx))
        enriched = bridge.build_agent_context(
            "csc", base_payload={"symbol": ctx.get("symbol")})
        return {"snapshot": _payload(snapshot),
                "context": _payload(enriched)}

    return AdvisoryModuleAdapter("world2agent_bridge", analyze)


# without writing a stub subclass.

# ---------------------------------------------------------------------------
# Bucket A2 — second-pass wiring: the remaining orphan packages and the
# additional capabilities audit found obs-callable. Same conventions:
# _BarHistory accumulates real bars ({"status": "warming"} until full),
# _payload normalizes returns, every factory is probe-gated.
# ---------------------------------------------------------------------------


def _enum_direction(value: Any) -> Optional[str]:
    """Map an enum-or-string market label to BUY/SELL/None."""
    s = str(getattr(value, "value", value) or "").upper()
    if s in _DIRECTION_MAP:
        return _DIRECTION_MAP[s]
    if any(k in s for k in ("BULL", "UPTREND", "LONG", "UP")):
        return "BUY"
    if any(k in s for k in ("BEAR", "DOWNTREND", "SHORT", "DOWN")):
        return "SELL"
    return None


def _moe_router_service() -> AdvisoryModuleAdapter:
    """advanced_intelligence MixtureOfExpertsRouter — action probability
    distribution on the canonical feature vector (numpy-only path; the
    deep-model remainder of the package stays tensor-bound)."""
    from trading_bot.advanced_intelligence.advanced_ai_ml.\
        mixture_of_experts import MixtureOfExpertsRouter

    router = MixtureOfExpertsRouter()

    async def analyze(ctx: Mapping[str, Any]) -> Any:
        feats = np.asarray(_feature_vector(ctx)[:4], dtype=float)
        out = router.predict(feats)
        regime = router.detect_regime(feats)
        if inspect.isawaitable(out):
            out = await out
        if inspect.isawaitable(regime):
            regime = await regime
        payload = _payload(out)
        payload["regime"] = str(regime)
        return payload

    return AdvisoryModuleAdapter("mixture_of_experts", analyze)


def _microstructure_service() -> AdvisoryModuleAdapter:
    """adaptive_systems MarketMicrostructureAnalyzer over real bars."""
    from trading_bot.adaptive_systems.market_microstructure import (
        MarketMicrostructureAnalyzer)

    analyzer = MarketMicrostructureAnalyzer()
    hist = _BarHistory()

    def analyze(ctx: Mapping[str, Any]) -> Any:
        n = hist.add(ctx)
        if len(hist) < 40:
            return {"status": "warming", "bars": n}
        df = hist.frame()
        df["price"] = df["close"]
        signals = analyzer.analyze_microstructure(df) or []
        inst = analyzer.detect_institutional_activity(df) or []
        return {"signals": [_payload(s) for s in signals[:5]],
                "institutional": [_payload(s) for s in inst[:5]]}

    return AdvisoryModuleAdapter("market_microstructure", analyze)


def _economy_agent_service(
        capability_id: str, agent_name: str
        ) -> Callable[[], AdvisoryModuleAdapter]:
    """cognitive_architecture layer-3 economy agents share
    analyze(dict) -> AgentDecision."""
    def factory() -> AdvisoryModuleAdapter:
        from trading_bot.cognitive_architecture import (
            layer3_cognitive_economy as econ)
        agent = getattr(econ, agent_name)()

        def analyze(ctx: Mapping[str, Any]) -> Any:
            # Agents read fixed typed keys; coerce from the observation
            # where present, honest defaults otherwise.
            sig = ctx.get("signal")
            data = {
                "data_quality": _num(ctx.get("data_quality")) or 0.8,
                "signal": dict(sig) if isinstance(sig, Mapping) else {
                    "direction": str(ctx.get("direction") or "hold"),
                    "confidence": _num(ctx.get("confidence")) or 0.5},
                "risk_score": (_num(ctx.get("risk_score"))
                               or _num(ctx.get("volatility")) or 0.5),
                "position_size": _num(ctx.get("position_size")) or 0.0,
                "pattern_confidence": (
                    _num(ctx.get("pattern_confidence"))
                    or _num(ctx.get("trend_strength")) or 0.5),
                "system_health": _num(ctx.get("system_health")) or 1.0,
            }
            return _payload(agent.analyze(data))

        return AdvisoryModuleAdapter(capability_id, analyze)
    return factory


def _regime_transition_service() -> AdvisoryModuleAdapter:
    """cognitive_architecture CUSUM change-point detector on real closes."""
    from trading_bot.cognitive_architecture.\
        layer1_market_state_detection import TransitionDetector

    detector = TransitionDetector()
    hist = _BarHistory()

    def analyze(ctx: Mapping[str, Any]) -> Any:
        n = hist.add(ctx)
        if len(hist) < 44:
            return {"status": "warming", "bars": n}
        import pandas as pd
        return {"change_point": bool(detector.detect_change_point(
            pd.Series(hist.prices())))}

    return AdvisoryModuleAdapter("regime_transition_detector", analyze)


def _market_psychology_service() -> AdvisoryModuleAdapter:
    """elite_ai_system MarketPsychologyEngine — crowd-psychology state;
    only a clear |sentiment|>0.2 expresses a direction."""
    from trading_bot.elite_ai_system.market_psychology_engine import (
        MarketPsychologyEngine)

    engine = MarketPsychologyEngine()

    async def analyze(ctx: Mapping[str, Any]) -> Any:
        state = engine.analyze_psychology(dict(ctx))
        if inspect.isawaitable(state):
            state = await state
        s = _num(getattr(getattr(state, "sentiment", None),
                         "overall_sentiment", None)) or 0.0
        out = _payload(state)
        out["direction"] = ("BUY" if s > 0.2 else
                            "SELL" if s < -0.2 else None)
        out["confidence"] = min(abs(s), 1.0) or None
        return out

    return AdvisoryModuleAdapter("market_psychology", analyze)


def _improvement_findings_service() -> AdvisoryModuleAdapter:
    """improvement_agent analyzer — its findings on the obs dict are
    honest (usually empty on non-code input); evidence-only."""
    from trading_bot.improvement_agent.agent_orchestrator import (
        ImprovementAgent)

    agent = ImprovementAgent()

    async def analyze(ctx: Mapping[str, Any]) -> Any:
        return _payload(await agent.analyze(dict(ctx)))

    return AdvisoryModuleAdapter("improvement_findings", analyze)


def _neural_hub_service() -> AdvisoryModuleAdapter:
    """neural_integration hub — topology report is the honest callable
    surface (no modules register off the canonical path)."""
    from trading_bot.neural_integration.neural_hub import (
        NeuralIntegrationHub)

    hub = NeuralIntegrationHub()

    def analyze(ctx: Mapping[str, Any]) -> Any:
        return _payload(hub.get_neural_topology())

    return AdvisoryModuleAdapter("neural_hub_topology", analyze)


def _hivemind_analyst_service() -> AdvisoryModuleAdapter:
    """radar_ai MarketAnalystAgent — async swarm analyst on the obs."""
    from trading_bot.radar_ai.hivemind_controller import (
        MarketAnalystAgent)

    agent = MarketAnalystAgent()

    async def analyze(ctx: Mapping[str, Any]) -> Any:
        d = await agent.analyze(dict(ctx))
        out = _payload(d)
        for key in ("action", "decision", "recommendation", "signal"):
            direction = _enum_direction(out.get(key))
            if direction:
                out["direction"] = direction
                break
        return out

    return AdvisoryModuleAdapter("hivemind_analyst", analyze)


def _radar_regime_service() -> AdvisoryModuleAdapter:
    """radar_ai understanding_engine RegimeDetector over real bars."""
    from trading_bot.radar_ai.understanding_engine import RegimeDetector

    detector = RegimeDetector()
    hist = _BarHistory()

    async def analyze(ctx: Mapping[str, Any]) -> Any:
        n = hist.add(ctx)
        if len(hist) < 30:
            return {"status": "warming", "bars": n}
        r = await detector.detect_regime(hist.frame())
        out = _payload(r)
        regime = getattr(r, "current_regime", getattr(r, "regime", None))
        out["direction"] = _enum_direction(regime)
        return out

    return AdvisoryModuleAdapter("radar_regime", analyze)


def _self_concept_service() -> AdvisoryModuleAdapter:
    """self_concepts engine — pre-trade concept pass over the obs."""
    from trading_bot.self_concepts.self_concept_engine import (
        SelfConceptEngine)

    engine = SelfConceptEngine()

    def analyze(ctx: Mapping[str, Any]) -> Any:
        return _payload(engine.pre_trade_process(dict(ctx)))

    return AdvisoryModuleAdapter("self_concept_guard", analyze)


def _self_healing_health_service() -> AdvisoryModuleAdapter:
    """self_healing_ai orchestrator — system health evidence."""
    from trading_bot.self_healing_ai.orchestrator import (
        SelfHealingOrchestrator)

    orch = SelfHealingOrchestrator()

    def analyze(ctx: Mapping[str, Any]) -> Any:
        h = orch.get_system_health()
        return {"health": str(getattr(h, "value", h))}

    return AdvisoryModuleAdapter("system_health", analyze)


def _self_learning_health_service() -> AdvisoryModuleAdapter:
    """self_learning SelfHealingSystem — issue-detection health dict."""
    from trading_bot.self_learning.self_healing_system import (
        SelfHealingSystem)

    system = SelfHealingSystem()

    def analyze(ctx: Mapping[str, Any]) -> Any:
        return _payload(system.get_system_health())

    return AdvisoryModuleAdapter("self_learning_health", analyze)


def _mastery_reflection_service() -> AdvisoryModuleAdapter:
    """self_mastery MasteryOrchestrator.reflect — self-review insights
    (empty until trades are recorded; honest evidence)."""
    from trading_bot.self_mastery.mastery_orchestrator import (
        MasteryOrchestrator)

    orch = MasteryOrchestrator()

    def analyze(ctx: Mapping[str, Any]) -> Any:
        insights = orch.reflect() or []
        return {"insights": [_payload(i) for i in insights[:5]],
                "count": len(insights)}

    return AdvisoryModuleAdapter("mastery_reflection", analyze)


def _introspection_service() -> AdvisoryModuleAdapter:
    """sentient_core Introspector — code health score evidence."""
    from trading_bot.sentient_core.introspector import Introspector

    intro = Introspector()

    def analyze(ctx: Mapping[str, Any]) -> Any:
        return {"code_health_score": _primitive(
            intro.get_code_health_score())}

    return AdvisoryModuleAdapter("codebase_introspection", analyze)


def _regime_memory_service() -> AdvisoryModuleAdapter:
    """superintelligence MemorySystem — lessons for the current regime."""
    from trading_bot.superintelligence.memory_systems import MemorySystem

    memory = MemorySystem()

    def analyze(ctx: Mapping[str, Any]) -> Any:
        regime = str(ctx.get("trend") or ctx.get("regime") or "unknown")
        lessons = memory.recall_lessons_for_regime(regime) or []
        return {"regime": regime,
                "lessons": [_payload(l) for l in lessons[:5]],
                "count": len(lessons)}

    return AdvisoryModuleAdapter("regime_memory", analyze)


def _trend_reversal_service() -> AdvisoryModuleAdapter:
    """superpowerful_ai PredictiveIntelligence — reversal probability
    over accumulated real bars."""
    from trading_bot.superpowerful_ai.predictive_intelligence import (
        PredictiveIntelligence)

    intel = PredictiveIntelligence()
    hist = _BarHistory()

    async def analyze(ctx: Mapping[str, Any]) -> Any:
        n = hist.add(ctx)
        if len(hist) < 40:
            return {"status": "warming", "bars": n}
        p = await intel.predict_trend_reversal(
            hist.frame(), str(ctx.get("symbol") or "UNKNOWN"))
        return _payload(p)

    return AdvisoryModuleAdapter("trend_reversal", analyze)


def _regime_discovery_service() -> AdvisoryModuleAdapter:
    """superpowerful_ai SelfDiscoveryEngine — unsupervised regime +
    anomaly pass over accumulated real bars."""
    from trading_bot.superpowerful_ai.self_discovery_engine import (
        SelfDiscoveryEngine)

    engine = SelfDiscoveryEngine()
    hist = _BarHistory()

    async def analyze(ctx: Mapping[str, Any]) -> Any:
        n = hist.add(ctx)
        if len(hist) < 40:
            return {"status": "warming", "bars": n}
        symbol = str(ctx.get("symbol") or "UNKNOWN")
        frame = hist.frame()
        state = await engine.detect_regime(frame, symbol)
        anomalies = await engine.detect_anomalies(frame, symbol)
        out = _payload(state)
        out["anomalies"] = _primitive(list(anomalies or [])[:5])
        regime = getattr(state, "regime", None)
        out["direction"] = _enum_direction(regime)
        return out

    return AdvisoryModuleAdapter("regime_discovery", analyze)


def _strategy_selector_service() -> AdvisoryModuleAdapter:
    """superpowerful_ai StrategicIntelligence — strategy selection on
    the observation as market_state (evidence, never an order)."""
    from trading_bot.superpowerful_ai.strategic_intelligence import (
        StrategicIntelligence)

    intel = StrategicIntelligence()

    async def analyze(ctx: Mapping[str, Any]) -> Any:
        return _payload(await intel.select_optimal_strategy(dict(ctx)))

    return AdvisoryModuleAdapter("strategy_selector", analyze)


def _data_drift_service() -> AdvisoryModuleAdapter:
    """systems_ai DriftDetector — feature-distribution drift evidence
    (first calls establish the baseline; returns None => no drift)."""
    from trading_bot.systems_ai.self_improvement import DriftDetector

    detector = DriftDetector()

    def analyze(ctx: Mapping[str, Any]) -> Any:
        dists = {k: {"mean": v, "std": 0.0}
                 for k, v in _numeric_fields(ctx).items()}
        out = detector.detect_data_drift(dists)
        if out is None:
            return {"drift_detected": False}
        return {"drift_detected": True, "detail": _payload(out)}

    return AdvisoryModuleAdapter("data_drift", analyze)


def _performance_decay_service() -> AdvisoryModuleAdapter:
    """systems_ai PerformanceTracker — decay check on obs metrics."""
    from trading_bot.systems_ai.self_improvement import PerformanceTracker

    tracker = PerformanceTracker()

    def analyze(ctx: Mapping[str, Any]) -> Any:
        decayed, detail = tracker.detect_decay(_numeric_fields(ctx))
        return {"decay_detected": bool(decayed),
                "detail": _payload(detail)}

    return AdvisoryModuleAdapter("performance_decay", analyze)


def _signal_decay_service() -> AdvisoryModuleAdapter:
    """tamic SignalDecay — extracted-signal decay analysis on real bars."""
    from trading_bot.tamic.signal_decay import SignalDecay

    decay = SignalDecay()
    hist = _BarHistory()

    async def analyze(ctx: Mapping[str, Any]) -> Any:
        n = hist.add(ctx)
        if len(hist) < 40:
            return {"status": "warming", "bars": n}
        r = await decay.analyze_signals(
            str(ctx.get("symbol") or "UNKNOWN"),
            str(ctx.get("timeframe") or "M15"), hist.frame())
        return _payload(r)

    return AdvisoryModuleAdapter("signal_decay", analyze)


def _autonomous_tuner_service() -> AdvisoryModuleAdapter:
    """ai AutonomousTuner — tuner-state summary evidence (its hub is
    torch-bound; the tuner is not)."""
    from trading_bot.ai.autonomous_tuner import AutonomousTuner

    tuner = AutonomousTuner()

    def analyze(ctx: Mapping[str, Any]) -> Any:
        return _payload(tuner.get_tuning_summary())

    return AdvisoryModuleAdapter("autonomous_tuner", analyze)


def _planner_agent_service() -> AdvisoryModuleAdapter:
    """ai_core PlannerAgent — plan list on the obs dict."""
    from trading_bot.ai_core.agents.orchestrator import PlannerAgent

    agent = PlannerAgent()

    async def analyze(ctx: Mapping[str, Any]) -> Any:
        out = await agent.process(dict(ctx)) or []
        return {"plans": [_payload(o) for o in out[:5]],
                "count": len(out)}

    return AdvisoryModuleAdapter("planner_agent", analyze)


def _alpha_evolve_service() -> AdvisoryModuleAdapter:
    """aads AlphaEvolveEngine — evolved signal genome as evidence (the
    deploy/backtest surface is never invoked)."""
    from types import SimpleNamespace
    from trading_bot.aads.core.alpha_evolve_engine import (
        AlphaEvolveEngine)

    engine = AlphaEvolveEngine()

    def analyze(ctx: Mapping[str, Any]) -> Any:
        evo_ctx = SimpleNamespace(
            asset_class="fx", previous_best_code=None,
            previous_best_sharpe=0.0,
            regime=str(ctx.get("trend") or ctx.get("regime") or "unknown"),
            timeframe=str(ctx.get("timeframe") or "M15"),
            rejection_history=[])
        return _payload(engine.generate_signal(evo_ctx))

    return AdvisoryModuleAdapter("alpha_evolve_signal", analyze)


def _polymarket_service() -> AdvisoryModuleAdapter:
    """aads PolymarketModule — probability estimate on a contract
    synthesized from the obs; capital path untouched."""
    from types import SimpleNamespace
    from trading_bot.aads.core.polymarket import PolymarketModule

    module = PolymarketModule()

    def analyze(ctx: Mapping[str, Any]) -> Any:
        contract = SimpleNamespace(
            category="macro", confidence=0.5, contract_id="obs",
            edge=0.0, implied_probability=0.5, liquidity=10000.0,
            no_price=0.5, our_probability=None,
            question=f"{ctx.get('symbol') or 'EURUSD'} up next bar?",
            resolution_date=None, resolved_outcome=None, status="open",
            volume_=10000.0, yes_price=0.5)
        est = module.estimate_probability(contract, dict(ctx))
        trade = module.evaluate_trade(contract)
        out = _payload(est)
        if isinstance(trade, Mapping):
            out["edge"] = _primitive(trade.get("edge"))
            out["side"] = str(trade.get("side"))
        return out

    return AdvisoryModuleAdapter("polymarket_estimate", analyze)


def _maven_stats_service() -> AdvisoryModuleAdapter:
    """aads MavenDecisionEngine — wargame decision statistics evidence."""
    from trading_bot.aads.core.maven_decision import MavenDecisionEngine

    engine = MavenDecisionEngine()

    def analyze(ctx: Mapping[str, Any]) -> Any:
        return _payload(engine.get_statistics())

    return AdvisoryModuleAdapter("maven_stats", analyze)


def _aamis_service() -> AdvisoryModuleAdapter:
    """aamis_v3 master orchestrator — its (deliberately abstaining)
    consolidated report is real advisory evidence."""
    from trading_bot.aamis_v3.aamis_master_orchestrator import (
        AAMISMasterOrchestrator)

    orch = AAMISMasterOrchestrator()

    async def analyze(ctx: Mapping[str, Any]) -> Any:
        report = await orch.analyze_market(dict(ctx))
        out = _payload(report)
        decision = getattr(report, "decision", None)
        out["direction"] = _enum_direction(
            getattr(decision, "action", None))
        return out

    return AdvisoryModuleAdapter("aamis_market", analyze)


def _learner_knowledge_service() -> AdvisoryModuleAdapter:
    """autonomous_learner KnowledgeBuilder — curriculum summary evidence
    (module is deprecated for authority, not for evidence)."""
    from trading_bot.autonomous_learner.knowledge_builder import (
        KnowledgeBuilder)

    builder = KnowledgeBuilder()

    def analyze(ctx: Mapping[str, Any]) -> Any:
        return _payload(builder.get_knowledge_summary())

    return AdvisoryModuleAdapter("learner_knowledge", analyze)


def _decision_explainer_service() -> AdvisoryModuleAdapter:
    """explainability TradingExplainer — NL read on the obs framed as a
    hypothetical decision (evidence text, never a directive)."""
    from trading_bot.explainability import TradingExplainer

    explainer = TradingExplainer()

    def analyze(ctx: Mapping[str, Any]) -> Any:
        return {"explanation": str(
            explainer.explain_decision(dict(ctx)))[:400]}

    return AdvisoryModuleAdapter("decision_explainer", analyze)


def _alpha_weakness_service() -> AdvisoryModuleAdapter:
    """alpha_research VolatilityRegimeDetector — |returns| history vs
    current volatility; weakness-severity evidence."""
    from trading_bot.alpha_research.weakness_detection import (
        VolatilityRegimeDetector)

    detector = VolatilityRegimeDetector()
    hist = _BarHistory()

    def analyze(ctx: Mapping[str, Any]) -> Any:
        n = hist.add(ctx)
        if len(hist) < 12:
            return {"status": "warming", "bars": n}
        vol_hist = [abs(r) for r in hist.returns()[:-1]]
        current = _num(ctx.get("volatility")) or abs(
            hist.returns()[-1] or 0.0)
        flag, message, severity = detector.detect(vol_hist, current)
        return {"weakness_detected": bool(flag), "message": str(message),
                "severity": str(getattr(severity, "value", severity))}

    return AdvisoryModuleAdapter("alpha_weakness_detector", analyze)


# --- Bucket B additions ---


def _regime_hostility_service() -> AdvisoryModuleAdapter:
    """alphaalgo_core RegimeHostilityEngine — hostile-regime scenarios
    for a reference mean_reversion config on obs-derived market data."""
    from trading_bot.alphaalgo_core.regime_hostility_engine import (
        RegimeHostilityEngine)

    engine = RegimeHostilityEngine()

    async def analyze(ctx: Mapping[str, Any]) -> Any:
        market_data = {
            "regime": {
                "current": str(ctx.get("trend") or ctx.get("regime")
                               or "unknown"),
                "transition_probability": 0.1},
            "volatility": {
                "current": _num(ctx.get("volatility")) or 0.01,
                "percentile": _num(ctx.get("volatility_percentile"))
                or 0.5},
            "correlation": {"stability": 0.5},
            "liquidity": {"score": 0.5},
            "signals": {"strength": _num(ctx.get("trend_strength"))
                        or 0.5},
        }
        r = await engine.process(
            "advisory_probe",
            {"family": "mean_reversion",
             "timeframe": str(ctx.get("timeframe") or "M15")},
            market_data)
        return _payload(r)

    return AdvisoryModuleAdapter("regime_hostility", analyze)


def _policy_network_service() -> AdvisoryModuleAdapter:
    """core_agent_system PolicyNetwork — action distribution evidence."""
    from trading_bot.core_agent_system.policy_value_network import (
        PolicyNetwork)

    net = PolicyNetwork()

    async def analyze(ctx: Mapping[str, Any]) -> Any:
        out = net.predict(dict(ctx))
        if inspect.isawaitable(out):
            out = await out
        actions = getattr(out, "actions", None) or []
        ranked = sorted(
            (a for a in actions if isinstance(a, Mapping)),
            key=lambda a: a.get("probability") or 0.0, reverse=True)
        top = ranked[0] if ranked else {}
        return {"top_action": str(top.get("type", "")),
                "direction": _enum_direction(top.get("type")),
                "confidence": _num(top.get("probability")),
                "actions": {str(a.get("type")): _num(a.get("probability"))
                            for a in ranked[:6]}}

    return AdvisoryModuleAdapter("policy_network", analyze)


def _value_network_service() -> AdvisoryModuleAdapter:
    """core_agent_system ValueNetwork — state-value estimate evidence."""
    from trading_bot.core_agent_system.policy_value_network import (
        ValueNetwork)

    net = ValueNetwork()

    async def analyze(ctx: Mapping[str, Any]) -> Any:
        value = net.evaluate(dict(ctx))
        if inspect.isawaitable(value):
            value = await value
        return {"state_value": _primitive(value)}

    return AdvisoryModuleAdapter("value_network", analyze)


def _hardening_score_service() -> AdvisoryModuleAdapter:
    """intelligence_core AdversarialHardening — hardening posture."""
    from trading_bot.intelligence_core.adversarial_hardening import (
        AdversarialHardening)

    hard = AdversarialHardening()

    def analyze(ctx: Mapping[str, Any]) -> Any:
        return {"hardening_score": _primitive(hard.get_hardening_score())}

    return AdvisoryModuleAdapter("adversarial_hardening", analyze)


def _hypothesis_generator_service() -> AdvisoryModuleAdapter:
    """intelligence_core MarketBehaviorGenerator — concrete hypothesis
    generator (HypothesisGenerator ABC itself stays abstract)."""
    from trading_bot.intelligence_core.hypothesis_engine import (
        MarketBehaviorGenerator)

    gen = MarketBehaviorGenerator()

    def analyze(ctx: Mapping[str, Any]) -> Any:
        hyps = gen.generate(dict(ctx)) or []
        return {"hypotheses": [_payload(h) for h in hyps[:5]],
                "count": len(hyps)}

    return AdvisoryModuleAdapter("hypothesis_generator", analyze)


def _bloomberg_benchmark_service() -> AdvisoryModuleAdapter:
    """intelligence_core BloombergBenchmark — domain benchmark score
    evidence (self-assessment, not market direction)."""
    from trading_bot.intelligence_core.self_improvement import (
        BloombergBenchmark)

    bench = BloombergBenchmark()

    def analyze(ctx: Mapping[str, Any]) -> Any:
        return {"benchmark_score": _primitive(
            bench.get_overall_score())}

    return AdvisoryModuleAdapter("bloomberg_benchmark", analyze)


def _directional_bias_service() -> AdvisoryModuleAdapter:
    """market_intelligence MarketBiasDetector — directional bias over
    accumulated real bars."""
    from trading_bot.market_intelligence.bias_analysis import (
        MarketBiasDetector)

    detector = MarketBiasDetector()
    hist = _BarHistory()

    def analyze(ctx: Mapping[str, Any]) -> Any:
        n = hist.add(ctx)
        if len(hist) < 40:
            return {"status": "warming", "bars": n}
        bias = detector.detect_directional_bias(hist.frame()) or {}
        overall = bias.get("overall_bias") or {}
        direction = overall.get("direction")
        return {"bias": _primitive(bias),
                "direction": _enum_direction(direction),
                "strength": str(getattr(overall.get("strength"), "value",
                                        overall.get("strength", "")))}

    return AdvisoryModuleAdapter("directional_bias", analyze)


def _orderbook_imbalance_service() -> AdvisoryModuleAdapter:
    """market_intelligence MarketDataMonitor — order-book imbalance and
    volume-spike reads on the symbol's monitored stream."""
    from trading_bot.market_intelligence.data_monitoring import (
        MarketDataMonitor)

    monitor = MarketDataMonitor()

    def analyze(ctx: Mapping[str, Any]) -> Any:
        symbol = str(ctx.get("symbol") or "EURUSD")
        imbalances = monitor.detect_order_book_imbalances(symbol) or []
        spikes = monitor.detect_volume_spikes(
            symbol, str(ctx.get("timeframe") or "M15")) or []
        return {"imbalances": [_payload(i) for i in imbalances[:5]],
                "volume_spikes": [_payload(s) for s in spikes[:5]],
                "imbalance_count": len(imbalances),
                "spike_count": len(spikes)}

    return AdvisoryModuleAdapter("orderbook_imbalance", analyze)


# --- Bucket C additions ---


# unified_ai_brain is deliberately absent: it is a QUARANTINED parallel
# brain (tests/foundation/test_brain_quarantine.py) — the canonical path,
# including this module, may not import it at all.


def _aean_cycle_service() -> AdvisoryModuleAdapter:
    """aean_meta_intelligence_layer — bounded meta-cycle report. The
    cycle consumes FrontierObservation/BenchmarkTask objects the market
    obs cannot supply, so an empty cycle is the honest callable surface."""
    from trading_bot.aean_meta_intelligence_layer import (
        AEANMetaIntelligenceLayer)

    layer = AEANMetaIntelligenceLayer(monthly_infra_spend_usd=1000.0)

    def analyze(ctx: Mapping[str, Any]) -> Any:
        return _payload(layer.run_cycle(
            observations=[], benchmark_tasks=[]))

    return AdvisoryModuleAdapter("aean_meta_cycle", analyze)


def _elite_master_service() -> AdvisoryModuleAdapter:
    """elite_master_system.py — feeds the observation through
    update_market_data and reports analyze_market's real subsystem
    analyses (empty until its engines register; its execute_trade
    surface is never touched)."""
    from trading_bot.elite_master_system import EliteMasterSystem

    system = EliteMasterSystem()

    def _sync_round(ctx: Mapping[str, Any]) -> Any:
        symbol = str(ctx.get("symbol") or "UNKNOWN")
        try:
            res = system.update_market_data(symbol, dict(ctx))
            if inspect.isawaitable(res):
                res = _run_coro_sync(res)
        except Exception:  # noqa: BLE001 - optional feed
            pass
        result = system.analyze_market(symbol)
        if inspect.isawaitable(result):
            result = _run_coro_sync(result)
        return result

    async def analyze(ctx: Mapping[str, Any]) -> Any:
        # Run in an executor: with torch present this module spins up heavy
        # subsystems synchronously — a direct await would block the whole
        # loop past the per-service timeout and stall the pipeline.
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(None, _sync_round, ctx)
        return _payload(result)

    return AdvisoryModuleAdapter("elite_master_analysis", analyze)


def _complete_impl_service() -> AdvisoryModuleAdapter:
    """complete_implementation.py — MarketRegimeDetector fed real closes
    plus SessionManager session multiplier; evidence-only."""
    from trading_bot.complete_implementation import (
        MarketRegimeDetector, SessionManager)

    detector, sessions = MarketRegimeDetector(), SessionManager()
    hist = _BarHistory()

    def analyze(ctx: Mapping[str, Any]) -> Any:
        n = hist.add(ctx)
        close = _num(ctx.get("close") or ctx.get("price"))
        if close is not None:
            detector.update(close)
        out = {"bars": n}
        try:
            regime = detector.get_regime()
            out["regime"] = str(regime)
            out["direction"] = _enum_direction(regime)
        except Exception:  # noqa: BLE001 - detector may need warmup
            out["regime"] = None
        try:
            out["session_multiplier"] = _primitive(
                sessions.get_session_risk_multiplier(
                    str(ctx.get("symbol") or "EURUSD")))
        except Exception:  # noqa: BLE001
            out["session_multiplier"] = None
        return out

    return AdvisoryModuleAdapter("complete_impl_market_intel", analyze)


# radar_ai note: MarketAnalystAgent + understanding_engine.RegimeDetector
# are wired above; OntologyDrivenAgent declares analyze/learn abstract —
# that part stays quarantined since nothing is directly
# observation-callable without fabricated stubs.


# Factories for services that are genuinely observation-callable. Each
# entry is attached at assembly time inside a probe; failures skip the
# service rather than break the runtime.
DEFAULT_ADVISORY_FACTORIES: Tuple[Tuple[str, Callable[[], Any]], ...] = (
    ("multi_agent_debate", _debate_service),
    ("market_anomaly_detection", _anomaly_service),
    ("regime_classification", _regime_classifier_service),
    ("adversarial_trade_eval", _adversarial_trade_service),
    ("trend_following_agent", _trend_agent_service),
    ("failure_mode_detection", _failure_mode_service),
    # Bucket A — orphan packages with genuinely obs-callable analyzers
    ("alpha_research_market_state", _alpha_research_state_service),
    ("alpha_research_risk_matrix", _alpha_research_risk_service),
    ("alpha_research_predator_defense", _alpha_research_predator_service),
    ("alpha_research_footprint", _alpha_research_footprint_service),
    ("institutional_market_selection", _institutional_selection_service),
    ("brain_technical_analysis", _brain_technical_service),
    ("brain_regime_classification", _brain_regime_service),
    ("cognitive_architecture_regime", _cognitive_regime_service),
    ("cognitive_performance_eval", _cognitive_perf_service),
    ("elite_factor_matrix", _elite_factor_service),
    ("adaptive_market_regime", _adaptive_regime_service),
    ("adaptive_learning_predict", _adaptive_learning_service),
    ("intelligence_strategy_stats", _intelligence_strategy_service),
    ("self_learning_ensemble", _self_learning_ensemble_service),
    ("signal_regime_change", _signal_regime_change_service),
    ("signal_statistical_outliers", _signal_outlier_service),
    ("tamic_market_time", _tamic_market_time_service),
    ("self_diagnostic_health", _self_diagnostic_service),
    ("aletheia_decision_audit", _aletheia_audit_service),
    ("superintelligence_regime_strategy", _superintel_regime_service),
    ("systems_ai_stress_test", _systems_stress_service),
    # Bucket B — additional capabilities from partially-wired packages
    ("mean_reversion_agent",
     _make_legacy_agent_service("mean_reversion_agent",
                                "MeanReversionAgent")),
    ("volatility_agent",
     _make_legacy_agent_service("volatility_agent", "VolatilityAgent")),
    ("risk_manager_agent",
     _make_legacy_agent_service("risk_manager_agent", "RiskManagerAgent")),
    ("agents2_mean_reversion",
     _make_agents2_service("agents2_mean_reversion",
                           "MeanReversionAgent")),
    ("agents2_volatility",
     _make_agents2_service("agents2_volatility", "VolatilityAgent")),
    ("regime_shift_detection",
     _make_failure_detector_service("regime_shift_detection",
                                    "RegimeShiftDetector")),
    ("liquidity_evaporation_detection",
     _make_failure_detector_service("liquidity_evaporation_detection",
                                    "LiquidityEvaporationDetector")),
    ("uncertainty_explosion_detection",
     _make_failure_detector_service("uncertainty_explosion_detection",
                                    "UncertaintyExplosionDetector")),
    ("institutional_accumulation",
     _make_anomaly_classifier_service(
         "institutional_accumulation",
         "trading_bot.market_intelligence.categories."
         "institutional_accumulation",
         "InstitutionalAccumulationClassifier")),
    ("macro_regime_shifts",
     _make_anomaly_classifier_service(
         "macro_regime_shifts",
         "trading_bot.market_intelligence.categories.macro_regime_shifts",
         "MacroRegimeShiftsClassifier")),
    ("macro_strategist_agent",
     _make_debate_agent_service("macro_strategist_agent",
                                "MacroStrategist")),
    ("risk_sentinel_agent",
     _make_debate_agent_service("risk_sentinel_agent", "RiskSentinel")),
    ("adversarial_failure_match", _adversarial_failure_match_service),
    ("alphaalgo_performance_sensor", _alphaalgo_perf_sensor_service),
    ("market_physics_filter", _market_physics_service),
    # Bucket C — loose orphan root files
    ("alphaalgo_5star_risk_metrics", _alphaalgo_5star_risk_service),
    ("world2agent_bridge", _world2agent_bridge_service),
    # Bucket A2 — second-pass: newly obs-callable orphan packages
    ("mixture_of_experts", _moe_router_service),
    ("market_microstructure", _microstructure_service),
    ("cognitive_economy_supervisor",
     _economy_agent_service("cognitive_economy_supervisor",
                            "SupervisorAgent")),
    ("cognitive_economy_risk",
     _economy_agent_service("cognitive_economy_risk", "RiskAgent")),
    ("cognitive_economy_data",
     _economy_agent_service("cognitive_economy_data", "DataAgent")),
    ("cognitive_economy_learning",
     _economy_agent_service("cognitive_economy_learning",
                            "LearningAgent")),
    ("cognitive_economy_strategy",
     _economy_agent_service("cognitive_economy_strategy",
                            "StrategyAgent")),
    ("regime_transition_detector", _regime_transition_service),
    ("market_psychology", _market_psychology_service),
    ("improvement_findings", _improvement_findings_service),
    ("neural_hub_topology", _neural_hub_service),
    ("hivemind_analyst", _hivemind_analyst_service),
    ("radar_regime", _radar_regime_service),
    ("self_concept_guard", _self_concept_service),
    ("system_health", _self_healing_health_service),
    ("self_learning_health", _self_learning_health_service),
    ("mastery_reflection", _mastery_reflection_service),
    ("codebase_introspection", _introspection_service),
    ("regime_memory", _regime_memory_service),
    ("trend_reversal", _trend_reversal_service),
    ("regime_discovery", _regime_discovery_service),
    ("strategy_selector", _strategy_selector_service),
    ("data_drift", _data_drift_service),
    ("performance_decay", _performance_decay_service),
    ("signal_decay", _signal_decay_service),
    ("autonomous_tuner", _autonomous_tuner_service),
    ("planner_agent", _planner_agent_service),
    ("alpha_evolve_signal", _alpha_evolve_service),
    ("polymarket_estimate", _polymarket_service),
    ("maven_stats", _maven_stats_service),
    ("aamis_market", _aamis_service),
    ("learner_knowledge", _learner_knowledge_service),
    ("decision_explainer", _decision_explainer_service),
    ("alpha_weakness_detector", _alpha_weakness_service),
    # Bucket B additions — second capabilities in wired packages
    ("regime_hostility", _regime_hostility_service),
    ("policy_network", _policy_network_service),
    ("value_network", _value_network_service),
    ("adversarial_hardening", _hardening_score_service),
    ("hypothesis_generator", _hypothesis_generator_service),
    ("bloomberg_benchmark", _bloomberg_benchmark_service),
    ("directional_bias", _directional_bias_service),
    ("orderbook_imbalance", _orderbook_imbalance_service),
    ("tactical_executioner_agent",
     _make_debate_agent_service("tactical_executioner_agent",
                                "TacticalExecutioner")),
    ("agents2_market_maker",
     _make_agents2_service("agents2_market_maker", "MarketMakerAgent")),
    # Bucket C additions — loose root files
    ("aean_meta_cycle", _aean_cycle_service),
    ("elite_master_analysis", _elite_master_service),
    ("complete_impl_market_intel", _complete_impl_service),
)

# Modules imported by the live path but with no advisory decision role —
# wired as dependencies, not as cognition (kept separate from orphans so
# the audit map stays honest).
LIVE_IMPORTED_NON_ADVISORY: Tuple[Tuple[str, str], ...] = (
    ("world_model", "imported by unified_bot.py — live dependency, "
     "not an advisory service"),
    ("alpha_engine", "imported by execution/__init__.py — live "
     "dependency, sentiment stack not in the decision path"),
    ("autonomous_financial_intelligence", "imported by "
     "core/chainofthoughtreasoner.py — legacy compat, no decision role"),
)

# Orphan modules that are NOT observation-callable advisory services —
# recorded so the audit map is total rather than silently partial.
# Attached dirs are covered by DEFAULT_ADVISORY_FACTORIES and therefore
# deliberately absent here.
UNWIRED_ORPHAN_MODULES: Tuple[Tuple[str, str], ...] = (
    ("advanced_intelligence", "mixture_of_experts attached; deep-model "
     "remainder (diffusion, capsule, contrastive, energy-based) takes "
     "trained tensors, not observation dicts"),
    ("autonomous_superintelligence", "package __init__ chains "
     "torch-dependent self_modifier; analyzers are fleet/research "
     "coordinators, not obs-callable"),
    ("core_agent_system", "legacy agents + policy/value networks "
     "attached; framework remainder subsumed by PCA"),
    ("improvement_agent", "improvement_findings attached; "
     "codebase self-modification machinery (ChangeManager) is not "
     "obs-callable"),
    ("intel", "news/macro ingestion; external data dependencies"),
    ("meta_learning", "maml.Maml.process is an identity passthrough stub "
     "(_process_internal returns input); no signal to wire"),
    ("neural_integration", "neural_hub_topology attached; model "
     "integration layer is torch-dependent"),
    ("radar_ai", "hivemind_analyst + radar_regime attached; "
     "OntologyDrivenAgent declares analyze/learn abstract — no "
     "obs-callable surface without fabricated stubs"),
    ("self_concepts", "self_concept_guard attached; concept catalogs "
     "proper are self-model bookkeeping, not market analyzers"),
    ("self_healing_ai", "system_health attached; healing workflow "
     "proper is state validation, not an obs-callable market analyzer"),
    ("self_mastery", "mastery_reflection attached; skill/knowledge "
     "bookkeeping remainder has no obs-callable analyzer"),
    ("sentient_core", "codebase_introspection attached; introspection "
     "facades (get_performance_report, get_threat_level) report internal "
     "state only"),
    ("superpowerful_ai", "trend_reversal + regime_discovery + "
     "strategy_selector attached; get_*_statistics facades are not "
     "obs-callable"),
    ("ai", "autonomous_tuner attached; BayesianOptimizer + torch-bound "
     "hub are not obs-callable"),
    ("ai_core", "planner_agent attached; verifier agents expose "
     "get_status only"),
    ("ai_engineer", "code-change safeguard machinery (safeguards, "
     "sandbox, compliance audit); approval semantics, not a market "
     "advisory"),
    ("aads", "alpha_evolve_signal + polymarket_estimate + maven_stats "
     "attached; aip_agents synthesize bull/bear cases via np.random — "
     "fabricated analysis, stays quarantined"),
    ("aamis_v3", "aamis_market attached; consolidated-engine status "
     "facades are not obs-callable"),
    ("learning", "RL learners (DistributionalQLearning, EKSFTTrainer) "
     "are offline training loops, not obs-callable advisors"),
    ("agents", "multi_agent_debate attached (system + MacroStrategist + "
     "RiskSentinel + TacticalExecutioner); prosecutor roles need an "
     "in-flight DebateTopic"),
    ("autonomous_learner", "learner_knowledge attached (evidence only); "
     "deprecated RSI duplicate carries no authority per AGENTS.md"),
    ("explainability", "decision_explainer attached; SHAPExplainer is "
     "post-hoc — needs a fitted model and its training data"),
    # Loose orphan root files (bucket C audit entries)
    ("unified_ai_brain.py", "quarantined parallel brain — the canonical "
     "path may not import it (brain quarantine test); subsystem registry "
     "façade, not an obs-callable analyzer"),
    ("agent_orchestrator.py", "flat-path shim re-exporting "
     "services.tier4_services; no analyzer"),
    ("ai_learner.py", "deprecated bridge to sentient_core.ai_learner "
     "per AGENTS.md"),
    ("neural_network.py", "merge-loss compatibility stub (no-op "
     "methods)"),
    ("maml_trainer.py", "merge-loss compatibility stub re-exporting "
     "ml.meta_learning.maml"),
    ("continual_learner.py", "deprecated shim; RSI is canonical"),
    ("advanced_rl_agents.py", "flat-path shim re-exporting ml.offline_rl "
     "agents — offline RL needs trained policies, not observations"),
    ("bear_agent.py", "merge-loss compatibility stub (no-op methods)"),
    ("magic_agent.py", "merge-loss compatibility stub (no-op methods)"),
    ("mbop_agent.py", "merge-loss compatibility stub (no-op methods)"),
    ("aean_meta_intelligence_layer.py", "aean_meta_cycle attached — "
     "empty-cycle report; market obs cannot supply FrontierObservation/"
     "BenchmarkTask inputs"),
    ("reward_model.py", "flat-path shim re-exporting "
     "evolution_layer.reward_model"),
    ("adaptive_retrainer.py", "merge-loss compatibility stub (no-op "
     "methods)"),
    ("auto_rollback.py", "deprecated shim; RSI is canonical"),
    ("code_evolver.py", "deprecated bridge; RSI is canonical per "
     "AGENTS.md"),
    ("performance_optimizer.py", "deprecated shim; RSI is canonical"),
    ("experiment_tracker.py", "deprecated shim; RSI is canonical"),
    ("world2agent.py", "world2agent_bridge attached — adapter module "
     "a2a.py stays a live dep of that seam"),
    ("alphaalgo_5star.py", "alphaalgo_5star_risk_metrics attached — "
     "probe-gated on the module's logger API"),
    ("elite_master_system.py", "elite_master_analysis attached — "
     "analyze_market only; execute paths never touched"),
    ("complete_implementation.py", "complete_impl_market_intel attached "
     "— regime detector fed real closes plus session multiplier"),
    ("a2a.py", "live dep — imported by the world2agent_bridge adapter"),
    # --- package-shadowed root files (import resolves to the
    #     same-named package; the .py file is unreachable) ---
    # --- package-shadowed root files (import resolves to the
    #     same-named package; the .py file is unreachable) ---
    ("adaptive_systems.py", "shadowed by trading_bot/adaptive_systems/ package — file unreachable"),
    ("agents.py", "shadowed by trading_bot/agents/ package — file unreachable"),
    ("agents2.py", "shadowed by trading_bot/agents2/ package — file unreachable"),
    ("analysis.py", "shadowed by trading_bot/analysis/ package — file unreachable"),
    ("api.py", "shadowed by trading_bot/api/ package — file unreachable"),
    ("approval.py", "shadowed by trading_bot/approval/ package — file unreachable"),
    ("arbitrage.py", "shadowed by trading_bot/arbitrage/ package — file unreachable"),
    ("audit.py", "shadowed by trading_bot/audit/ package — file unreachable"),
    ("autonomous.py", "shadowed by trading_bot/autonomous/ package — file unreachable"),
    ("backtesting.py", "shadowed by trading_bot/backtesting/ package — file unreachable"),
    ("blockchain.py", "shadowed by trading_bot/blockchain/ package — file unreachable"),
    ("broker.py", "shadowed by trading_bot/broker/ package — file unreachable"),
    ("connectivity.py", "shadowed by trading_bot/connectivity/ package — file unreachable"),
    ("critical_fixes.py", "shadowed by trading_bot/critical_fixes/ package — file unreachable"),
    ("data.py", "shadowed by trading_bot/data/ package — file unreachable"),
    ("documentation.py", "shadowed by trading_bot/documentation/ package — file unreachable"),
    ("evolution_layer.py", "shadowed by trading_bot/evolution_layer/ package — file unreachable"),
    ("exit_strategies.py", "shadowed by trading_bot/exit_strategies/ package — file unreachable"),
    ("exits.py", "shadowed by trading_bot/exits/ package — file unreachable"),
    ("explainability.py", "shadowed by trading_bot/explainability/ package — file unreachable"),
    ("features.py", "shadowed by trading_bot/features/ package — file unreachable"),
    ("filters.py", "shadowed by trading_bot/filters/ package — file unreachable"),
    ("governance.py", "shadowed by trading_bot/governance/ package — file unreachable"),
    ("indicators.py", "shadowed by trading_bot/indicators/ package — file unreachable"),
    ("integration.py", "shadowed by trading_bot/integration/ package — file unreachable"),
    ("integrations.py", "shadowed by trading_bot/integrations/ package — file unreachable"),
    ("mobile_app.py", "shadowed by trading_bot/mobile_app/ package — file unreachable"),
    ("models.py", "shadowed by trading_bot/models/ package — file unreachable"),
    ("multimodal.py", "shadowed by trading_bot/multimodal/ package — file unreachable"),
    ("portfolio.py", "shadowed by trading_bot/portfolio/ package — file unreachable"),
    ("quantum.py", "shadowed by trading_bot/quantum/ package — file unreachable"),
    ("qwen_codemender.py", "shadowed by trading_bot/qwen_codemender/ package — file unreachable"),
    ("realtime_trading_core.py", "shadowed by trading_bot/realtime_trading_core/ package — file unreachable"),
    ("risk.py", "shadowed by trading_bot/risk/ package — file unreachable"),
    ("schemas.py", "shadowed by trading_bot/schemas/ package — file unreachable"),
    ("sentiment.py", "shadowed by trading_bot/sentiment/ package — file unreachable"),
    ("signals.py", "shadowed by trading_bot/signals/ package — file unreachable"),
    ("system.py", "shadowed by trading_bot/system/ package — file unreachable"),
    ("tamic.py", "shadowed by trading_bot/tamic/ package — file unreachable"),
    ("trade_journal.py", "shadowed by trading_bot/trade_journal/ package — file unreachable"),
    ("ultimate_approval.py", "shadowed by trading_bot/ultimate_approval/ package — file unreachable"),
    ("unified_approval.py", "shadowed by trading_bot/unified_approval/ package — file unreachable"),
    ("upgrades.py", "shadowed by trading_bot/upgrades/ package — file unreachable"),
    ("utils.py", "shadowed by trading_bot/utils/ package — file unreachable"),
    ("voice_assistant.py", "shadowed by trading_bot/voice_assistant/ package — file unreachable"),
    ("wealth.py", "shadowed by trading_bot/wealth/ package — file unreachable"),
    # --- merge-era deprecation stubs (subsystem removed during
    #     convergence; no behavior lives here) ---
    ("apply_and_fix.py", "merge-era deprecation stub — no behavior"),
    ("apply_approved.py", "merge-era deprecation stub — no behavior"),
    ("autonomy_levels.py", "merge-era deprecation stub — no behavior"),
    ("behavior_monitor.py", "merge-era deprecation stub — no behavior"),
    ("change_applier.py", "merge-era deprecation stub — no behavior"),
    ("chart_analyzer.py", "merge-era deprecation stub — no behavior"),
    ("classa.py", "merge-era deprecation stub — no behavior"),
    ("classb.py", "merge-era deprecation stub — no behavior"),
    ("deepseek_core.py", "merge-era deprecation stub — no behavior"),
    ("deepseek_engineer_demo.py", "merge-era deprecation stub — no behavior"),
    ("deepseek_integration.py", "merge-era deprecation stub — no behavior"),
    ("deepseek_orchestrator.py", "merge-era deprecation stub — no behavior"),
    ("deepseek_r1_8b_integration.py", "merge-era deprecation stub — no behavior"),
    ("freetradingbot.py", "merge-era deprecation stub — no behavior"),
    ("generator_verifier.py", "merge-era deprecation stub — no behavior"),
    ("governance_orchestrator.py", "merge-era deprecation stub — no behavior"),
    ("guardrails.py", "merge-era deprecation stub — no behavior"),
    ("hardware_manager.py", "merge-era deprecation stub — no behavior"),
    ("human_collaboration.py", "merge-era deprecation stub — no behavior"),
    ("human_protocol.py", "merge-era deprecation stub — no behavior"),
    ("immutable_purpose.py", "merge-era deprecation stub — no behavior"),
    ("live_engineer.py", "merge-era deprecation stub — no behavior"),
    ("mytradingbot.py", "merge-era deprecation stub — no behavior"),
    ("pipeline_orchestrator.py", "merge-era deprecation stub — no behavior"),
    ("positive_impact.py", "merge-era deprecation stub — no behavior"),
    ("pre_commit_hook.py", "merge-era deprecation stub — no behavior"),
    ("proposal_system.py", "merge-era deprecation stub — no behavior"),
    ("protected_registry.py", "merge-era deprecation stub — no behavior"),
    ("quant_research_engine.py", "merge-era deprecation stub — no behavior"),
    ("risk_mitigation.py", "merge-era deprecation stub — no behavior"),
    ("security_hardening.py", "merge-era deprecation stub — no behavior"),
    ("self_evolution_engine.py", "merge-era deprecation stub — no behavior"),
    ("self_improvement_loop.py", "merge-era deprecation stub — no behavior"),
    ("self_improvement_orchestrator.py", "merge-era deprecation stub — no behavior"),
    ("testyourclass.py", "merge-era deprecation stub — no behavior"),
    ("tradingbot.py", "merge-era deprecation stub — no behavior"),
    ("unifiedtradingsystem.py", "merge-era deprecation stub — no behavior"),
    ("verification_engine.py", "merge-era deprecation stub — no behavior"),
    ("workflow_engine.py", "merge-era deprecation stub — no behavior"),
    # --- auto-generated stubs ---
    ("adaptive.py", "auto-generated stub — start/stop/get_status only"),
    ("advanced_exits.py", "auto-generated stub — start/stop/get_status only"),
    ("calendar.py", "auto-generated stub — start/stop/get_status only"),
    ("market_regime.py", "auto-generated stub — start/stop/get_status only"),
    ("scanners.py", "auto-generated stub — start/stop/get_status only"),
    ("transformer.py", "auto-generated stub — start/stop/get_status only"),
    # --- flat-path re-export shims ---
    ("code_analyzer.py", "flat-path re-export shim — no analyzer surface"),
    ("diagnostic_engine.py", "flat-path re-export shim — no analyzer surface"),
    ("exit_strategy.py", "flat-path re-export shim — no analyzer surface"),
    ("experience_memory.py", "flat-path re-export shim — no analyzer surface"),
    ("health_monitor.py", "flat-path re-export shim — no analyzer surface"),
    ("institutional_github_scout.py", "flat-path re-export shim — no analyzer surface"),
    ("knowledge_consolidator.py", "flat-path re-export shim — no analyzer surface"),
    ("knowledge_harvester.py", "flat-path re-export shim — no analyzer surface"),
    ("market_microstructure.py", "flat-path re-export shim — no analyzer surface"),
    ("mastery_orchestrator.py", "flat-path re-export shim — no analyzer surface"),
    ("network_sentinel.py", "flat-path re-export shim — no analyzer surface"),
    ("self_defender.py", "flat-path re-export shim — no analyzer surface"),
    ("self_reflection.py", "flat-path re-export shim — no analyzer surface"),
    ("sentient_orchestrator.py", "flat-path re-export shim — no analyzer surface"),
    ("strategy_genome.py", "flat-path re-export shim — no analyzer surface"),
    # --- status facades (get_status/to_dict only; no
    #     observation-callable analyzer) ---
    ("adwin.py", "status facade only — get_status/to_dict"),
    ("adwin_detector.py", "status facade only — get_status/to_dict"),
    ("alphaalgo_orchestrator.py", "status facade only — get_status/to_dict"),
    ("attention_viz.py", "status facade only — get_status/to_dict"),
    ("causal_analyzer.py", "status facade only — get_status/to_dict"),
    ("deepar.py", "status facade only — get_status/to_dict"),
    ("forecast_ensemble.py", "status facade only — get_status/to_dict"),
    ("hierarchical_rl.py", "status facade only — get_status/to_dict"),
    ("informer.py", "status facade only — get_status/to_dict"),
    ("monitor.py", "status facade only — get_status/to_dict"),
    ("nbeats.py", "status facade only — get_status/to_dict"),
    ("offline_policy_eval.py", "status facade only — get_status/to_dict"),
    ("offline_policy_evaluation.py", "status facade only — get_status/to_dict"),
    ("page_hinkley.py", "status facade only — get_status/to_dict"),
    ("rl_executor.py", "status facade only — get_status/to_dict"),
    ("temporal_fusion_transformer.py", "status facade only — get_status/to_dict"),
    ("tft.py", "status facade only — get_status/to_dict"),
    ("trade_attributor.py", "status facade only — get_status/to_dict"),
    ("uncertainty.py", "status facade only — get_status/to_dict"),
    # --- parallel capital / integration paths (load, wire,
    #     or execute other systems — authority surface) ---
    ("auto_dependency_installer.py", "dependency installer — side-effect tool, never advisory"),
    ("background.py", "parallel capital/integration path — authority surface"),
    ("complete_integrator.py", "parallel capital/integration path — authority surface"),
    ("complete_system_integrator.py", "parallel capital/integration path — authority surface"),
    ("elite_integration.py", "parallel capital/integration path — authority surface"),
    ("master_integration.py", "parallel capital/integration path — authority surface"),
    ("mega_integration.py", "parallel capital/integration path — authority surface"),
    ("optimized_integration.py", "parallel capital/integration path — authority surface"),
    ("position_manager.py", "parallel capital/integration path — authority surface"),
    ("realtime_dependency_manager.py", "parallel capital/integration path — authority surface"),
    ("realtime_system_validator.py", "parallel capital/integration path — authority surface"),
    ("system_interfaces.py", "parallel capital/integration path — authority surface"),
    ("trading_engine.py", "parallel capital/integration path — authority surface"),
    ("ultimate_integration.py", "parallel capital/integration path — authority surface"),
    ("ultimate_module_integrator.py", "parallel capital/integration path — authority surface"),
    ("unified_main.py", "parallel capital/integration path — authority surface"),
    ("unified_master_integrator.py", "parallel capital/integration path — authority surface"),
    ("universal_action_layer.py", "parallel capital/integration path — authority surface"),
    # --- utilities ---
    ("constants.py", "utility module — not a market analyzer"),
    ("core_types.py", "utility module — not a market analyzer"),
    ("safe_imports.py", "utility module — not a market analyzer"),
    ("system_config.py", "utility module — not a market analyzer"),
    ("unicode_fix.py", "utility module — not a market analyzer"),
    # --- test-only fixtures ---
    ("autonomous_engineer.py", "test-only fixture — no production reach"),
    ("yourtradingbot.py", "test-only fixture — no production reach"),
    # --- non-AI-named orphan dirs never imported by the canonical path
    #     (the 140 other non-manifest dirs ARE live imports — telemetry,
    #     brokers, monitoring etc. — and stay outside this manifest) ---
    ("adversarial_verification", "orphan parallel verification stack; "
     "canonical path uses core/verification swarm"),
    ("alpha_evolve", "deprecated RSI duplicate; RSI is canonical per "
     "AGENTS.md"),
    ("apex_fi", "orphan parallel APEX system; not on the canonical spine"),
    ("cos", "orphan parallel orchestration system"),
    ("decision_governance", "orphan parallel governance; canonical path "
     "uses governance/policy_adapter + human_layer"),
    ("deepseek_engineer", "offline engineering assistant; not a runtime "
     "advisor"),
    ("deepseek_engineer_pkg_tmp", "temporary packaging dir"),
    ("events", "orphan event plumbing; canonical path uses "
     "core/unified_event_bus"),
    ("feedback", "orphan feedback plumbing; canonical path uses "
     "record_outcome/decision sink"),
    ("gets", "orphan governance-promotion experiment"),
    ("golden_path", "orphan scripted demo path"),
    ("hivemind", "orphan collective-intelligence loop"),
    ("master_system", "orphan parallel master orchestrator"),
    ("meta_governance", "orphan parallel governance layer"),
    ("metrics", "orphan metrics shim; canonical path uses telemetry/"),
    ("neuros_evolution", "deprecated evolution duplicate; RSI is "
     "canonical per AGENTS.md"),
    ("orchestration", "orphan parallel orchestrator"),
    ("perplexity_trading", "orphan external-API research path"),
    ("realtime_trading_core", "orphan parallel realtime engine; "
     "canonical path is unified_bot -> CSC"),
    ("registry", "orphan registry shim; canonical path uses "
     "core/unified_registry"),
    ("services", "orphan service plumbing"),
    ("tests", "in-repo test package, not a runtime module"),
)


_DISCOVERY_METHODS = ("analyze", "detect", "classify", "predict",
                      "assess", "estimate", "evaluate")
_DISCOVERY_TIMEOUT_S = 0.5
_DISCOVERY_CAP = 40
# Confirmed live-failures: classes that pass the synthetic probe but
# crash on real observations (type errors on string/sequence fields).
# Circuit breaker already silences them in-session; skip attaching.
_DISCOVERY_BLOCKLIST = frozenset({
    "DataAgent",   # cognitive_architecture layer3: '<' on str vs float
})


def discover_advisory_callables(
        packages: Tuple[str, ...],
        max_services: int = _DISCOVERY_CAP,
        probe: bool = True) -> Tuple[List[AdvisoryModuleAdapter], List[str]]:
    """Long-tail wiring: scan orphan packages for observation-callable
    analyzers and wrap them as advisory services.

    For each ``trading_bot.<pkg>`` top-level module (no recursion): find
    zero-arg-constructible classes exposing one of
    analyze/detect/classify/predict/assess/estimate/evaluate(ctx). The
    method is called with the observation dict only — modules needing
    series or external data fail the probe and are skipped. Every import
    and probe is inside try/except — discovery can never break the
    runtime; it can only add evidence or report a skip.

    Discovered services get ``capability_id = "discovered:<cls>"`` and a
    per-call timeout so a hanging advisor cannot stall the pipeline.
    """
    import asyncio
    import importlib
    import inspect as _inspect
    import pkgutil

    found: List[AdvisoryModuleAdapter] = []
    skipped: List[str] = []
    # Realistic context: real observations carry string/sequence fields
    # alongside numerics — advisors that assume all-numeric inputs must
    # fail here, not mid-pipeline.
    probe_ctx = {
        "symbol": "EURUSD", "price": 1.09, "close": 1.09,
        "volatility": 0.01, "trend": "FLAT", "trend_strength": 0.1,
        "sentiment": 0.0, "momentum": 0.0, "timeframe": "M15",
        "timestamp": "2026-01-01T00:00:00", "volume_ratio": 1.0,
        "raw_market_data": {"note": "nested"}, "key_levels": [],
    }

    async def _probe(svc):
        res = svc.analyze(probe_ctx)
        if _inspect.isawaitable(res):
            res = await asyncio.wait_for(res, _DISCOVERY_TIMEOUT_S)
        return res

    def _probe_sync(svc) -> None:
        _run_coro_sync(_probe(svc))

    for pkg_name in packages:
        if len(found) >= max_services:
            break
        try:
            pkg = importlib.import_module(f"trading_bot.{pkg_name}")
        except Exception:
            skipped.append(pkg_name)
            continue
        try:
            mod_infos = list(pkgutil.iter_modules(
                pkg.__path__)) if hasattr(pkg, "__path__") else []
        except Exception:
            mod_infos = []
        for mi in mod_infos:
            if len(found) >= max_services:
                break
            try:
                mod = importlib.import_module(
                    f"trading_bot.{pkg_name}.{mi.name}")
            except Exception:
                continue
            for _, cls in vars(mod).items():
                if len(found) >= max_services:
                    break
                if not isinstance(cls, type) or cls.__module__ != mod.__name__:
                    continue
                if cls.__name__ in _DISCOVERY_BLOCKLIST:
                    skipped.append(f"discovered:{cls.__name__}(blocklisted)")
                    continue
                method = next(
                    (getattr(cls, m) for m in _DISCOVERY_METHODS
                     if callable(getattr(cls, m, None))), None)
                if method is None:
                    continue
                try:
                    if len(_inspect.signature(cls.__init__).parameters) > 1:
                        continue
                    inst = cls()
                except Exception:
                    continue

                cap_id = f"discovered:{cls.__name__}"
                _meth = getattr(inst, next(
                    m for m in _DISCOVERY_METHODS
                    if callable(getattr(inst, m, None))))

                async def _call(ctx, _m=_meth):
                    out = _m(dict(ctx))
                    if _inspect.isawaitable(out):
                        out = await asyncio.wait_for(
                            out, _DISCOVERY_TIMEOUT_S)
                    return out

                svc = AdvisoryModuleAdapter(cap_id, _call)
                try:
                    if probe:
                        _probe_sync(svc)
                    found.append(svc)
                except Exception:
                    skipped.append(cap_id)
    return found, skipped


def attach_advisory_modules(
    csc: Any,
    factories: Optional[Tuple[Tuple[str, Callable[[], Any]], ...]] = None,
    probe: bool = True,
    discover: bool = False,
) -> Tuple[List[str], List[str]]:
    """Attach every wireable advisory service to the CSC.

    Each factory is constructed inside try/except; when ``probe`` is set
    the service is exercised once with a synthetic observation so a
    malformed signature fails at attach time, not mid-pipeline. Returns
    ``(attached_capability_ids, skipped_capability_ids)``.
    """
    import asyncio

    attached: List[str] = []
    skipped: List[str] = []
    for capability_id, factory in (factories or DEFAULT_ADVISORY_FACTORIES):
        try:
            service = factory()
            if probe:
                probe_ctx = {
                    "symbol": "EURUSD", "price": 1.09, "close": 1.09,
                    "volatility": 0.01, "trend": "FLAT", "sentiment": 0.0,
                }
                result = service.analyze(probe_ctx)
                if inspect.isawaitable(result):
                    _run_coro_sync(result)
            csc.configure_cognition(service)
            attached.append(capability_id)
            logger.info("advisory module attached: %s", capability_id)
        except Exception as exc:
            skipped.append(capability_id)
            logger.warning("advisory module skipped: %s (%s)",
                           capability_id, exc)

    if discover:
        # Only package names — root .py manifest entries resolve to dead
        # stubs or side-effect modules (installers, stdout patchers) that
        # must never be imported by discovery.
        orphan_pkgs = tuple(
            name.split("(")[0]
            for name, _ in UNWIRED_ORPHAN_MODULES
            if not name.endswith(".py"))
        try:
            found, disc_skipped = discover_advisory_callables(orphan_pkgs)
            for svc in found:
                try:
                    csc.configure_cognition(svc)
                    attached.append(svc.capability_id)
                    logger.info("advisory module attached: %s",
                                svc.capability_id)
                except Exception as exc:
                    skipped.append(svc.capability_id)
                    logger.warning("advisory module skipped: %s (%s)",
                                   svc.capability_id, exc)
            skipped.extend(disc_skipped)
        except Exception as exc:
            logger.warning("advisory discovery failed: %s", exc)

    return attached, skipped
